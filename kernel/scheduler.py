"""
scheduler.py — StrideCOWScheduler Stride 公平调度算法

项目: StrideCOWScheduler — 进程管理内核模拟器
作者: zavci (zjh3432512933)
仓库: https://gitee.com/zjh3432512933/process-management

Stride 调度是 Linux CFS（完全公平调度器）的数学基础。

核心思想：
- 每个进程有一个 stride（步长）= BIG_STRIDE / priority
- 每次调度选 pass_value 最小的进程运行
- 运行一次后 pass_value += stride

数学证明：
  对于进程 A(priority=10) 和 B(priority=5)：
  stride_A = 1000/10 = 100, stride_B = 1000/5 = 200
  经过 3 次调度后：pass_A = 300, pass_B = 400
  CPU 时间比 = 1/stride_A : 1/stride_B = 1/100 : 1/200 = 2:1
  优先级高的进程获得 2 倍 CPU 时间

特性：
1. 严格公平：优先级高的进程获得更多CPU时间，比例精确可控
2. 无饥饿：所有进程最终都会被调度
3. O(log n) 调度：使用最小堆
4. 优先级动态调整：基于进程行为（I/O密集 vs CPU密集）
"""

import heapq
from typing import Dict, List, Optional, Tuple


# 大常数，用于计算步长
BIG_STRIDE = 1_000_000


class StrideScheduler:
    """
    Stride 公平调度器

    使用最小堆维护就绪队列，每次选出 pass_value 最小的进程运行。

    使用示例：
        sched = StrideScheduler()
        sched.register(1, priority=10)
        sched.register(2, priority=5)
        sched.enqueue(1)
        sched.enqueue(2)

        pid = sched.dequeue()   # 返回 pass_value 最小的进程
        sched.update_after_run(pid, 1)  # 运行 1 个 tick
        sched.enqueue(pid)      # 重新入队
    """

    def __init__(self):
        # 最小堆：(pass_value, pid)
        # heapq 自动按 pass_value 排序，最小的在堆顶
        self._heap: List[Tuple[float, int]] = []

        # 进程注册表：{pid: {'priority': int, 'stride': float, 'pass_value': float}}
        self._registry: Dict[int, dict] = {}

        # 当前正在运行的进程 PID
        self._running_pid: Optional[int] = None

        # 调度统计
        self._total_ticks = 0
        self._schedule_count = 0

    def register(self, pid: int, priority: int = 128) -> None:
        """
        注册进程到调度器（创建进程时调用）。

        Args:
            pid: 进程 PID
            priority: 优先级 (0-255，越小越高)

        Stride 计算：
            stride = BIG_STRIDE / (256 - priority)
            - priority=0（最高）→ stride = BIG/256 ≈ 3906（最小步长，最多CPU）
            - priority=128（默认）→ stride = BIG/128 ≈ 7812
            - priority=255（最低）→ stride = BIG/1 = 1000000（最大步长，最少CPU）
        """
        # 限制优先级范围
        priority = max(0, min(255, priority))
        # 使用 256-priority 使得优先级越高（数值越小）stride 越小
        stride = BIG_STRIDE / max(256 - priority, 1)

        self._registry[pid] = {
            'priority': priority,
            'stride': stride,
            'pass_value': 0.0,
            'cpu_time': 0,
        }

    def unregister(self, pid: int) -> None:
        """
        从调度器中注销进程（进程退出时调用）。

        Args:
            pid: 进程 PID
        """
        if pid in self._registry:
            del self._registry[pid]

        if self._running_pid == pid:
            self._running_pid = None

    def enqueue(self, pid: int) -> None:
        """
        将进程加入就绪队列。

        Args:
            pid: 进程 PID

        Raises:
            ValueError: 如果进程未注册
        """
        if pid not in self._registry:
            raise ValueError(f"进程 PID={pid} 未注册到调度器")

        pass_value = self._registry[pid]['pass_value']
        heapq.heappush(self._heap, (pass_value, pid))

    def dequeue(self) -> Optional[int]:
        """
        从就绪队列中取出下一个要运行的进程。

        选择 pass_value 最小的进程（最"饥饿"的进程）。

        Returns:
            进程 PID，队列为空返回 None
        """
        # 跳过已注销的进程
        while self._heap:
            pass_value, pid = heapq.heappop(self._heap)
            if pid in self._registry:
                self._running_pid = pid
                self._schedule_count += 1
                return pid

        return None

    def remove(self, pid: int) -> None:
        """
        从就绪队列中移除指定进程（延迟删除）。

        由于堆不支持高效删除，这里采用延迟删除策略：
        只在 dequeue 时跳过已注销的进程。

        Args:
            pid: 进程 PID
        """
        # 标记为已注销（dequeue 时会跳过）
        if pid in self._registry:
            del self._registry[pid]

        if self._running_pid == pid:
            self._running_pid = None

    def update_after_run(self, pid: int, ticks: int = 1) -> None:
        """
        进程运行指定 tick 数后更新调度状态。

        核心操作：pass_value += stride

        Args:
            pid: 进程 PID
            ticks: 运行的 tick 数
        """
        if pid not in self._registry:
            return

        entry = self._registry[pid]
        entry['pass_value'] += entry['stride'] * ticks
        entry['cpu_time'] += ticks
        self._total_ticks += ticks

        # 溢出处理：当 pass_value 过大时，减去最小值保持相对差值
        self._handle_overflow()

    def _handle_overflow(self) -> None:
        """
        溢出处理：当 pass_value 接近溢出时，重置所有进程的 pass_value。

        策略：减去所有进程中最小的 pass_value，保持相对差值不变。
        """
        if not self._registry:
            return

        min_pass = min(e['pass_value'] for e in self._registry.values())

        if min_pass > BIG_STRIDE * 100:
            for entry in self._registry.values():
                entry['pass_value'] -= min_pass

            # 重建堆
            self._heap = [
                (entry['pass_value'], pid)
                for pid, entry in self._registry.items()
            ]
            heapq.heapify(self._heap)

    def set_priority(self, pid: int, priority: int) -> None:
        """
        设置进程优先级（同时更新 stride）。

        Args:
            pid: 进程 PID
            priority: 新优先级 (0-255，越小越高)
        """
        if pid not in self._registry:
            return

        priority = max(0, min(255, priority))
        entry = self._registry[pid]
        entry['priority'] = priority
        entry['stride'] = BIG_STRIDE / max(256 - priority, 1)

    def get_queue_snapshot(self) -> List[Tuple[int, float]]:
        """
        获取就绪队列快照。

        Returns:
            [(pid, pass_value), ...] 列表，按 pass_value 排序
        """
        # 合并堆中和已注册但不在堆中的进程
        snapshot = []
        for pid, entry in self._registry.items():
            snapshot.append((pid, entry['pass_value']))
        snapshot.sort(key=lambda x: x[1])
        return snapshot

    def get_running_pid(self) -> Optional[int]:
        """获取当前正在运行的进程 PID"""
        return self._running_pid

    def get_stats(self) -> dict:
        """获取调度统计信息"""
        return {
            'total_ticks': self._total_ticks,
            'schedule_count': self._schedule_count,
            'registered_count': len(self._registry),
            'queue_size': len(self._heap),
        }

    def __repr__(self) -> str:
        return f"StrideScheduler(processes={len(self._registry)}, ticks={self._total_ticks})"
