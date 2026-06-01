"""
pcb.py — 进程控制块（Process Control Block）

PCB 是操作系统中最核心的数据结构，代表一个进程的全部信息。
本模块定义了 PCB 类，包含进程的所有属性和状态管理方法。

设计原则：
- 使用 dataclass 简化定义，自动生成 __init__、__repr__ 等方法
- 状态转换通过 set_state() 方法统一管理，确保转换合法
- reset() 方法支持模拟器重置（用于比较不同调度算法）
"""

from dataclasses import dataclass, field
from typing import List, Optional


class ProcessState:
    """进程状态常量"""
    NEW = "NEW"              # 刚创建，尚未加入调度队列
    READY = "READY"          # 就绪，等待 CPU 调度
    RUNNING = "RUNNING"      # 正在 CPU 上执行
    SLEEPING = "SLEEPING"    # 阻塞等待（如 waitpid）
    ZOMBIE = "ZOMBIE"        # 已退出，等待父进程回收
    TERMINATED = "TERMINATED"  # 彻底销毁

    # 合法的状态转换路径
    VALID_TRANSITIONS = {
        NEW: {READY},
        READY: {RUNNING, SLEEPING, TERMINATED},
        RUNNING: {READY, SLEEPING, ZOMBIE, TERMINATED},
        SLEEPING: {READY, TERMINATED},
        ZOMBIE: {TERMINATED},
        TERMINATED: set(),
    }

    @classmethod
    def is_valid_transition(cls, from_state: str, to_state: str) -> bool:
        """检查状态转换是否合法"""
        allowed = cls.VALID_TRANSITIONS.get(from_state, set())
        return to_state in allowed


# ============================================================
# 进程控制块
# ============================================================
@dataclass
class PCB:
    """
    进程控制块（Process Control Block）

    存储一个进程的所有信息，包括：
    - 身份标识（pid, ppid, name）
    - 进程状态（state）
    - 调度参数（priority, stride, pass_value, nice）
    - 时间统计（cpu_time, wait_time, arrival_time 等）
    - 内存信息（page_table, memory_usage）
    - 进程树关系（children, exit_code, wait_queue）
    """

    # ── 身份标识 ──────────────────────────────────────────────
    pid: int                           # 进程 ID（全局唯一）
    ppid: int                          # 父进程 ID（init 进程 ppid = -1）
    name: str                          # 进程名（如 "shell", "editor"）
    state: str = ProcessState.NEW      # 进程状态

    # ── 调度相关 ──────────────────────────────────────────────
    priority: int = 128                # 静态优先级 (0-255，越小越高)
    stride: float = 0.0               # 步长 = BIG_STRIDE / priority
    pass_value: float = 0.0           # 累计步长（Stride 调度决策依据）
    nice: int = 0                      # nice 值 (-20 ~ 19)

    # ── 时间统计 ──────────────────────────────────────────────
    arrival_time: float = 0.0          # 进程创建时间
    start_time: float = -1.0           # 首次被调度运行的时间（-1 表示未运行过）
    cpu_time: float = 0.0             # 累计 CPU 执行时间
    wait_time: float = 0.0            # 累计等待时间
    burst_time: float = 0.0           # 本次连续执行的时间片数

    # ── COW 内存 ─────────────────────────────────────────────
    page_table: Optional[object] = None  # PageTable 实例（由 B 实现）
    memory_usage: int = 0              # 实际物理内存占用（字节）

    # ── 进程树 ────────────────────────────────────────────────
    children: List[int] = field(default_factory=list)  # 子进程 PID 列表
    exit_code: int = 0                 # 退出码（exit 时设置）
    wait_queue: List[int] = field(default_factory=list)  # 等待此进程的父进程 PID 列表

    # ── 统计信息 ──────────────────────────────────────────────
    page_faults: int = 0               # 缺页次数
    cow_copies: int = 0                # COW 触发次数
    context_switches: int = 0          # 上下文切换次数

    # ── 进程限制 ──────────────────────────────────────────────
    max_children: int = 64             # 最大子进程数（fork bomb 防护）

    def set_state(self, new_state: str) -> bool:
        """
        设置进程状态，自动检查转换是否合法。

        Args:
            new_state: 目标状态

        Returns:
            True 转换成功，False 转换非法（状态不变）

        示例：
            pcb.set_state(ProcessState.READY)   # NEW → READY，成功
            pcb.set_state(ProcessState.RUNNING)  # NEW → RUNNING，失败
        """
        if not ProcessState.is_valid_transition(self.state, new_state):
            return False
        self.state = new_state
        return True

    def reset(self) -> None:
        """
        重置为初始状态（用于重新运行模拟）。

        保留 pid、ppid、name、arrival_time、priority、nice、burst_time
        重置其他所有字段为默认值。
        """
        self.state = ProcessState.NEW
        self.stride = 0.0
        self.pass_value = 0.0
        self.start_time = -1.0
        self.cpu_time = 0.0
        self.wait_time = 0.0
        self.burst_time = 0.0
        self.page_table = None
        self.memory_usage = 0
        self.children = []
        self.exit_code = 0
        self.wait_queue = []
        self.page_faults = 0
        self.cow_copies = 0
        self.context_switches = 0

    def to_dict(self) -> dict:
        """转换为字典（用于序列化和调试输出）"""
        return {
            'pid': self.pid,
            'ppid': self.ppid,
            'name': self.name,
            'state': self.state,
            'priority': self.priority,
            'stride': round(self.stride, 2),
            'pass_value': round(self.pass_value, 2),
            'nice': self.nice,
            'cpu_time': self.cpu_time,
            'wait_time': self.wait_time,
            'arrival_time': self.arrival_time,
            'start_time': self.start_time,
            'children': self.children[:],
            'exit_code': self.exit_code,
            'wait_queue': self.wait_queue[:],
            'memory_usage': self.memory_usage,
            'page_faults': self.page_faults,
            'cow_copies': self.cow_copies,
            'context_switches': self.context_switches,
        }

    def __repr__(self) -> str:
        return (
            f"PCB(pid={self.pid}, ppid={self.ppid}, name='{self.name}', "
            f"state={self.state}, priority={self.priority})"
        )
