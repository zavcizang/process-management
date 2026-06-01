"""
test_kernel.py — 内核和系统调用集成测试

测试内容：
1. 内核初始化和 init 进程
2. fork + waitpid 完整流程
3. 级联退出 + 孤儿回收
4. 进程树可视化
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kernel.kernel import Kernel
from core.pcb import ProcessState
from error_codes import ErrorCode


def test_kernel_init():
    """测试内核初始化"""
    kernel = Kernel(max_processes=16)

    # init 进程应该自动创建
    init = kernel.get_process(0)
    assert init is not None
    assert init.pid == 0
    assert init.name == "init"
    assert init.ppid == -1
    assert init.state == ProcessState.READY

    print("[PASS] 内核初始化测试通过")


def test_create_process():
    """测试创建进程"""
    kernel = Kernel(max_processes=16)

    shell_pid = kernel.create_process("shell", parent_pid=0)
    assert shell_pid == 1

    shell = kernel.get_process(shell_pid)
    assert shell is not None
    assert shell.name == "shell"
    assert shell.ppid == 0
    assert shell.state == ProcessState.READY

    # 进程树中应该有 shell
    assert kernel.process_tree.has_process(shell_pid)
    assert shell_pid in kernel.process_tree.get_children(0)

    print("[PASS] 创建进程测试通过")


def test_fork_and_waitpid():
    """测试 fork + waitpid 完整流程"""
    kernel = Kernel(max_processes=16)
    syscall = kernel.syscall

    # 创建父进程
    parent_pid = kernel.create_process("parent", parent_pid=0)

    # fork
    child_pid = syscall.sys_fork(parent_pid)
    assert child_pid > 0
    assert child_pid != parent_pid

    # 检查子进程
    child = kernel.get_process(child_pid)
    assert child is not None
    assert child.ppid == parent_pid
    assert child.state == ProcessState.READY

    # 推进时钟，让子进程被调度运行
    for _ in range(5):
        kernel.tick()

    # 子进程退出（需要先在 RUNNING 状态才能转 ZOMBIE）
    # 如果子进程不在 RUNNING，需要先手动设置
    if child.state == ProcessState.READY:
        child.set_state(ProcessState.RUNNING)
    syscall.sys_exit(child_pid, exit_code=42)
    assert child.state == ProcessState.ZOMBIE

    # 父进程 waitpid
    result = syscall.sys_waitpid(parent_pid, child_pid)
    assert result == 42

    # 子进程应该被销毁
    assert kernel.get_process(child_pid) is None

    print("[PASS] fork + waitpid 测试通过")


def test_waitpid_any():
    """测试 waitpid 等待任意子进程"""
    kernel = Kernel(max_processes=16)
    syscall = kernel.syscall

    parent_pid = kernel.create_process("parent", parent_pid=0)

    # 创建两个子进程
    child1 = syscall.sys_fork(parent_pid)
    child2 = syscall.sys_fork(parent_pid)

    # 子进程1退出（先设置为 RUNNING）
    c1 = kernel.get_process(child1)
    c1.set_state(ProcessState.RUNNING)
    syscall.sys_exit(child1, exit_code=1)

    # waitpid(-1) 应该能回收子进程1
    result = syscall.sys_waitpid(parent_pid, -1)
    assert result == 1

    # 子进程2退出
    c2 = kernel.get_process(child2)
    c2.set_state(ProcessState.RUNNING)
    syscall.sys_exit(child2, exit_code=2)
    result = syscall.sys_waitpid(parent_pid, -1)
    assert result == 2

    print("[PASS] waitpid 任意子进程测试通过")


def test_orphan_reparenting():
    """测试孤儿进程回收

    进程树：init → parent → child → grandchild
    杀死 parent 后，child 成为孤儿挂到 init 下
    grandchild 的父进程仍然是 child
    """
    kernel = Kernel(max_processes=16)
    syscall = kernel.syscall

    # 创建进程树：init → parent → child → grandchild
    parent_pid = kernel.create_process("parent", parent_pid=0)
    child_pid = syscall.sys_fork(parent_pid)
    grandchild_pid = syscall.sys_fork(child_pid)

    # 杀死 parent（先设置为 RUNNING）
    parent = kernel.get_process(parent_pid)
    parent.set_state(ProcessState.RUNNING)
    syscall.sys_exit(parent_pid, exit_code=0)

    # child 应该被挂到 init 下（成为 init 的直接子进程）
    child = kernel.get_process(child_pid)
    assert child is not None
    assert child.ppid == 0  # init PID=0
    assert child_pid in kernel.process_tree.get_children(0)

    # grandchild 的父进程仍然是 child
    grandchild = kernel.get_process(grandchild_pid)
    assert grandchild is not None
    assert grandchild.ppid == child_pid

    print("[PASS] 孤儿进程回收测试通过")


def test_cascade_exit():
    """测试级联退出"""
    kernel = Kernel(max_processes=16)
    syscall = kernel.syscall

    # 创建进程树：init → A → B → C
    a_pid = kernel.create_process("A", parent_pid=0)
    b_pid = syscall.sys_fork(a_pid)
    c_pid = syscall.sys_fork(b_pid)

    # 杀死 A（先设置为 RUNNING）
    a = kernel.get_process(a_pid)
    a.set_state(ProcessState.RUNNING)
    syscall.sys_exit(a_pid, exit_code=0)

    # B 和 C 应该被挂到 init 下
    b = kernel.get_process(b_pid)
    c = kernel.get_process(c_pid)

    assert b is not None
    assert b.ppid == 0
    assert c is not None
    assert c.ppid == b_pid  # C 的父进程还是 B

    print("[PASS] 级联退出测试通过")


def test_process_tree_visualization():
    """测试进程树可视化"""
    kernel = Kernel(max_processes=16)
    syscall = kernel.syscall

    # 创建进程树
    shell_pid = kernel.create_process("shell", parent_pid=0)
    daemon_pid = kernel.create_process("daemon", parent_pid=0)
    editor_pid = syscall.sys_fork(shell_pid)

    viz = kernel.process_tree.visualize_ascii()
    assert "PID=0" in viz
    assert "PID=1" in viz
    assert "PID=2" in viz

    print("[PASS] 进程树可视化测试通过")
    print("  输出：")
    for line in viz.split("\n"):
        print(f"    {line}")


def test_kernel_tick():
    """测试内核时钟推进"""
    kernel = Kernel(max_processes=16)

    # 创建进程
    kernel.create_process("test", parent_pid=0)

    # 推进时钟
    for _ in range(10):
        kernel.tick()

    stats = kernel.get_stats()
    assert stats['tick_count'] == 10

    print("[PASS] 内核时钟测试通过")


def test_system_stats():
    """测试系统统计"""
    kernel = Kernel(max_processes=16)

    kernel.create_process("p1", parent_pid=0)
    kernel.create_process("p2", parent_pid=0)

    stats = kernel.get_stats()
    assert stats['processes']['total_processes'] == 3  # init + p1 + p2
    assert stats['processes']['max_processes'] == 16

    print("[PASS] 系统统计测试通过")


if __name__ == "__main__":
    test_kernel_init()
    test_create_process()
    test_fork_and_waitpid()
    test_waitpid_any()
    test_orphan_reparenting()
    test_cascade_exit()
    test_process_tree_visualization()
    test_kernel_tick()
    test_system_stats()
    print("\n[DONE] 所有内核测试通过！")
