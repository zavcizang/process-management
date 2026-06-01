"""
memory_manager.py — COW 内存管理器

实现写时复制（Copy-On-Write）机制，这是 fork 高效实现的核心。

COW 原理：
- fork 时，父子进程共享同一份物理内存（零拷贝）
- 每个物理帧有一个引用计数，记录有多少进程在使用
- 只有当某个进程尝试写入时，才真正复制该帧（按需复制）

优势：
- fork 速度极快（只复制页表，不复制物理内存）
- 节省内存（共享的帧只占一份物理内存）
- 按需分配（只有被修改的帧才会被复制）

数据结构：
- PageTableEntry: 页表项（帧号、有效位、可写位、脏位、引用计数）
- PageTable: 页表（页号 → PTE 的映射）
- FrameManager: 物理帧管理器（帧分配、回收、引用计数）
- COWManager: COW 管理器（fork 页表复制、写时复制触发）
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


# ============================================================
# 页表项
# ============================================================
@dataclass
class PageTableEntry:
    """
    页表项（Page Table Entry）

    存储虚拟页到物理帧的映射信息。

    Attributes:
        frame_id: 物理帧号
        is_valid: 有效位（页面是否在内存中）
        is_writable: 可写位（COW 时设为 False，写入时触发复制）
        is_dirty: 脏位（页面是否被修改过）
        ref_count: 引用计数（多少进程共享此帧）
        last_access: 最后访问时间（用于 LRU 替换）
    """
    frame_id: int
    is_valid: bool = True
    is_writable: bool = True
    is_dirty: bool = False
    ref_count: int = 1
    last_access: float = 0.0


# ============================================================
# 页表
# ============================================================
class PageTable:
    """
    进程的页表

    存储虚拟页号到物理帧的映射。

    使用示例：
        pt = PageTable(page_size=4096)
        pt.map(0, frame_id=5)      # 虚拟页 0 → 物理帧 5
        pt.map(1, frame_id=8)      # 虚拟页 1 → 物理帧 8
        pte = pt.get_entry(0)      # 获取页表项
        pt.unmap(0)                # 取消映射
    """

    def __init__(self, page_size: int = 4096):
        self.page_size = page_size
        self._entries: Dict[int, PageTableEntry] = {}

    def map(self, page_num: int, frame_id: int, is_writable: bool = True) -> None:
        """建立虚拟页到物理帧的映射"""
        self._entries[page_num] = PageTableEntry(
            frame_id=frame_id,
            is_writable=is_writable,
        )

    def unmap(self, page_num: int) -> Optional[int]:
        """取消映射，返回物理帧号"""
        entry = self._entries.pop(page_num, None)
        return entry.frame_id if entry else None

    def get_entry(self, page_num: int) -> Optional[PageTableEntry]:
        """获取页表项"""
        return self._entries.get(page_num)

    def get_all_entries(self) -> Dict[int, PageTableEntry]:
        """获取所有页表项"""
        return self._entries.copy()

    def get_mapped_pages(self) -> List[int]:
        """获取所有已映射的虚拟页号"""
        return list(self._entries.keys())

    def get_memory_usage(self, page_size: int = 4096) -> int:
        """计算内存使用量（字节）"""
        return len(self._entries) * page_size

    def __repr__(self) -> str:
        return f"PageTable(pages={len(self._entries)}, page_size={self.page_size})"


# ============================================================
# 物理帧管理器
# ============================================================
class FrameManager:
    """
    物理内存帧管理器

    管理物理内存的分配和回收，支持引用计数（用于 COW）。

    使用示例：
        fm = FrameManager(total_frames=256)
        frame = fm.allocate()    # 分配一个空闲帧
        fm.incref(frame)         # 增加引用计数（COW fork）
        fm.decref(frame)         # 减少引用计数，归零时自动回收
    """

    def __init__(self, total_frames: int = 256, page_size: int = 4096):
        """
        Args:
            total_frames: 总帧数（默认 256 帧 = 1MB，假设 4KB/帧）
            page_size: 页大小（字节）
        """
        self.total_frames = total_frames
        self.page_size = page_size

        # 引用计数：ref_counts[frame_id] = 引用此帧的进程数
        self._ref_counts: List[int] = [0] * total_frames

        # 空闲帧列表
        self._free_list: List[int] = list(range(total_frames))

        # 帧内容存储：frame_contents[frame_id] = bytes
        # 模拟物理内存，实际 OS 中这是硬件管理的
        self._frame_contents: Dict[int, bytearray] = {}

        # 替换算法的访问记录
        self._access_times: Dict[int, float] = {}
        self._access_counts: Dict[int, int] = {}

    def allocate(self) -> int:
        """
        分配一个空闲物理帧。

        Returns:
            帧号

        Raises:
            MemoryError: 如果没有空闲帧且无法置换
        """
        if self._free_list:
            frame = self._free_list.pop(0)
            self._ref_counts[frame] = 1
            self._frame_contents[frame] = bytearray(self.page_size)
            return frame

        # 无空闲帧，触发页面置换
        return self._evict()

    def incref(self, frame: int) -> None:
        """
        增加帧的引用计数（COW fork 时使用）。

        Args:
            frame: 帧号
        """
        if 0 <= frame < self.total_frames:
            self._ref_counts[frame] += 1

    def decref(self, frame: int) -> None:
        """
        减少帧的引用计数，归零时自动回收。

        Args:
            frame: 帧号
        """
        if 0 <= frame < self.total_frames:
            self._ref_counts[frame] -= 1
            if self._ref_counts[frame] <= 0:
                self._ref_counts[frame] = 0
                self._free_list.append(frame)
                # 清理帧内容
                if frame in self._frame_contents:
                    del self._frame_contents[frame]
                if frame in self._access_times:
                    del self._access_times[frame]
                if frame in self._access_counts:
                    del self._access_counts[frame]

    def get_ref_count(self, frame: int) -> int:
        """获取帧的引用计数"""
        if 0 <= frame < self.total_frames:
            return self._ref_counts[frame]
        return 0

    def is_shared(self, frame: int) -> bool:
        """检查帧是否被多个进程共享（COW）"""
        return self.get_ref_count(frame) > 1

    def get_free_count(self) -> int:
        """返回当前空闲帧数"""
        return len(self._free_list)

    def get_total_count(self) -> int:
        """返回总帧数"""
        return self.total_frames

    def get_frame_content(self, frame: int) -> Optional[bytearray]:
        """获取帧内容（用于 COW 复制）"""
        return self._frame_contents.get(frame)

    def set_frame_content(self, frame: int, content: bytearray) -> None:
        """设置帧内容"""
        if frame in self._frame_contents:
            self._frame_contents[frame] = content

    def copy_frame(self, src_frame: int, dst_frame: int) -> None:
        """复制帧内容（COW 触发时使用）"""
        src_content = self._frame_contents.get(src_frame)
        if src_content is not None:
            self._frame_contents[dst_frame] = bytearray(src_content)

    def _evict(self) -> int:
        """
        页面置换：选择一个帧换出。

        使用 LFU + 访问时间的双因子策略。

        Returns:
            被换出的帧号
        """
        best_score = -1
        victim = -1

        for frame in range(self.total_frames):
            if self._ref_counts[frame] == 0:
                continue

            # 计算 recency（距离上次访问的时间）
            last_access = self._access_times.get(frame, 0)
            recency = 1000 - last_access  # 简化：假设总时间 1000

            # 计算 frequency（访问频率的倒数）
            freq = self._access_counts.get(frame, 1)
            inv_freq = 1.0 / max(freq, 1)

            # 综合分数（越高越应该被换出）
            score = 0.6 * recency + 0.4 * inv_freq

            if score > best_score:
                best_score = score
                victim = frame

        if victim == -1:
            raise MemoryError("无法置换：所有帧都在使用中")

        # 清理被换出的帧
        self._ref_counts[victim] = 0
        if victim in self._frame_contents:
            del self._frame_contents[victim]
        if victim in self._access_times:
            del self._access_times[victim]
        if victim in self._access_counts:
            del self._access_counts[victim]

        return victim

    def get_stats(self) -> dict:
        """获取内存统计信息"""
        shared_frames = sum(1 for i in range(self.total_frames) if self._ref_counts[i] > 1)
        used_frames = sum(1 for i in range(self.total_frames) if self._ref_counts[i] > 0)

        return {
            'total_frames': self.total_frames,
            'used_frames': used_frames,
            'free_frames': len(self._free_list),
            'shared_frames': shared_frames,
            'page_size': self.page_size,
            'total_memory_mb': (self.total_frames * self.page_size) / (1024 * 1024),
            'used_memory_mb': (used_frames * self.page_size) / (1024 * 1024),
        }

    def __repr__(self) -> str:
        return f"FrameManager(total={self.total_frames}, free={len(self._free_list)})"


# ============================================================
# COW 管理器
# ============================================================
class COWManager:
    """
    写时复制（Copy-On-Write）管理器

    实现 fork 时的页表复制和写时复制触发。

    使用示例：
        fm = FrameManager(total_frames=256)
        cow = COWManager(fm)

        # fork 时复制页表（零拷贝）
        child_pt = cow.fork_page_table(parent_pt)

        # 写入页面时触发 COW
        cow.on_page_write(pid, page_num)
    """

    def __init__(self, frame_manager: FrameManager):
        self._fm = frame_manager

    def fork_page_table(self, parent_pt: PageTable) -> PageTable:
        """
        复制页表（COW 方式）。

        核心操作：
        1. 子进程的 PTE 指向同一个物理帧
        2. 父进程和子进程的 PTE 都设为只读
        3. 物理帧的 ref_count + 1

        Args:
            parent_pt: 父进程的页表

        Returns:
            子进程的页表（共享物理帧）
        """
        child_pt = PageTable(page_size=parent_pt.page_size)

        for page_num, parent_entry in parent_pt.get_all_entries().items():
            # 子进程指向同一物理帧
            child_entry = PageTableEntry(
                frame_id=parent_entry.frame_id,
                is_valid=parent_entry.is_valid,
                is_writable=False,  # 设为只读（COW）
                is_dirty=False,
                ref_count=1,
            )
            child_pt._entries[page_num] = child_entry

            # 父进程也设为只读
            parent_entry.is_writable = False

            # 物理帧引用计数 + 1
            self._fm.incref(parent_entry.frame_id)

        return child_pt

    def on_page_write(self, pt: PageTable, page_num: int) -> bool:
        """
        处理页面写入。

        如果页面是只读的（COW），则：
        1. 如果 ref_count == 1：直接改权限
        2. 如果 ref_count > 1：复制物理帧，更新页表

        Args:
            pt: 进程的页表
            page_num: 要写入的虚拟页号

        Returns:
            True 表示触发了 COW，False 表示正常写入
        """
        entry = pt.get_entry(page_num)
        if entry is None:
            return False

        if entry.is_writable:
            # 正常写入，标记为脏页
            entry.is_dirty = True
            return False

        # 触发 COW！
        frame = entry.frame_id
        ref_count = self._fm.get_ref_count(frame)

        if ref_count <= 1:
            # 只剩自己引用，直接改权限
            entry.is_writable = True
            entry.is_dirty = True
        else:
            # 多人共享，需要复制物理帧
            new_frame = self._fm.allocate()
            self._fm.copy_frame(frame, new_frame)

            # 更新页表
            entry.frame_id = new_frame
            entry.is_writable = True
            entry.is_dirty = True

            # 原帧引用计数减 1
            self._fm.decref(frame)

        return True

    def release_all_frames(self, pt: PageTable) -> None:
        """
        释放页表中所有物理帧（进程退出时调用）。

        Args:
            pt: 进程的页表
        """
        for page_num, entry in pt.get_all_entries().items():
            self._fm.decref(entry.frame_id)

        pt._entries.clear()

    def get_cow_stats(self, pt: PageTable) -> dict:
        """获取 COW 统计信息"""
        shared_pages = 0
        private_pages = 0
        total_pages = 0

        for entry in pt.get_all_entries().values():
            total_pages += 1
            if self._fm.is_shared(entry.frame_id):
                shared_pages += 1
            else:
                private_pages += 1

        return {
            'total_pages': total_pages,
            'shared_pages': shared_pages,
            'private_pages': private_pages,
            'memory_saved_kb': shared_pages * self._fm.page_size / 1024,
        }

    def __repr__(self) -> str:
        return f"COWManager(frame_manager={self._fm})"
