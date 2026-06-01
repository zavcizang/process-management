"""
cow_demo.py — COW 写时复制演示

演示内容：
1. 创建父进程并分配内存页
2. fork 子进程（零拷贝）
3. 子进程写入页面（触发 COW）
4. 展示内存节省效果
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kernel.kernel import Kernel
from kernel.memory_manager import PageTable


def main():
    print("=" * 60)
    print("  演示: COW 写时复制")
    print("=" * 60)

    # 创建内核
    kernel = Kernel(max_processes=16, total_frames=16)
    syscall = kernel.syscall

    # 创建父进程
    parent_pid = kernel.create_process("parent", parent_pid=0)
    parent = kernel.get_process(parent_pid)

    # 父进程分配 4 页内存
    print(f"\n1. 父进程分配 4 页内存 (16KB)")
    for i in range(4):
        frame = kernel.memory_manager._fm.allocate()
        parent.page_table.map(i, frame)

    free_before = kernel.memory_manager._fm.get_free_count()
    print(f"   分配前空闲帧: {free_before}")

    # fork 子进程
    print(f"\n2. 执行 fork...")
    child_pid = syscall.sys_fork(parent_pid)
    child = kernel.get_process(child_pid)

    free_after_fork = kernel.memory_manager._fm.get_free_count()
    print(f"   fork 后空闲帧: {free_after_fork}")
    print(f"   COW 效果: 零拷贝！没有分配新帧")

    # 检查共享状态
    print(f"\n3. 检查父子进程共享状态:")
    for i in range(4):
        parent_entry = parent.page_table.get_entry(i)
        child_entry = child.page_table.get_entry(i)
        shared = parent_entry.frame_id == child_entry.frame_id
        print(f"   页 {i}: 帧号={parent_entry.frame_id}, 共享={'是' if shared else '否'}")

    # 子进程写入第 0 页
    print(f"\n4. 子进程写入第 0 页...")
    triggered = kernel.memory_manager.on_page_write(child.page_table, 0)
    print(f"   COW 触发: {triggered}")

    free_after_write = kernel.memory_manager._fm.get_free_count()
    print(f"   写入后空闲帧: {free_after_write}")
    print(f"   只复制了 1 页，节省了 3 页内存")

    # 再次检查共享状态
    print(f"\n5. 写入后共享状态:")
    for i in range(4):
        parent_entry = parent.page_table.get_entry(i)
        child_entry = child.page_table.get_entry(i)
        shared = parent_entry.frame_id == child_entry.frame_id
        print(f"   页 {i}: 父帧={parent_entry.frame_id}, 子帧={child_entry.frame_id}, 共享={'是' if shared else '否'}")

    # 统计
    print(f"\n6. 内存统计:")
    total_frames = kernel.memory_manager._fm.get_total_count()
    used_frames = total_frames - kernel.memory_manager._fm.get_free_count()
    print(f"   总帧数: {total_frames}")
    print(f"   已使用: {used_frames}")
    print(f"   空闲: {kernel.memory_manager._fm.get_free_count()}")

    # 对比完全复制
    print(f"\n7. 对比完全复制:")
    print(f"   完全复制: 需要 8 帧 (父4 + 子4)")
    print(f"   COW:      只用了 {used_frames} 帧")
    print(f"   节省: {8 - used_frames} 帧 ({(8 - used_frames) / 8 * 100:.1f}%)")

    print("\n" + "=" * 60)
    print("  演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
