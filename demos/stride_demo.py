"""
stride_demo.py — Stride 调度公平性演示

演示内容：
1. 创建 3 个不同优先级的进程
2. 运行调度器
3. 统计每个进程的 CPU 时间
4. 验证公平性
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kernel.kernel import Kernel


def main():
    print("=" * 60)
    print("  演示: Stride 调度公平性")
    print("=" * 60)

    # 创建内核
    kernel = Kernel(max_processes=16)
    syscall = kernel.syscall

    # 创建 3 个进程，优先级不同
    print(f"\n1. 创建 3 个进程:")
    p1 = kernel.create_process("A", parent_pid=0, priority=10)   # 高优先级
    p2 = kernel.create_process("B", parent_pid=0, priority=133)  # 低优先级
    p3 = kernel.create_process("C", parent_pid=0, priority=133)  # 低优先级

    print(f"   A (PID={p1}): priority=10 (高优先级)")
    print(f"   B (PID={p2}): priority=133 (低优先级)")
    print(f"   C (PID={p3}): priority=133 (低优先级)")

    # 显示 stride 值
    sched = kernel.scheduler
    print(f"\n2. Stride 值:")
    for pid, entry in sched._registry.items():
        print(f"   PID={pid}: stride={entry['stride']:.2f}")

    # 运行 200 个 tick
    print(f"\n3. 运行 200 个时间片...")
    for _ in range(200):
        kernel.tick()

    # 统计 CPU 时间
    print(f"\n4. CPU 时间统计:")
    processes = kernel.get_all_processes()
    total_cpu = sum(p.cpu_time for p in processes.values() if p.pid != 0)

    for pid in [p1, p2, p3]:
        pcb = kernel.get_process(pid)
        if pcb:
            ratio = pcb.cpu_time / total_cpu * 100 if total_cpu > 0 else 0
            print(f"   {pcb.name} (PID={pid}): cpu_time={pcb.cpu_time:.0f}, 比例={ratio:.1f}%")

    # 验证公平性
    print(f"\n5. 公平性验证:")
    p1_ratio = kernel.get_process(p1).cpu_time / total_cpu * 100
    p2_ratio = kernel.get_process(p2).cpu_time / total_cpu * 100
    p3_ratio = kernel.get_process(p3).cpu_time / total_cpu * 100

    print(f"   期望: A ≈ 50%, B ≈ 25%, C ≈ 25%")
    print(f"   实际: A = {p1_ratio:.1f}%, B = {p2_ratio:.1f}%, C = {p3_ratio:.1f}%")

    if abs(p1_ratio - 50) < 10 and abs(p2_ratio - 25) < 10 and abs(p3_ratio - 25) < 10:
        print(f"   结论: 公平性验证通过！")
    else:
        print(f"   结论: 公平性偏差较大")

    print("\n" + "=" * 60)
    print("  演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
