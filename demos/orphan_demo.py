"""
orphan_demo.py — StrideCOWScheduler 孤儿进程回收演示

项目: StrideCOWScheduler — 进程管理内核模拟器
作者: zavci (zjh3432512933)
仓库: https://gitee.com/zjh3432512933/process-management

演示内容：
1. 创建进程树: init → A → B → C
2. 杀死进程 A
3. 进程 B 和 C 成为孤儿
4. 孤儿进程被重新挂到 init 下
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kernel.kernel import Kernel
from core.pcb import ProcessState


def main():
    print("=" * 60)
    print("  演示: 孤儿进程回收")
    print("=" * 60)

    # 创建内核
    kernel = Kernel(max_processes=16)
    syscall = kernel.syscall

    # 创建进程树: init → A → B → C
    print(f"\n1. 创建进程树: init → A → B → C")
    a_pid = kernel.create_process("A", parent_pid=0)
    b_pid = syscall.sys_fork(a_pid)
    c_pid = syscall.sys_fork(b_pid)

    print(f"   init (PID=0)")
    print(f"   └── A (PID={a_pid})")
    print(f"       └── B (PID={b_pid})")
    print(f"           └── C (PID={c_pid})")

    # 显示进程树
    print(f"\n2. 当前进程树:")
    print(kernel.process_tree.visualize_ascii())

    # 杀死进程 A
    print(f"\n3. 杀死进程 A (PID={a_pid})...")
    a = kernel.get_process(a_pid)
    if a:
        if a.state == ProcessState.READY:
            a.set_state(ProcessState.RUNNING)
        syscall.sys_exit(a_pid, exit_code=0)

    # 检查孤儿回收
    print(f"\n4. 检查孤儿回收:")
    b = kernel.get_process(b_pid)
    c = kernel.get_process(c_pid)

    if b:
        print(f"   B (PID={b_pid}): ppid={b.ppid} (应该是 0)")
    if c:
        print(f"   C (PID={c_pid}): ppid={c.ppid} (应该是 {b_pid})")

    # 显示最终进程树
    print(f"\n5. 最终进程树:")
    print(kernel.process_tree.visualize_ascii())

    # 清理
    print(f"\n6. 清理进程...")
    if b:
        if b.state == ProcessState.READY:
            b.set_state(ProcessState.RUNNING)
        syscall.sys_exit(b_pid, exit_code=0)
    if c:
        if c.state == ProcessState.READY:
            c.set_state(ProcessState.RUNNING)
        syscall.sys_exit(c_pid, exit_code=0)

    print(f"\n" + "=" * 60)
    print("  演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
