"""
charts.py — Matplotlib 图表生成

提供基于 matplotlib 的可视化图表：
1. 进程调度甘特图
2. CPU 利用率折线图
3. 内存使用饼图
4. Stride 调度公平性柱状图
5. 上下文切换时间线

使用：
    from visualizer.charts import ChartGenerator

    chart = ChartGenerator(output_dir='output')
    chart.plot_gantt(kernel)
    chart.plot_cpu_utilization(kernel)
    chart.plot_memory_usage(kernel)
    chart.plot_stride_fairness(processes)
    chart.plot_context_switches(kernel)
"""

import os
from typing import Dict, List, Optional, Tuple

try:
    import matplotlib
    matplotlib.use('Agg')  # 非交互式后端，适合生成图片
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib import rcParams
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

from core.pcb import PCB, ProcessState


# 中文字体配置
if HAS_MATPLOTLIB:
    rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
    rcParams['axes.unicode_minus'] = False


# 进程颜色映射
PROCESS_COLORS = {
    0: '#95a5a6',   # init - 灰色
    1: '#3498db',   # 第一个用户进程 - 蓝色
    2: '#e74c3c',   # 第二个 - 红色
    3: '#2ecc71',   # 第三个 - 绿色
    4: '#f39c12',   # 第四个 - 橙色
    5: '#9b59b6',   # 第五个 - 紫色
    6: '#1abc9c',   # 第六个 - 青色
    7: '#e67e22',   # 第七个 - 深橙色
}


