"""
dashboard.py — 实时仪表盘

整合所有可视化组件，提供系统状态的全景视图。
"""

from typing import Dict, Optional
from core.pcb import PCB, ProcessState
from kernel.kernel import Kernel
from visualizer.tree_view import visualize_tree_with_status, get_process_summary
from visualizer.scheduler_view import visualize_queue_snapshot, visualize_cpu_utilization, visualize_context_switches
from visualizer.memory_view import visualize_frame_map, visualize_memory_stats


def show_dashboard(kernel: Kernel) -> str:
    """
    显示系统仪表盘。

    Args:
        kernel: 内核实例

    Returns:
        仪表盘字符串
    """
    processes = kernel.get_all_processes()
    stats = kernel.get_stats()

    lines = [
        "=" * 60,
        "系统仪表盘",
        "=" * 60,
        "",
        f"时钟: Tick {stats['tick_count']}",
        f"当前运行: PID={stats['current_pid']}",
        "",
        get_process_summary(processes),
        "",
        "进程树:",
        visualize_tree_with_status(processes, kernel.process_tree),
        "",
        visualize_queue_snapshot(
            kernel.scheduler.get_queue_snapshot(),
            processes
        ),
        "",
        visualize_memory_stats(kernel.memory_manager._fm),
        "",
        visualize_cpu_utilization(
            [],  # 暂无历史
            stats['tick_count']
        ),
        "",
        visualize_context_switches(
            kernel.get_context_switch_history(),
            processes
        ),
        "=" * 60,
    ]

    return "\n".join(lines)


def show_process_detail(kernel: Kernel, pid: int) -> str:
    """
    显示单个进程的详细信息。

    Args:
        kernel: 内核实例
        pid: 进程 PID

    Returns:
        进程详情字符串
    """
    pcb = kernel.get_process(pid)
    if pcb is None:
        return f"进程 PID={pid} 不存在"

    lines = [
        f"进程详情: PID={pid}",
        "-" * 40,
        f"名称: {pcb.name}",
        f"状态: {pcb.state}",
        f"父进程: PID={pcb.ppid}",
        f"子进程: {pcb.children}",
        f"优先级: {pcb.priority}",
        f"nice值: {pcb.nice}",
        "",
        "时间统计:",
        f"  到达时间: {pcb.arrival_time}",
        f"  首次运行: {pcb.start_time}",
        f"  CPU时间: {pcb.cpu_time}",
        f"  等待时间: {pcb.wait_time}",
        f"  突发时间: {pcb.burst_time}",
        "",
        "内存信息:",
        f"  内存使用: {pcb.memory_usage} 字节",
        f"  缺页次数: {pcb.page_faults}",
        f"  COW复制: {pcb.cow_copies}",
        "",
        "调度信息:",
        f"  stride: {pcb.stride:.2f}",
        f"  pass_value: {pcb.pass_value:.2f}",
        f"  上下文切换: {pcb.context_switches}",
        "",
        "退出信息:",
        f"  退出码: {pcb.exit_code}",
        f"  等待队列: {pcb.wait_queue}",
    ]

    return "\n".join(lines)
