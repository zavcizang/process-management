"""
error_handling_demo.py — StrideCOWScheduler 错误处理演示

项目: StrideCOWScheduler — 进程管理内核模拟器
作者: zavci (zjh3432512933)
仓库: https://gitee.com/zjh3432512933/process-management

演示内容：
1. 尝试杀死 init 进程（EPERM 错误）
2. Fork Bomb 防护（最大进程数限制）
3. 无效参数处理
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kernel.kernel import Kernel
from error_codes import ErrorCode


def main():
    print("=" * 60)
    print("  演示: 错误处理 — 安全机制")
    print("=" * 60)

    # 创建内核
    kernel = Kernel(max_processes=8)  # 设置较小的进程数限制
    syscall = kernel.syscall

    # 创建一些进程
    print(f"\n1. 创建一些进程:")
    p1 = kernel.create_process("shell", parent_pid=0)
    p2 = kernel.create_process("editor", parent_pid=0)
    print(f"   shell (PID={p1})")
    print(f"   editor (PID={p2})")

    # 演示 1: 尝试杀死 init 进程
    print(f"\n2. 尝试杀死 init 进程 (PID=0):")
    result = syscall.sys_exit(0, exit_code=0)
    if result == ErrorCode.EPERM:
        print(f"   错误: 不能杀死 init 进程 (EPERM)")
        print(f"   init 是所有进程的根，有特殊保护")
    else:
        print(f"   结果: {result}")

    # 验证 init 进程仍然存在
    init = kernel.get_process(0)
    print(f"   init 进程状态: {init.state.value if init else '不存在'}")

    # 演示 2: Fork Bomb 防护
    print(f"\n3. Fork Bomb 防护演示:")
    print(f"   最大进程数限制: {kernel._max_processes}")

    # 尝试创建超过限制的进程
    created = 0
    for i in range(15):  # 尝试创建 15 个进程
        pid = kernel.create_process(f"bomb_{i}", parent_pid=0)
        if pid is not None:
            created += 1
        else:
            print(f"   第 {i+1} 次 fork 被拒绝: 达到进程上限")
            break

    print(f"   成功创建: {created} 个进程")
    print(f"   总进程数: {len(kernel.get_all_processes())}")

    # 演示 3: 无效参数处理
    print(f"\n4. 无效参数处理:")

    # waitpid 没有子进程的进程
    dummy_pid = kernel.create_process("dummy", parent_pid=0)
    result = syscall.sys_waitpid(dummy_pid, -1)
    if result == ErrorCode.ECHILD:
        print(f"   waitpid 没有子进程的进程: ECHILD 错误")

    # 获取不存在的进程
    pcb = kernel.get_process(999)
    print(f"   获取不存在的进程 (PID=999): {pcb}")

    # 演示 4: 错误码定义
    print(f"\n5. 错误码定义:")
    print(f"   SUCCESS = {ErrorCode.SUCCESS}")
    print(f"   ECHILD  = {ErrorCode.ECHILD}  (没有子进程)")
    print(f"   EAGAIN  = {ErrorCode.EAGAIN}  (资源限制)")
    print(f"   EINVAL  = {ErrorCode.EINVAL}  (无效参数)")
    print(f"   ESRCH   = {ErrorCode.ESRCH}   (进程不存在)")
    print(f"   ENOMEM  = {ErrorCode.ENOMEM}  (内存不足)")
    print(f"   EPERM   = {ErrorCode.EPERM}   (权限不足)")

    print("\n" + "=" * 60)
    print("  演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