class ChartGenerator:
    """
    Matplotlib 图表生成器

    使用示例：
        chart = ChartGenerator(output_dir='output')
        chart.plot_gantt(kernel)
        chart.show()  # 或自动保存到 output/
    """

    def __init__(self, output_dir: str = 'output'):
        """
        Args:
            output_dir: 图表输出目录
        """
        self._output_dir = output_dir
        if HAS_MATPLOTLIB and not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def _get_color(self, pid: int) -> str:
        """获取进程对应的颜色"""
        return PROCESS_COLORS.get(pid % 8, '#bdc3c7')

    def plot_gantt(self, kernel, filename: str = 'gantt.png') -> Optional[str]:
        """
        生成进程调度甘特图。

        Args:
            kernel: 内核实例
            filename: 输出文件名

        Returns:
            图表文件路径，matplotlib 未安装返回 None
        """
        if not HAS_MATPLOTLIB:
            print("[提示] 未安装 matplotlib，跳过图表生成")
            return None

        processes = kernel.get_all_processes()

        # 构建调度历史
        tick_count = kernel._tick_count
        if tick_count == 0:
            print("[提示] 无调度历史，跳过甘特图")
            return None

        # 创建图表
        fig, ax = plt.subplots(figsize=(14, 4))

        # 收集所有用户进程（排除 init）
        user_pids = [pid for pid in processes.keys() if pid != 0]
        y_positions = {pid: i for i, pid in enumerate(sorted(user_pids))}

        # 绘制甘特条
        for pid, y_pos in y_positions.items():
            pcb = processes[pid]
            color = self._get_color(pid)

            # 简化：基于 CPU 时间估算执行段
            if pcb.cpu_time > 0:
                # 均匀分布在时间轴上
                segment_length = tick_count / max(pcb.cpu_time, 1)
                current_pos = 0
                for _ in range(int(pcb.cpu_time)):
                    ax.barh(y_pos, 1, left=current_pos, height=0.6,
                           color=color, edgecolor='white', linewidth=0.5)
                    current_pos += segment_length

        # 设置坐标轴
        ax.set_yticks(range(len(user_pids)))
        ax.set_yticklabels([f"P{pid} ({processes[pid].name})" for pid in sorted(user_pids)])
        ax.set_xlabel('时间 (Tick)')
        ax.set_title('进程调度甘特图', fontsize=14, fontweight='bold')
        ax.set_xlim(0, tick_count)
        ax.grid(axis='x', alpha=0.3)

        # 图例
        legend_patches = [mpatches.Patch(color=self._get_color(pid), label=f"P{pid}")
                         for pid in sorted(user_pids)]
        ax.legend(handles=legend_patches, loc='upper right', ncol=len(user_pids))

        plt.tight_layout()
        output_path = os.path.join(self._output_dir, filename)
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"[图表] 甘特图已保存: {output_path}")
        return output_path

    def plot_cpu_utilization(self, kernel, filename: str = 'cpu_util.png') -> Optional[str]:
        """
        生成 CPU 利用率折线图。

        Args:
            kernel: 内核实例
            filename: 输出文件名

        Returns:
            图表文件路径
        """
        if not HAS_MATPLOTLIB:
            print("[提示] 未安装 matplotlib，跳过图表生成")
            return None

        tick_count = kernel._tick_count
        if tick_count == 0:
            print("[提示] 无调度历史，跳过 CPU 利用率图")
            return None

        processes = kernel.get_all_processes()

        # 创建图表
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), height_ratios=[2, 1])

        # 上图：各进程 CPU 时间随时间变化
        ticks = list(range(tick_count + 1))
        for pid in sorted(processes.keys()):
            if pid == 0:
                continue
            pcb = processes[pid]
            # 模拟 CPU 时间增长（简化）
            cpu_times = [min(pcb.cpu_time * t / tick_count, pcb.cpu_time)
                        for t in ticks]
            ax1.plot(ticks, cpu_times, label=f"P{pid} ({pcb.name})",
                    linewidth=2, marker='o', markersize=3)

        ax1.set_xlabel('时间 (Tick)')
        ax1.set_ylabel('CPU 时间')
        ax1.set_title('各进程 CPU 时间变化', fontsize=14, fontweight='bold')
        ax1.legend()
        ax1.grid(alpha=0.3)

        # 下图：CPU 利用率
        total_cpu_time = sum(p.cpu_time for p in processes.values() if p.pid != 0)
        utilization = [min(total_cpu_time * t / tick_count / max(t, 1) * 100, 100)
                      for t in ticks]

        ax2.fill_between(ticks, utilization, alpha=0.3, color='#3498db')
        ax2.plot(ticks, utilization, color='#2980b9', linewidth=2)
        ax2.set_xlabel('时间 (Tick)')
        ax2.set_ylabel('利用率 (%)')
        ax2.set_title('CPU 利用率', fontsize=14, fontweight='bold')
        ax2.set_ylim(0, 110)
        ax2.grid(alpha=0.3)

        plt.tight_layout()
        output_path = os.path.join(self._output_dir, filename)
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"[图表] CPU 利用率图已保存: {output_path}")
        return output_path

    def plot_memory_usage(self, kernel, filename: str = 'memory.png') -> Optional[str]:
        """
        生成内存使用饼图。

        Args:
            kernel: 内核实例
            filename: 输出文件名

        Returns:
            图表文件路径
        """
        if not HAS_MATPLOTLIB:
            print("[提示] 未安装 matplotlib，跳过图表生成")
            return None

        stats = kernel.memory_manager._fm.get_stats()

        # 创建图表
        fig, ax = plt.subplots(figsize=(8, 6))

        # 饼图数据
        used = stats['used_frames']
        free = stats['free_frames']
        shared = stats['shared_frames']

        sizes = [used - shared, shared, free]
        labels = [f'独占帧 ({used - shared})', f'共享帧/COW ({shared})', f'空闲帧 ({free})']
        colors = ['#3498db', '#e74c3c', '#ecf0f1']
        explode = (0, 0.1, 0)

        wedges, texts, autotexts = ax.pie(
            sizes, explode=explode, labels=labels, colors=colors,
            autopct='%1.1f%%', shadow=True, startangle=90,
            textprops={'fontsize': 11}
        )

        # 设置百分比文字颜色
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')

        ax.set_title(f'内存帧使用情况 (共 {stats["total_frames"]} 帧)',
                    fontsize=14, fontweight='bold')

        plt.tight_layout()
        output_path = os.path.join(self._output_dir, filename)
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"[图表] 内存使用图已保存: {output_path}")
        return output_path

    def plot_stride_fairness(self, processes: Dict[int, PCB],
                             filename: str = 'stride_fairness.png') -> Optional[str]:
        """
        生成 Stride 调度公平性柱状图。

        Args:
            processes: 进程字典
            filename: 输出文件名

        Returns:
            图表文件路径
        """
        if not HAS_MATPLOTLIB:
            print("[提示] 未安装 matplotlib，跳过图表生成")
            return None

        # 排除 init 进程
        user_processes = {pid: pcb for pid, pcb in processes.items() if pid != 0}
        if not user_processes:
            print("[提示] 无用户进程，跳过公平性图")
            return None

        # 创建图表
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        # 左图：CPU 时间柱状图
        pids = sorted(user_processes.keys())
        cpu_times = [user_processes[pid].cpu_time for pid in pids]
        colors = [self._get_color(pid) for pid in pids]

        bars = ax1.bar([f"P{pid}" for pid in pids], cpu_times, color=colors,
                      edgecolor='white', linewidth=2)

        # 在柱子上显示数值
        for bar, cpu_time in zip(bars, cpu_times):
            ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                    f'{cpu_time:.1f}', ha='center', va='bottom', fontweight='bold')

        ax1.set_xlabel('进程')
        ax1.set_ylabel('CPU 时间')
        ax1.set_title('各进程 CPU 时间', fontsize=14, fontweight='bold')
        ax1.grid(axis='y', alpha=0.3)

        # 右图：CPU 比例饼图
        total = sum(cpu_times)
        if total > 0:
            ratios = [cpu / total * 100 for cpu in cpu_times]
            labels = [f'P{pid} ({ratio:.1f}%)' for pid, ratio in zip(pids, ratios)]

            ax2.pie(ratios, labels=labels, colors=colors,
                   autopct='', startangle=90, textprops={'fontsize': 11})
            ax2.set_title(f'CPU 时间比例 (总计: {total:.1f})',
                         fontsize=14, fontweight='bold')

        plt.tight_layout()
        output_path = os.path.join(self._output_dir, filename)
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"[图表] Stride 公平性图已保存: {output_path}")
        return output_path

    def plot_context_switches(self, kernel, filename: str = 'context_switches.png') -> Optional[str]:
        """
        生成上下文切换时间线图。

        Args:
            kernel: 内核实例
            filename: 输出文件名

        Returns:
            图表文件路径
        """
        if not HAS_MATPLOTLIB:
            print("[提示] 未安装 matplotlib，跳过图表生成")
            return None

        history = kernel.get_context_switch_history()
        if not history:
            print("[提示] 无上下文切换历史，跳过")
            return None

        processes = kernel.get_all_processes()

        # 创建图表
        fig, ax = plt.subplots(figsize=(14, 4))

        # 绘制上下文切换事件
        for i, (tick, old_pid, new_pid) in enumerate(history):
            color = self._get_color(new_pid)
            ax.scatter(tick, 0, color=color, s=100, zorder=5, edgecolors='black')

            # 标注进程名
            if i < 20:  # 只标注前 20 个
                name = processes[new_pid].name if new_pid in processes else "?"
                ax.annotate(f'{name}({new_pid})', (tick, 0),
                          textcoords="offset points", xytext=(0, 15),
                          ha='center', fontsize=8, fontweight='bold')

        ax.set_xlabel('时间 (Tick)')
        ax.set_yticks([])
        ax.set_title(f'上下文切换时间线 (共 {len(history)} 次切换)',
                    fontsize=14, fontweight='bold')
        ax.grid(axis='x', alpha=0.3)

        # 图例
        unique_pids = set(new_pid for _, _, new_pid in history)
        legend_patches = [mpatches.Patch(color=self._get_color(pid),
                                         label=f"P{pid} ({processes[pid].name if pid in processes else '?'})")
                         for pid in sorted(unique_pids)]
        ax.legend(handles=legend_patches, loc='upper right', ncol=min(len(legend_patches), 4))

        plt.tight_layout()
        output_path = os.path.join(self._output_dir, filename)
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"[图表] 上下文切换图已保存: {output_path}")
        return output_path

    def plot_all(self, kernel) -> List[str]:
        """
        生成所有图表。

        Args:
            kernel: 内核实例

        Returns:
            生成的图表文件路径列表
        """
        paths = []

        # 运行一些 tick 让统计数据更丰富
        for _ in range(20):
            kernel.tick()

        path = self.plot_gantt(kernel)
        if path:
            paths.append(path)

        path = self.plot_cpu_utilization(kernel)
        if path:
            paths.append(path)

        path = self.plot_memory_usage(kernel)
        if path:
            paths.append(path)

        path = self.plot_stride_fairness(kernel.get_all_processes())
        if path:
            paths.append(path)

        path = self.plot_context_switches(kernel)
        if path:
            paths.append(path)

        print(f"\n共生成 {len(paths)} 个图表，保存在 {self._output_dir}/ 目录")
        return paths
