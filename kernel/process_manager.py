"""
process_manager.py — 进程管理器

负责进程的完整生命周期管理：
- 进程创建（分配 PID、初始化 PCB、注册到调度器和进程树）
- 进程销毁（释放资源、从调度器和进程树中移除）
- 状态转换（统一管理进程状态变更）
- PID 分配（全局唯一、单调递增）

设计原则：
- PID 0 保留给 init 进程
- 进程数有上限（fork bomb 防护）
- 所有状态转换通过 set_state() 验证
"""

from typing import Dict, Optional

from core.pcb import PCB, ProcessState
from core.process_tree import ProcessTree
from kernel.scheduler import StrideScheduler
from kernel.memory_manager import COWManager, PageTable


class ProcessManager:
    """
    进程管理器

    使用示例：
        pm = ProcessManager(max_processes=64)
        pid = pm.create_process("shell", parent_pid=0)
        pcb = pm.get_process(pid)
        pm.destroy_process(pid)
    """

    def __init__(self, max_processes: int = 64):
        """
        Args:
            max_processes: 最大进程数（fork bomb 防护）
        """
        self._max_processes = max_processes
        self._processes: Dict[int, PCB] = {}
        self._next_pid = 0
        self._current_tick = 0

        # 关联的子系统（由 Kernel 注入）
        self._tree: Optional[ProcessTree] = None
        self._scheduler: Optional[StrideScheduler] = None
        self._cow_manager: Optional[COWManager] = None

        # 统计
        self._total_created = 0
        self._total_destroyed = 0

    def bind(self, tree: ProcessTree, scheduler: StrideScheduler,
             cow_manager: COWManager) -> None:
        """绑定子系统（Kernel 初始化时调用）"""
        self._tree = tree
        self._scheduler = scheduler
        self._cow_manager = cow_manager

    def create_process(self, name: str, parent_pid: int = 0,
                       priority: int = 128) -> int:
        """
        创建新进程。

        完整流程：
        1. 检查进程数上限
        2. 分配 PID
        3. 创建 PCB
        4. 注册到进程树
        5. 注册到调度器
        6. 分配初始页表
        7. 设置状态为 READY

        Args:
            name: 进程名
            parent_pid: 父进程 PID（默认为 init）
            priority: 优先级 (0-255)

        Returns:
            新进程的 PID

        Raises:
            RuntimeError: 如果达到进程数上限
        """
        # 检查进程数上限
        if len(self._processes) >= self._max_processes:
            raise RuntimeError(f"达到进程数上限 {self._max_processes}")

        # 分配 PID
        pid = self._next_pid
        self._next_pid += 1

        # 创建 PCB
        pcb = PCB(
            pid=pid,
            ppid=parent_pid,
            name=name,
            priority=priority,
            arrival_time=self._current_tick,
        )
        pcb.page_table = PageTable(page_size=4096)

        # 注册到进程树
        if self._tree:
            self._tree.add_process(pid, parent_pid)
            # 更新父进程的 children 列表
            parent = self._processes.get(parent_pid)
            if parent:
                parent.children.append(pid)

        # 注册到调度器
        if self._scheduler:
            self._scheduler.register(pid, priority=priority)

        # 设置状态为 READY 并加入调度队列
        pcb.set_state(ProcessState.READY)
        if self._scheduler:
            self._scheduler.enqueue(pid)

        # 存储 PCB
        self._processes[pid] = pcb
        self._total_created += 1

        return pid

    def destroy_process(self, pid: int) -> None:
        """
        销毁进程，释放所有资源。

        流程：
        1. 释放物理内存帧（COW）
        2. 从调度器中移除
        3. 从进程树中移除
        4. 删除 PCB

        Args:
            pid: 进程 PID
        """
        pcb = self._processes.get(pid)
        if pcb is None:
            return

        # 释放物理内存帧
        if self._cow_manager and pcb.page_table:
            self._cow_manager.release_all_frames(pcb.page_table)

        # 从调度器中移除
        if self._scheduler:
            self._scheduler.unregister(pid)

        # 从进程树中移除
        if self._tree and self._tree.has_process(pid):
            self._tree.remove_process(pid)

        # 从父进程的 children 列表中移除
        parent = self._processes.get(pcb.ppid)
        if parent and pid in parent.children:
            parent.children.remove(pid)

        # 删除 PCB
        del self._processes[pid]
        self._total_destroyed += 1

    def get_process(self, pid: int) -> Optional[PCB]:
        """获取进程 PCB"""
        return self._processes.get(pid)

    def get_all_processes(self) -> Dict[int, PCB]:
        """获取所有进程"""
        return self._processes.copy()

    def get_process_count(self) -> int:
        """获取当前进程数"""
        return len(self._processes)

    def set_current_tick(self, tick: int) -> None:
        """设置当前时间（由 Kernel 调用）"""
        self._current_tick = tick

    def get_stats(self) -> dict:
        """获取进程管理器统计信息"""
        states = {}
        for pcb in self._processes.values():
            states[pcb.state] = states.get(pcb.state, 0) + 1

        return {
            'total_processes': len(self._processes),
            'max_processes': self._max_processes,
            'total_created': self._total_created,
            'total_destroyed': self._total_destroyed,
            'states': states,
        }

    def __repr__(self) -> str:
        return f"ProcessManager(processes={len(self._processes)}, max={self._max_processes})"
