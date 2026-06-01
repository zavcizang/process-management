"""
kernel.py — 内核核心

将所有子系统整合在一起，提供统一的内核接口。

子系统：
- ProcessManager: 进程生命周期管理
- ProcessTree: 进程树（父子关系）
- StrideScheduler: Stride 调度器
- COWManager: COW 内存管理
- IPCManager: 进程间通信（管道）
- KernelLogger: 内核日志
- SyscallHandler: 系统调用处理

设计原则：
- Kernel 是所有子系统的协调者
- init 进程（PID=0）在内核初始化时自动创建
- 每个 tick 驱动调度器执行
"""

from typing import Dict, Optional

from core.pcb import PCB, ProcessState
from core.process_tree import ProcessTree
from kernel.process_manager import ProcessManager
from kernel.scheduler import StrideScheduler
from kernel.memory_manager import FrameManager, COWManager
from kernel.ipc import IPCManager
from kernel.logger import KernelLogger
from syscall.syscall import SyscallHandler
from error_codes import ErrorCode


class Kernel:
    """
    内核核心类

    使用示例：
        kernel = Kernel()
        syscall = SyscallHandler(kernel)

        # 创建进程
        shell_pid = kernel.create_process("shell", parent_pid=0)

        # fork
        child_pid = syscall.sys_fork(shell_pid)

        # 运行
        for _ in range(100):
            kernel.tick()
    """

    def __init__(self, max_processes: int = 64, total_frames: int = 256,
                 enable_logging: bool = True):
        """
        Args:
            max_processes: 最大进程数
            total_frames: 物理内存帧数（默认 256 帧 = 1MB）
            enable_logging: 是否启用内核日志
        """
        # 初始化子系统
        self._tree = ProcessTree()
        self._scheduler = StrideScheduler()
        self._frame_manager = FrameManager(total_frames=total_frames)
        self._cow_manager = COWManager(self._frame_manager)
        self._process_manager = ProcessManager(max_processes=max_processes)
        self._ipc_manager = IPCManager()
        self._logger = KernelLogger(enabled=enable_logging)

        # 绑定子系统
        self._process_manager.bind(self._tree, self._scheduler, self._cow_manager)

        # 系统调用处理器
        self._syscall = SyscallHandler(self)

        # 当前运行的进程 PID
        self._current_pid: Optional[int] = None

        # 系统时钟
        self._tick_count = 0

        # 上下文切换历史：[(tick, old_pid, new_pid), ...]
        self._context_switch_history: list = []

        # 创建 init 进程（PID=0）
        self._create_init_process()

    def _create_init_process(self) -> None:
        """创建 init 进程（PID=0）"""
        init_pid = self._process_manager.create_process(
            name="init",
            parent_pid=-1,  # init 没有父进程
            priority=255,   # 最低优先级
        )
        # init 进程特殊处理：直接设为 READY，不加入调度队列
        init_pcb = self._process_manager.get_process(init_pid)
        init_pcb.set_state(ProcessState.READY)

    @property
    def current_pid(self) -> Optional[int]:
        """当前正在运行的进程 PID"""
        return self._current_pid

    @property
    def process_tree(self) -> ProcessTree:
        """进程树"""
        return self._tree

    @property
    def scheduler(self) -> StrideScheduler:
        """调度器"""
        return self._scheduler

    @property
    def memory_manager(self) -> COWManager:
        """内存管理器"""
        return self._cow_manager

    @property
    def syscall(self) -> SyscallHandler:
        """系统调用处理器"""
        return self._syscall

    @property
    def ipc_manager(self) -> IPCManager:
        """IPC 管理器"""
        return self._ipc_manager

    @property
    def logger(self) -> KernelLogger:
        """内核日志"""
        return self._logger

    def create_process(self, name: str, parent_pid: int = 0,
                       priority: int = 128) -> int:
        """创建新进程"""
        pid = self._process_manager.create_process(name, parent_pid, priority)
        self._logger.log_create(pid, name, parent_pid)
        return pid

    def destroy_process(self, pid: int) -> None:
        """销毁进程"""
        self._logger.log_destroy(pid, "reaped")
        self._process_manager.destroy_process(pid)

    def get_process(self, pid: int) -> Optional[PCB]:
        """获取进程 PCB"""
        return self._process_manager.get_process(pid)

    def get_all_processes(self) -> Dict[int, PCB]:
        """获取所有进程"""
        return self._process_manager.get_all_processes()

    def tick(self) -> None:
        """
        推进一个时间片。

        流程：
        1. 从调度器取出下一个进程
        2. 将当前进程设为 READY（如果还在运行）
        3. 将新进程设为 RUNNING
        4. 更新进程统计
        5. 推进时钟
        """
        self._tick_count += 1
        self._process_manager.set_current_tick(self._tick_count)

        # 保存旧的运行进程
        old_pid = self._current_pid

        # 从调度器取出下一个进程
        next_pid = self._scheduler.dequeue()

        if next_pid is not None:
            # 将旧进程设为 READY（如果还在运行）
            if old_pid is not None:
                old_pcb = self._process_manager.get_process(old_pid)
                if old_pcb and old_pcb.state == ProcessState.RUNNING:
                    old_pcb.set_state(ProcessState.READY)

            # 记录上下文切换（如果进程发生变化）
            if old_pid != next_pid:
                self._context_switch_history.append((self._tick_count, old_pid, next_pid))

            # 将新进程设为 RUNNING
            new_pcb = self._process_manager.get_process(next_pid)
            if new_pcb:
                new_pcb.set_state(ProcessState.RUNNING)
                if new_pcb.start_time < 0:
                    new_pcb.start_time = self._tick_count
                new_pcb.context_switches += 1

            self._current_pid = next_pid
        else:
            # 没有就绪进程，CPU 空闲
            if old_pid is not None:
                old_pcb = self._process_manager.get_process(old_pid)
                if old_pcb and old_pcb.state == ProcessState.RUNNING:
                    old_pcb.set_state(ProcessState.READY)
            self._current_pid = None

        # 更新所有进程的等待时间
        for pcb in self._process_manager.get_all_processes().values():
            if pcb.state == ProcessState.READY:
                pcb.wait_time += 1
            elif pcb.state == ProcessState.RUNNING:
                pcb.cpu_time += 1
                pcb.burst_time += 1

        # 更新调度器
        if self._current_pid is not None:
            self._scheduler.update_after_run(self._current_pid, 1)
            # 进程运行后重新入队
            current_pcb = self._process_manager.get_process(self._current_pid)
            if current_pcb and current_pcb.state == ProcessState.RUNNING:
                self._scheduler.enqueue(self._current_pid)

        # init 进程清理 ZOMBIE 子进程
        self._cleanup_zombies()

    def _cleanup_zombies(self) -> None:
        """init 进程自动清理 ZOMBIE 子进程"""
        init_pcb = self._process_manager.get_process(0)
        if init_pcb is None:
            return

        for child_pid in init_pcb.children[:]:
            child = self._process_manager.get_process(child_pid)
            if child and child.state == ProcessState.ZOMBIE:
                self.destroy_process(child_pid)

    def get_stats(self) -> dict:
        """获取系统统计信息"""
        return {
            'tick_count': self._tick_count,
            'current_pid': self._current_pid,
            'context_switches': len(self._context_switch_history),
            'processes': self._process_manager.get_stats(),
            'scheduler': self._scheduler.get_stats(),
            'memory': self._frame_manager.get_stats(),
        }

    def get_context_switch_history(self) -> list:
        """获取上下文切换历史"""
        return self._context_switch_history.copy()

    def dmesg(self, last_n: int = 0) -> str:
        """
        输出内核日志（类似 Linux dmesg 命令）。

        Args:
            last_n: 只输出最后 N 条（0=全部）

        Returns:
            日志字符串
        """
        return self._logger.dump(last_n)

    def get_log_summary(self) -> dict:
        """获取日志统计摘要"""
        return self._logger.get_summary()

    def __repr__(self) -> str:
        return f"Kernel(tick={self._tick_count}, processes={self._process_manager.get_process_count()})"
