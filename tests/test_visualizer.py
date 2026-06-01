"""
test_visualizer.py — 可视化模块测试

测试内容：
1. 进程树可视化
2. 调度队列可视化
3. 内存页表可视化
4. 仪表盘
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kernel.kernel import Kernel
from visualizer import (
    visualize_tree_with_status,
    get_process_summary,
    visualize_queue_snapshot,
    visualize_frame_map,
    visualize_page_table,
    visualize_memory_stats,
    show_dashboard,
    show_process_detail,
)


def test_tree_visualization():
    """测试进程树可视化"""
    kernel = Kernel(max_processes=16)
    kernel.create_process("shell", parent_pid=0)
    kernel.create_process("daemon", parent_pid=0)

    processes = kernel.get_all_processes()
    viz = visualize_tree_with_status(processes, kernel.process_tree)

    assert "init" in viz
    assert "shell" in viz
    assert "daemon" in viz
    assert "PID=" in viz

    print("[PASS] 进程树可视化测试通过")


def test_process_summary():
    """测试进程统计摘要"""
    kernel = Kernel(max_processes=16)
    kernel.create_process("p1", parent_pid=0)
    kernel.create_process("p2", parent_pid=0)

    processes = kernel.get_all_processes()
    summary = get_process_summary(processes)

    assert "总计: 3" in summary
    assert "就绪:" in summary

    print("[PASS] 进程统计摘要测试通过")


def test_queue_snapshot():
    """测试调度队列可视化"""
    kernel = Kernel(max_processes=16)
    kernel.create_process("p1", parent_pid=0)
    kernel.create_process("p2", parent_pid=0)

    snapshot = kernel.scheduler.get_queue_snapshot()
    processes = kernel.get_all_processes()
    viz = visualize_queue_snapshot(snapshot, processes)

    assert "就绪队列" in viz
    assert "PID" in viz

    print("[PASS] 调度队列可视化测试通过")


def test_frame_map():
    """测试帧分配图"""
    kernel = Kernel(max_processes=16, total_frames=32)
    kernel.create_process("p1", parent_pid=0)

    viz = visualize_frame_map(kernel.memory_manager._fm)

    assert "物理内存帧" in viz
    assert "已分配" in viz

    print("[PASS] 帧分配图测试通过")


def test_page_table():
    """测试页表可视化"""
    kernel = Kernel(max_processes=16)
    pid = kernel.create_process("p1", parent_pid=0)
    pcb = kernel.get_process(pid)

    # 分配一些帧
    for i in range(3):
        frame = kernel.memory_manager._fm.allocate()
        pcb.page_table.map(i, frame)

    viz = visualize_page_table(pid, pcb.page_table, kernel.memory_manager._fm)

    assert "页表" in viz
    assert "页号" in viz
    assert "帧号" in viz

    print("[PASS] 页表可视化测试通过")


def test_memory_stats():
    """测试内存统计"""
    kernel = Kernel(max_processes=16, total_frames=32)

    viz = visualize_memory_stats(kernel.memory_manager._fm)

    assert "内存统计" in viz
    assert "总帧数" in viz
    assert "使用率" in viz

    print("[PASS] 内存统计测试通过")


def test_dashboard():
    """测试仪表盘"""
    kernel = Kernel(max_processes=16)
    kernel.create_process("shell", parent_pid=0)

    viz = show_dashboard(kernel)

    assert "系统仪表盘" in viz
    assert "时钟" in viz
    assert "进程树" in viz
    assert "就绪队列" in viz
    assert "内存统计" in viz

    print("[PASS] 仪表盘测试通过")


def test_process_detail():
    """测试进程详情"""
    kernel = Kernel(max_processes=16)
    pid = kernel.create_process("test", parent_pid=0)

    viz = show_process_detail(kernel, pid)

    assert "进程详情" in viz
    assert "test" in viz
    assert "优先级" in viz
    assert "CPU时间" in viz

    print("[PASS] 进程详情测试通过")


if __name__ == "__main__":
    test_tree_visualization()
    test_process_summary()
    test_queue_snapshot()
    test_frame_map()
    test_page_table()
    test_memory_stats()
    test_dashboard()
    test_process_detail()
    print("\n[DONE] 所有可视化测试通过！")
