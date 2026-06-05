"""
basic_fork.py — StrideCOWScheduler 基础 fork/wait 演示

项目: StrideCOWScheduler — 进程管理内核模拟器
作者: zavci (zjh3432512933)
仓库: https://gitee.com/zjh3432512933/process-management

演示内容：
1. 创建父进程
2. fork 子进程
3. 子进程执行并退出
4. 父进程 waitpid 回收子进程
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kernel.kernel import Kernel
from core.pcb import ProcessState


def main():
    print("=" * 60)
    print("  演示: 基础 fork/wait 流程")
    print("=" * 60)

    # 创建内核
    kernel = Kernel(max_processes=16)
    syscall = kernel.syscall

    # 创建父进程
    parent_pid = kernel.create_process("parent", parent_pid=0)
    print(f"\n1. 创建父进程: PID={parent_pid}")

    # 推进时钟，让父进程运行
    kernel.tick()

    # fork 子进程
    print(f"\n2. 父进程 fork 子进程...")
    child_pid = syscall.sys_fork(parent_pid)
    print(f"   子进程已创建: PID={child_pid}")

    # 推进时钟，让子进程运行
    print(f"\n3. 子进程开始执行...")
    for i in range(5):
        kernel.tick()
        current = kernel.current_pid
        if current:
            pcb = kernel.get_process(current)
            print(f"   Tick {kernel._tick_count}: PID={current} ({pcb.name}) 运行中")

    # 子进程退出
    print(f"\n4. 子进程退出 (exit_code=42)...")
    child = kernel.get_process(child_pid)
    if child:
        if child.state == ProcessState.READY:
            child.set_state(ProcessState.RUNNING)
        syscall.sys_exit(child_pid, exit_code=42)

    # 父进程 waitpid
    print(f"\n5. 父进程 waitpid 回收子进程...")
    result = syscall.sys_waitpid(parent_pid, child_pid)
    print(f"   获得子进程退出码: {result}")

    # 显示最终状态
    print(f"\n6. 最终进程状态:")
    print(f"   父进程 PID={parent_pid}: 存在={kernel.get_process(parent_pid) is not None}")
    print(f"   子进程 PID={child_pid}: 存在={kernel.get_process(child_pid) is not None}")

    print("\n" + "=" * 60)
    print("  演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
