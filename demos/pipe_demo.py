"""
pipe_demo.py — StrideCOWScheduler 管道通信演示

项目: StrideCOWScheduler — 进程管理内核模拟器
作者: zavci (zjh3432512933)
仓库: https://gitee.com/zjh3432512933/process-management

演示内容：
1. 创建管道
2. fork 子进程
3. 父进程写入数据
4. 子进程读取数据
5. 展示内核日志
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kernel.kernel import Kernel
from core.pcb import ProcessState


def main():
    print("=" * 60)
    print("  演示: 管道通信 (IPC)")
    print("=" * 60)

    # 创建内核
    kernel = Kernel(max_processes=16, total_frames=16, enable_logging=True)
    syscall = kernel.syscall

    # 创建父进程
    parent_pid = kernel.create_process("parent", parent_pid=0)
    kernel.tick()

    print(f"\n1. 创建管道...")
    read_fd, write_fd = kernel.ipc_manager.create_pipe(parent_pid)
    print(f"   管道已创建: read_fd={read_fd}, write_fd={write_fd}")

    # fork 子进程
    print(f"\n2. fork 子进程...")
    child_pid = syscall.sys_fork(parent_pid)
    child = kernel.get_process(child_pid)
    print(f"   子进程已创建: PID={child_pid}")

    # 让子进程运行
    kernel.tick()

    # 父进程写入数据
    print(f"\n3. 父进程写入管道...")
    messages = ["Hello from parent", "IPC is working!", "OS competition"]

    for msg in messages:
        data = msg.encode('utf-8')
        bytes_written = kernel.ipc_manager.write(write_fd, data)
        print(f"   写入: '{msg}' ({bytes_written} 字节)")

    # 子进程读取数据
    print(f"\n4. 子进程读取管道...")
    for i in range(len(messages)):
        data = kernel.ipc_manager.read(read_fd, 1024)
        if data:
            print(f"   读取: '{data.decode('utf-8')}'")

    # 显示管道状态
    print(f"\n5. 管道状态:")
    pipe_info = kernel.ipc_manager.get_pipe_info(0)
    if pipe_info:
        print(f"   管道 ID: {pipe_info['pipe_id']}")
        print(f"   缓冲区大小: {pipe_info['buffer_size']}")
        print(f"   当前数据量: {pipe_info['size']}")
        print(f"   已关闭: {pipe_info['closed']}")

    # 显示文件描述符
    print(f"\n6. 进程文件描述符:")
    for pid in [parent_pid, child_pid]:
        fds = kernel.ipc_manager.get_process_fds(pid)
        pcb = kernel.get_process(pid)
        if pcb:
            print(f"   {pcb.name} (PID={pid}): {len(fds)} 个文件描述符")
            for fd, info in fds.items():
                mode_str = "读" if info['mode'] == 'r' else "写"
                print(f"     fd={fd}: {mode_str}端 (管道{info['pipe_id']})")

    # 显示内核日志
    print(f"\n7. 内核日志 (dmesg):")
    print(kernel.dmesg())

    print("=" * 60)
    print("  演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
