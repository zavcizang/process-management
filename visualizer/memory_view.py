"""
memory_view.py — 内存页表可视化

提供内存状态的可视化：
1. 物理帧分配图
2. COW 共享状态
3. 内存使用统计
"""

from typing import Dict, List, Optional
from kernel.memory_manager import FrameManager, PageTable


def visualize_frame_map(frame_manager: FrameManager) -> str:
    """
    可视化物理帧分配状态。

    示例输出：
        物理内存帧分配 (共 256 帧, 已用 12 帧)
        ┌────────────────────────────────────────┐
        │██·█·██·█································│
        │··········································│
        │··········································│
        │··········································│
        └────────────────────────────────────────┘
        ██ = 已分配  · = 空闲

    Args:
        frame_manager: 帧管理器

    Returns:
        帧分配图字符串
    """
    total = frame_manager.get_total_count()
    stats = frame_manager.get_stats()
    used = stats['used_frames']
    free = stats['free_frames']

    # 构建帧分配图
    line_width = 50
    lines = [
        f"物理内存帧分配 (共 {total} 帧, 已用 {used} 帧)",
        "┌" + "─" * line_width + "┐",
    ]

    # 逐行显示帧状态
    for row_start in range(0, total, line_width):
        row_end = min(row_start + line_width, total)
        row = "│"
        for frame in range(row_start, row_end):
            if frame < total:
                ref_count = frame_manager.get_ref_count(frame)
                if ref_count > 1:
                    row += "▓"  # 共享帧
                elif ref_count > 0:
                    row += "█"  # 已分配
                else:
                    row += "·"  # 空闲
        row += "│"
        lines.append(row)

    lines.append("└" + "─" * line_width + "┘")
    lines.append("██ = 已分配  ▓ = 共享(COW)  · = 空闲")

    return "\n".join(lines)


def visualize_page_table(pid: int, page_table: PageTable,
                         frame_manager: FrameManager) -> str:
    """
    可视化进程的页表。

    示例输出：
        进程 PID=1 的页表:
        ┌──────┬──────┬──────┬──────┬──────┐
        │ 页号 │ 帧号 │ 可写 │ 脏页 │ 引用 │
        ├──────┼──────┼──────┼──────┼──────┤
        │    0 │    5 │  是  │  否  │    2 │
        │    1 │    8 │  否  │  是  │    1 │
        └──────┴──────┴──────┴──────┴──────┘

    Args:
        pid: 进程 PID
        page_table: 页表
        frame_manager: 帧管理器

    Returns:
        页表可视化字符串
    """
    entries = page_table.get_all_entries()

    if not entries:
        return f"进程 PID={pid} 的页表: 空"

    lines = [
        f"进程 PID={pid} 的页表:",
        "┌──────┬──────┬──────┬──────┬──────┐",
        "│ 页号 │ 帧号 │ 可写 │ 脏页 │ 引用 │",
        "├──────┼──────┼──────┼──────┼──────┤",
    ]

    for page_num, entry in sorted(entries.items()):
        writable = "是" if entry.is_writable else "否"
        dirty = "是" if entry.is_dirty else "否"
        ref_count = frame_manager.get_ref_count(entry.frame_id)
        lines.append(f"│ {page_num:4d} │ {entry.frame_id:4d} │ {writable:4s} │ {dirty:4s} │ {ref_count:4d} │")

    lines.append("└──────┴──────┴──────┴──────┴──────┘")

    return "\n".join(lines)


def visualize_memory_stats(frame_manager: FrameManager) -> str:
    """
    可视化内存统计信息。

    Args:
        frame_manager: 帧管理器

    Returns:
        内存统计字符串
    """
    stats = frame_manager.get_stats()

    used = stats['used_frames']
    total = stats['total_frames']
    shared = stats['shared_frames']
    page_size = stats['page_size']

    # 使用率进度条
    usage = used / total * 100
    bar_width = 30
    filled = int(usage / 100 * bar_width)
    bar = "█" * filled + "·" * (bar_width - filled)

    lines = [
        "内存统计:",
        f"  总帧数: {total}",
        f"  已使用: {used}",
        f"  空闲: {stats['free_frames']}",
        f"  共享帧: {shared}",
        f"  页大小: {page_size} 字节",
        f"  总内存: {stats['total_memory_mb']:.2f} MB",
        f"  已使用: {stats['used_memory_mb']:.2f} MB",
        f"  使用率: [{bar}] {usage:.1f}%",
    ]

    return "\n".join(lines)
