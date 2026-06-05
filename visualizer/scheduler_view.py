"""
scheduler_view.py — StrideCOWScheduler 调度器可视化

项目: StrideCOWScheduler — 进程管理内核模拟器
作者: zavci (zjh3432512933)
仓库: https://gitee.com/zjh3432512933/process-management

提供调度过程的可视化：
1. 调度甘特图（ASCII）
2. 就绪队列状态
3. CPU 利用率统计
"""

from typing import Dict, List, Tuple, Optional
from core.pcb import PCB, ProcessState


def visualize_gantt(history: List[Tuple[int, Optional[int]]], width: int = 60) -> str:
    """
    生成调度甘特图的 ASCII 可视化。

    Args:
        history: [(tick, pid), ...] 调度历史
        width: 图表宽度

    Returns:
        甘特图字符串
    """
    if not history:
        return "(无调度历史)"

    # 收集所有进程
    pids = set()
    for _, pid in history:
        if pid is not None:
            pids.add(pid)

    if not pids:
        return "(CPU 空闲)"

    pids = sorted(pids)

    # 构建图表
    lines = ["调度甘特图:"]

    # 时间轴
    time_line = "      "
    for tick in range(len(history)):
        if tick % 10 == 0:
            time_line += str(tick // 10)
        else:
            time_line += " "
    lines.append(time_line)

    # 每个进程的执行情况
    for pid in pids:
        line = f"P{pid:3d} |"
        for tick, running_pid in history:
            if running_pid == pid:
                line += "█"
            elif running_pid is None:
                line += "·"
            else:
                line += " "
        lines.append(line)

    # 图例
    lines.append("      " + "-" * len(history))
    lines.append("      █ = 运行  · = 空闲")

    return "\n".join(lines)


def visualize_queue_snapshot(snapshot: List[Tuple[int, float]],
                             processes: Dict[int, PCB]) -> str:
    """
    可视化就绪队列快照。

    Args:
        snapshot: [(pid, pass_value), ...]
        processes: 进程字典

    Returns:
        队列可视化字符串
    """
    if not snapshot:
        return "就绪队列: 空"

    lines = ["就绪队列:"]
    lines.append(f"  {'PID':<8} {'名称':<12} {'pass_value':<12} {'优先级':<8}")
    lines.append("  " + "-" * 42)

    for pid, pass_value in snapshot:
        pcb = processes.get(pid)
        if pcb:
            lines.append(f"  {pid:<8} {pcb.name:<12} {pass_value:<12.2f} {pcb.priority:<8}")

    return "\n".join(lines)


def visualize_cpu_utilization(history: List[Tuple[int, Optional[int]]],
                              total_ticks: int) -> str:
    """
    计算并可视化 CPU 利用率。

    Args:
        history: 调度历史
        total_ticks: 总时间片数

    Returns:
        CPU 利用率字符串
    """
    if total_ticks == 0:
        return "CPU 利用率: N/A"

    busy_ticks = sum(1 for _, pid in history if pid is not None)
    utilization = busy_ticks / total_ticks * 100

    # 进度条
    bar_width = 40
    filled = int(utilization / 100 * bar_width)
    bar = "█" * filled + "·" * (bar_width - filled)

    lines = [
        f"CPU 利用率: {utilization:.1f}%",
        f"  [{bar}] {busy_ticks}/{total_ticks} ticks",
    ]

    return "\n".join(lines)


def visualize_context_switches(history: List[Tuple[int, int, int]],
                               processes: Dict[int, PCB]) -> str:
    """
    可视化上下文切换历史。

    Args:
        history: [(tick, old_pid, new_pid), ...]
        processes: 进程字典

    Returns:
        上下文切换可视化字符串
    """
    if not history:
        return "上下文切换: 无"

    lines = [
        f"上下文切换历史 (共 {len(history)} 次):",
        f"  {'Tick':<8} {'从':<15} {'到':<15}",
        "  " + "-" * 40,
    ]

    # 只显示最近的 10 次
    recent = history[-10:] if len(history) > 10 else history
    for tick, old_pid, new_pid in recent:
        old_name = processes[old_pid].name if old_pid and old_pid in processes else "空闲"
        new_name = processes[new_pid].name if new_pid in processes else "未知"
        lines.append(f"  {tick:<8} {old_name}({old_pid}){'':<5} {new_name}({new_pid})")

    if len(history) > 10:
        lines.append(f"  ... (还有 {len(history) - 10} 条记录)")

    return "\n".join(lines)
