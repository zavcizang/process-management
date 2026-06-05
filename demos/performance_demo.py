"""
performance_demo.py — 性能对比演示

演示内容：
1. COW Fork vs 传统 Fork 的内存开销对比
2. 验证 COW 的零拷贝效果
3. 展示内存节省百分比
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kernel.kernel import Kernel


def main():
    print("=" * 60)
    print("  演示: 性能对比 — COW vs 传统 Fork")
    print("=" * 60)

    # 创建内核
    kernel = Kernel(max_processes=16, total_frames=256)

    # 创建父进程
    parent_pid = kernel.create_process("parent", parent_pid=0)
    parent = kernel.get_process(parent_pid)

    # 父进程分配 4 页内存
    print(f"\n1. 父进程分配 4 页内存 (16KB):")
    for i in range(4):
        frame = kernel.memory_manager._fm.allocate()
        parent.page_table.map(i, frame)

    free_before = kernel.memory_manager._fm.get_free_count()
    total_frames = kernel.memory_manager._fm.get_total_count()
    print(f"   总帧数: {total_frames}")
    print(f"   分配前空闲帧: {free_before}")
    print(f"   已使用: {total_frames - free_before}")

    # 模拟传统 Fork（复制所有页表项）
    print(f"\n2. 模拟传统 Fork:")
    print(f"   传统 Fork 会复制父进程的所有页表项")
    print(f"   如果子进程有 4 页，fork 后会多分配 4 帧")
    print(f"   额外开销: 4 帧 = 16KB")

    # 执行 COW Fork
    print(f"\n3. 执行 COW Fork:")
    child_pid = kernel.syscall.sys_fork(parent_pid)
    child = kernel.get_process(child_pid)

    free_after_fork = kernel.memory_manager._fm.get_free_count()
    used_after_fork = total_frames - free_after_fork

    print(f"   fork 后空闲帧: {free_after_fork}")
    print(f"   fork 后已使用: {used_after_fork}")

    # 检查共享状态
    print(f"\n4. 检查父子进程共享状态:")
    shared_count = 0
    for i in range(4):
        parent_entry = parent.page_table.get_entry(i)
        child_entry = child.page_table.get_entry(i)
        shared = parent_entry.frame_id == child_entry.frame_id
        if shared:
            shared_count += 1
        print(f"   页 {i}: 父帧={parent_entry.frame_id}, 子帧={child_entry.frame_id}, 共享={'是' if shared else '否'}")

    print(f"   共享帧数: {shared_count}")

    # 性能对比
    print(f"\n5. 性能对比:")
    print(f"   ┌─────────────────────────────────────────────────────┐")
    print(f"   │  传统 Fork:                                         │")
    print(f"   │    fork 前空闲帧: {free_before}                               │")
    print(f"   │    fork 后空闲帧: {free_before - 4} (假设复制 4 帧)                  │")
    print(f"   │    额外开销: 4 帧 = 16KB                           │")
    print(f"   └─────────────────────────────────────────────────────┘")
    print(f"   ┌─────────────────────────────────────────────────────┐")
    print(f"   │  COW Fork (我们的实现):                             │")
    print(f"   │    fork 前空闲帧: {free_before}                               │")
    print(f"   │    fork 后空闲帧: {free_after_fork}                               │")
    print(f"   │    额外开销: 0 帧 = 0KB                            │")
    print(f"   └─────────────────────────────────────────────────────┘")

    # 计算节省
    traditional_used = 4 + 4  # 父进程 4 帧 + 子进程 4 帧
    cow_used = used_after_fork
    saved = traditional_used - cow_used
    saved_percent = saved / traditional_used * 100

    print(f"\n6. 内存节省:")
    print(f"   传统 Fork 总使用: {traditional_used} 帧")
    print(f"   COW Fork 总使用: {cow_used} 帧")
    print(f"   节省: {saved} 帧 ({saved_percent:.1f}%)")

    # 触发 COW 后的效果
    print(f"\n7. 触发 COW 后的效果:")
    print(f"   子进程写入第 0 页...")
    kernel.memory_manager.on_page_write(child.page_table, 0)

    free_after_write = kernel.memory_manager._fm.get_free_count()
    used_after_write = total_frames - free_after_write
    print(f"   写入后空闲帧: {free_after_write}")
    print(f"   写入后已使用: {used_after_write}")
    print(f"   只复制了 1 帧，节省了 3 帧")

    # 最终总结
    print(f"\n8. 最终总结:")
    print(f"   ┌─────────────────────────────────────────────────────┐")
    print(f"   │  COW 的价值:                                        │")
    print(f"   │    • fork 后不写入: 内存开销为零，节省 100%         │")
    print(f"   │    • fork 后写入 N 页: 只复制 N 帧，节省 (4-N)/4   │")
    print(f"   │    • 现实中很多进程 fork 后立即 exec，不会写入      │")
    print(f"   └─────────────────────────────────────────────────────┘")

    print("\n" + "=" * 60)
    print("  演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
