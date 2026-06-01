"""
interfaces.py — 项目接口定义（所有人的"宪法"）

规则：
1. 所有模块必须实现或调用这些接口
2. 接口只能由架构师修改
3. 修改接口前必须通知全员
4. 所有接口都有对应的测试用例

本文件使用 Python Protocol 定义接口，IDE 可以据此提供类型提示。
"""

from typing import Protocol, Dict, List, Optional, Tuple, Union


# ============================================================
# 进程状态枚举
# ============================================================
class ProcessState:
    """进程状态常量（不使用 Enum，简化序列化）"""
    NEW = "NEW"              # 刚创建，尚未加入调度队列
    READY = "READY"          # 就绪，等待 CPU 调度
    RUNNING = "RUNNING"      # 正在 CPU 上执行
    SLEEPING = "SLEEPING"    # 阻塞等待（如 waitpid 等子进程退出）
    ZOMBIE = "ZOMBIE"        # 已退出，等待父进程回收 exit_code
    TERMINATED = "TERMINATED"  # 彻底销毁，资源已释放

    # 合法状态集合（用于验证）
    ALL_STATES = {NEW, READY, RUNNING, SLEEPING, ZOMBIE, TERMINATED}

    # 合法的状态转换路径
    VALID_TRANSITIONS = {
        NEW: {READY},                        # NEW → READY（加入调度队列）
        READY: {RUNNING, SLEEPING, TERMINATED},  # 被调度运行 / 被 kill
        RUNNING: {READY, SLEEPING, ZOMBIE, TERMINATED},  # 时间片用完 / exit / kill
        SLEEPING: {READY, TERMINATED},       # 被唤醒 / 被 kill
        ZOMBIE: {TERMINATED},                # 被父进程 waitpid 回收
        TERMINATED: set(),                   # 终态，不可转换
    }

    @classmethod
    def is_valid_transition(cls, from_state: str, to_state: str) -> bool:
        """检查状态转换是否合法"""
        if from_state not in cls.ALL_STATES:
            return False
        if to_state not in cls.ALL_STATES:
            return False
        return to_state in cls.VALID_TRANSITIONS.get(from_state, set())


# ============================================================
# PCB 接口
# ============================================================
class PCBInterface(Protocol):
    """进程控制块接口"""

    # 身份标识
    pid: int               # 进程 ID（全局唯一）
    ppid: int              # 父进程 ID
    name: str              # 进程名（如 "shell", "editor"）
    state: str             # 进程状态（ProcessState 中的值）

    # 调度相关
    priority: int          # 静态优先级 (0-255，越小越高)
    stride: float          # 步长 = BIG_STRIDE / priority
    pass_value: float      # 累计步长（Stride 调度决策依据）
    nice: int              # nice 值 (-20 ~ 19)

    # 时间统计
    cpu_time: float        # 累计 CPU 执行时间
    wait_time: float       # 累计等待时间（在就绪队列中的时间）
    arrival_time: float    # 进程创建时间
    start_time: float      # 首次被调度运行的时间（-1 表示未运行过）
    burst_time: float      # 本次连续执行的时间片数

    # COW 内存
    page_table: object     # PageTable 实例（由 B 实现）
    memory_usage: int      # 实际物理内存占用（字节）

    # 进程树
    children: List[int]    # 子进程 PID 列表
    exit_code: int         # 退出码（exit 时设置）
    wait_queue: List[int]  # 等待此进程退出的父进程 PID 列表

    # 统计信息
    page_faults: int       # 缺页次数
    cow_copies: int        # COW 触发次数
    context_switches: int  # 上下文切换次数

    def reset(self) -> None: ...
    """重置为初始状态（用于重新运行模拟）"""


# ============================================================
# 进程树接口（A 实现）
# ============================================================
class ProcessTreeInterface(Protocol):
    """进程树管理接口"""

    def add_process(self, pid: int, ppid: int) -> None: ...
    """添加进程节点到树中"""

    def remove_process(self, pid: int) -> None: ...
    """从树中移除进程节点"""

    def get_children(self, pid: int) -> List[int]: ...
    """获取指定进程的直接子进程列表"""

    def reparent_orphans(self, dead_pid: int, new_parent: int) -> List[int]: ...
    """将 dead_pid 的子进程重新挂到 new_parent 下，返回被重新挂载的孤儿列表"""

    def get_all_descendants(self, pid: int) -> List[int]: ...
    """获取指定进程的所有后代进程（递归）"""

    def visualize_ascii(self) -> str: ...
    """返回进程树的 ASCII 可视化字符串"""


