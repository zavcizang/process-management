"""
zombie_demo.py — StrideCOWScheduler 僵尸进程演示

项目: StrideCOWScheduler — 进程管理内核模拟器
作者: zavci (zjh3432512933)
仓库: https://gitee.com/zjh3432512933/process-management

演示内容：
1. 创建父进程和多个子进程
2. 子进程退出但父进程不 wait
3. 子进程变为 ZOMBIE 状态
4. 父进程调用 waitpid 回收
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kernel.kernel import Kernel
from core.pcb import ProcessState


def main():
    print("=" * 60)
    print("  演示: 僵尸进程")
    print("=" * 60)

    # 创建内核
    kernel = Kernel(max_processes=16)
    syscall = kernel.syscall

    # 创建父进程
    parent_pid = kernel.create_process("lazy_parent", parent_pid=0)
    print(f"\n1. 创建父进程: PID={parent_pid}")

    # 创建 5 个子进程
    print(f"\n2. 创建 5 个子进程...")
    child_pids = []
    for i in range(5):
        child_pid = syscall.sys_fork(parent_pid)
        child_pids.append(child_pid)
        print(f"   子进程 {i+1}: PID={child_pid}")

    # 子进程退出（但父进程不 wait）
    print(f"\n3. 子进程退出（父进程不 wait）...")
    for i, child_pid in enumerate(child_pids):
        child = kernel.get_process(child_pid)
        if child:
            if child.state == ProcessState.READY:
                child.set_state(ProcessState.RUNNING)
            syscall.sys_exit(child_pid, exit_code=i)

    # 检查 ZOMBIE 状态
    print(f"\n4. 检查进程状态:")
    zombies = []
    for child_pid in child_pids:
        child = kernel.get_process(child_pid)
        if child:
            if child.state == ProcessState.ZOMBIE:
                zombies.append(child_pid)
                print(f"   PID={child_pid}: ZOMBIE (僵尸进程)")

    print(f"\n   共有 {len(zombies)} 个僵尸进程")

    # 父进程 waitpid 回收
    print(f"\n5. 父进程调用 waitpid 回收...")
    for child_pid in child_pids:
        result = syscall.sys_waitpid(parent_pid, child_pid)
        if isinstance(result, int) and result >= 0:
            print(f"   回收 PID={child_pid}, exit_code={result}")

    # 最终状态
    print(f"\n6. 最终状态:")
    print(f"   父进程 PID={parent_pid}: 存在={kernel.get_process(parent_pid) is not None}")
    print(f"   子进程: 全部已回收")

    print("\n" + "=" * 60)
    print("  演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
