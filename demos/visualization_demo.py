"""
visualization_demo.py — 可视化图表演示

演示内容：
1. 创建进程并运行 Stride 调度
2. 生成 Stride 公平性柱状图
3. 生成内存映射图
4. 展示图表功能
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kernel.kernel import Kernel


def main():
    print("=" * 60)
    print("  演示: 可视化图表展示")
    print("=" * 60)

    # 创建内核
    kernel = Kernel(max_processes=16, total_frames=256)

    # 创建 3 个进程，优先级不同
    print(f"\n1. 创建 3 个进程:")
    p1 = kernel.create_process("A", parent_pid=0, priority=10)   # 高优先级
    p2 = kernel.create_process("B", parent_pid=0, priority=133)  # 低优先级
    p3 = kernel.create_process("C", parent_pid=0, priority=133)  # 低优先级

    print(f"   A (PID={p1}): priority=10 (高优先级)")
    print(f"   B (PID={p2}): priority=133 (低优先级)")
    print(f"   C (PID={p3}): priority=133 (低优先级)")

    # 运行 200 个 tick
    print(f"\n2. 运行 200 个时间片...")
    for _ in range(200):
        kernel.tick()

    # 统计 CPU 时间
    print(f"\n3. CPU 时间统计:")
    processes = kernel.get_all_processes()
    total_cpu = sum(p.cpu_time for p in processes.values() if p.pid != 0)

    for pid in [p1, p2, p3]:
        pcb = kernel.get_process(pid)
        if pcb:
            ratio = pcb.cpu_time / total_cpu * 100 if total_cpu > 0 else 0
            print(f"   {pcb.name} (PID={pid}): cpu_time={pcb.cpu_time:.0f}, 比例={ratio:.1f}%")

    # 生成图表
    print(f"\n4. 生成可视化图表:")
    try:
        from visualizer.charts import ChartGenerator
        chart = ChartGenerator(output_dir='output')

        print(f"   生成 Stride 公平性柱状图...")
        chart.plot_stride_fairness(processes)
        print(f"   [图表] Stride 公平性图已保存: output/stride_fairness.png")

        print(f"   生成内存映射图...")
        chart.plot_memory_mapping(kernel)
        print(f"   [图表] 内存映射图已保存: output/memory_mapping.png")

        print(f"   生成所有图表...")
        chart.plot_all(kernel)
        print(f"   [图表] 所有图表已保存到 output/ 目录")

    except ImportError:
        print(f"   [警告] matplotlib 未安装，无法生成图表")
        print(f"   请运行: pip install matplotlib numpy")

    print("\n" + "=" * 60)
    print("  演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