# ============================================================
# 帧管理器接口（B 实现）
# ============================================================
class FrameManagerInterface(Protocol):
    """物理内存帧管理接口"""

    def allocate(self) -> int: ...
    """分配一个空闲物理帧，返回帧号。无空闲帧时触发页面置换。"""

    def incref(self, frame: int) -> None: ...
    """增加帧的引用计数（COW fork 时使用）"""

    def decref(self, frame: int) -> None: ...
    """减少帧的引用计数，归零时自动回收到空闲列表"""

    def get_free_count(self) -> int: ...
    """返回当前空闲帧数量"""

    def get_total_count(self) -> int: ...
    """返回总帧数"""


# ============================================================
# COW 内存管理接口（B 实现）
# ============================================================
class COWManagerInterface(Protocol):
    """写时复制（COW）内存管理接口"""

    def fork_page_table(self, parent_pt: object) -> object: ...
    """复制页表（COW 方式）：共享物理帧，设置只读位，增加引用计数"""

    def on_page_write(self, pid: int, page_num: int) -> bool: ...
    """处理页面写入。如果触发 COW 则复制帧并返回 True，否则返回 False"""

    def release_all_frames(self, pt: object) -> None: ...
    """释放页表中所有物理帧（进程退出时调用）"""


# ============================================================
# 调度器接口（C 实现）
# ============================================================
class SchedulerInterface(Protocol):
    """Stride 调度器接口"""

    def enqueue(self, pid: int) -> None: ...
    """将进程加入就绪队列"""

    def dequeue(self) -> Optional[int]: ...
    """从就绪队列中取出下一个要运行的进程 PID，队列为空返回 None"""

    def remove(self, pid: int) -> None: ...
    """从就绪队列中移除指定进程（进程退出时调用）"""

    def update_after_run(self, pid: int, ticks: int) -> None: ...
    """进程运行指定 tick 数后更新调度状态（pass_value 累加等）"""

    def set_priority(self, pid: int, priority: int) -> None: ...
    """设置进程优先级（同时更新 stride）"""

    def get_queue_snapshot(self) -> List[Tuple[int, float]]: ...
    """获取就绪队列快照，返回 [(pid, pass_value), ...] 列表"""

    def get_running_pid(self) -> Optional[int]: ...
    """获取当前正在运行的进程 PID，没有则返回 None"""


# ============================================================
# 内核接口（D 实现，其他人调用）
# ============================================================
class KernelInterface(Protocol):
    """内核核心接口"""

    def create_process(self, name: str, parent_pid: int = 0) -> int: ...
    """创建新进程，返回新分配的 PID"""

    def destroy_process(self, pid: int) -> None: ...
    """销毁进程，释放所有资源"""

    def get_process(self, pid: int) -> Optional[PCBInterface]: ...
    """获取进程 PCB，不存在返回 None"""

    def get_all_processes(self) -> Dict[int, PCBInterface]: ...
    """获取所有进程的字典 {pid: pcb}"""

    def tick(self) -> None: ...
    """推进一个时间片（驱动调度器和资源回收器）"""

    @property
    def process_tree(self) -> ProcessTreeInterface: ...
    """进程树（只读访问）"""

    @property
    def scheduler(self) -> SchedulerInterface: ...
    """调度器（只读访问）"""

    @property
    def memory_manager(self) -> COWManagerInterface: ...
    """内存管理器（只读访问）"""


# ============================================================
# 系统调用接口（D 实现）
# ============================================================
class SyscallInterface(Protocol):
    """系统调用接口"""

    def sys_fork(self, parent_pid: int) -> int: ...
    """创建子进程。成功返回子进程 PID（父进程收到）或 0（子进程收到），失败返回错误码"""

    def sys_exit(self, pid: int, exit_code: int) -> None: ...
    """进程退出，设置 exit_code，触发级联退出和孤儿回收"""

    def sys_waitpid(self, pid: int, target: int = -1) -> Union[int, str]: ...
    """等待子进程退出。target=-1 表示等待任意子进程。成功返回 exit_code，阻塞返回 BLOCKED，失败返回错误码"""

    def sys_getpid(self, pid: int) -> int: ...
    """获取进程自身 PID"""

    def sys_setpriority(self, pid: int, priority: int) -> int: ...
    """设置进程优先级，成功返回 0，失败返回错误码"""

    def sys_yield(self, pid: int) -> None: ...
    """主动让出 CPU（回到就绪队列）"""
