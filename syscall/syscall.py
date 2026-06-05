"""
syscall.py — StrideCOWScheduler 系统调用层

项目: StrideCOWScheduler — 进程管理内核模拟器
作者: zavci (zjh3432512933)
仓库: https://gitee.com/zjh3432512933/process-management

实现操作系统的核心系统调用：
- sys_fork: 创建子进程（基于 COW 写时复制）
- sys_exit: 进程退出（级联退出 + 孤儿回收）
- sys_waitpid: 等待子进程退出
- sys_getpid: 获取进程 PID
- sys_setpriority: 设置进程优先级
- sys_yield: 主动让出 CPU

设计原则：
- 所有系统调用通过 Kernel 实例访问底层资源
- 错误通过 error_codes 返回，不抛异常
- 状态转换统一通过 PCB.set_state() 验证
"""

from typing import Union

from core.pcb import PCB, ProcessState
from error_codes import ErrorCode


class SyscallHandler:
    """
    系统调用处理器

    使用示例：
        kernel = Kernel()
        syscall = SyscallHandler(kernel)

        child_pid = syscall.sys_fork(parent_pid=1)
        syscall.sys_exit(child_pid, exit_code=0)
        result = syscall.sys_waitpid(parent_pid=1, target=-1)
    """

    def __init__(self, kernel):
        """
        Args:
            kernel: Kernel 实例，提供底层资源访问
        """
        self._kernel = kernel

    def sys_fork(self, parent_pid: int) -> int:
        """
        创建子进程。

        流程：
        1. 检查父进程是否存在
        2. 检查子进程数限制
        3. 创建子进程 PCB
        4. COW 复制页表（零拷贝）
        5. 注册到进程树
        6. 加入就绪队列

        Args:
            parent_pid: 父进程 PID

        Returns:
            成功：子进程 PID（父进程收到）或 0（子进程收到）
            失败：错误码（负数）
        """
        # 检查父进程
        parent = self._kernel.get_process(parent_pid)
        if parent is None:
            return ErrorCode.ESRCH

        # 检查子进程数限制
        if len(parent.children) >= parent.max_children:
            return ErrorCode.EAGAIN

        try:
            # 创建子进程
            child_pid = self._kernel.create_process(
                name=f"{parent.name}_child",
                parent_pid=parent_pid,
                priority=parent.priority,
            )

            # COW 复制页表
            child = self._kernel.get_process(child_pid)
            if child and parent.page_table:
                child_page_table = self._kernel.memory_manager.fork_page_table(parent.page_table)
                child.page_table = child_page_table

            # 复制文件描述符（IPC）
            self._kernel.ipc_manager.fork_pipe(parent_pid, child_pid)

            return child_pid

        except RuntimeError:
            return ErrorCode.EAGAIN

    def sys_exit(self, pid: int, exit_code: int = 0) -> None:
        """
        进程退出。

        三阶段退出协议：
        1. 自身状态转换：RUNNING → ZOMBIE
        2. 子进程处理：孤儿进程重新挂到 init
        3. 通知父进程：如果父进程在 wait，唤醒它

        Args:
            pid: 进程 PID
            exit_code: 退出码
        """
        pcb = self._kernel.get_process(pid)
        if pcb is None:
            return

        # 阶段1：自身状态转换
        pcb.exit_code = exit_code
        pcb.set_state(ProcessState.ZOMBIE)

        # 从调度队列中移除
        self._kernel.scheduler.remove(pid)

        # 释放物理内存帧（保留 PCB，因为父进程可能还要读 exit_code）
        if pcb.page_table:
            self._kernel.memory_manager.release_all_frames(pcb.page_table)

        # 阶段2：子进程处理（级联退出）
        for child_pid in pcb.children[:]:
            child = self._kernel.get_process(child_pid)
            if child is None:
                continue

            if child.state == ProcessState.ZOMBIE:
                # 子进程已退出，直接销毁
                self._kernel.destroy_process(child_pid)
            else:
                # 孤儿进程！重新挂到 init 进程下
                self._kernel.process_tree.reparent_orphans(pid, 0)
                # 更新 PCB 的 ppid
                child.ppid = 0
                # 如果 init 正在 wait，唤醒它
                self._wakeup_parent_if_waiting(0)

        # 阶段3：通知父进程
        self._wakeup_parent_if_waiting(pcb.ppid, pid)

    def _wakeup_parent_if_waiting(self, parent_pid: int, child_pid: int = -1) -> None:
        """
        如果父进程正在 waitpid，唤醒它。

        Args:
            parent_pid: 父进程 PID
            child_pid: 退出的子进程 PID（-1 表示任意）
        """
        parent = self._kernel.get_process(parent_pid)
        if parent is None:
            return

        if parent.state != ProcessState.SLEEPING:
            return

        # 检查父进程是否在等待这个子进程
        if -1 in parent.wait_queue or child_pid in parent.wait_queue:
            # 唤醒父进程
            parent.set_state(ProcessState.READY)
            self._kernel.scheduler.enqueue(parent_pid)

    def sys_waitpid(self, pid: int, target: int = -1) -> Union[int, str]:
        """
        等待子进程退出。

        Args:
            pid: 父进程 PID
            target: 目标子进程 PID（-1 表示等待任意子进程）

        Returns:
            成功：子进程的 exit_code
            阻塞：ErrorCode.BLOCKED（父进程进入 SLEEPING）
            失败：错误码（负数）
        """
        parent = self._kernel.get_process(pid)
        if parent is None:
            return ErrorCode.ESRCH

        # 检查是否有子进程
        if not parent.children:
            return ErrorCode.ECHILD

        # 查找已退出的子进程
        for child_pid in parent.children[:]:
            if target != -1 and child_pid != target:
                continue

            child = self._kernel.get_process(child_pid)
            if child is None:
                continue

            if child.state == ProcessState.ZOMBIE:
                # 找到已退出的子进程，回收它
                exit_code = child.exit_code
                self._kernel.destroy_process(child_pid)
                return exit_code

        # 没有已退出的子进程，阻塞等待
        parent.set_state(ProcessState.SLEEPING)
        parent.wait_queue.append(target)
        return ErrorCode.BLOCKED

    def sys_getpid(self, pid: int) -> int:
        """
        获取进程自身 PID。

        Args:
            pid: 进程 PID

        Returns:
            进程 PID
        """
        return pid

    def sys_setpriority(self, pid: int, priority: int) -> int:
        """
        设置进程优先级。

        Args:
            pid: 进程 PID
            priority: 新优先级 (0-255)

        Returns:
            成功返回 0，失败返回错误码
        """
        pcb = self._kernel.get_process(pid)
        if pcb is None:
            return ErrorCode.ESRCH

        if priority < 0 or priority > 255:
            return ErrorCode.EINVAL

        pcb.priority = priority
        if self._kernel.scheduler:
            self._kernel.scheduler.set_priority(pid, priority)

        return ErrorCode.SUCCESS

    def sys_yield(self, pid: int) -> None:
        """
        主动让出 CPU。

        进程从 RUNNING 回到 READY，重新加入调度队列。
        """
        pcb = self._kernel.get_process(pid)
        if pcb is None:
            return

        if pcb.state == ProcessState.RUNNING:
            pcb.set_state(ProcessState.READY)
            self._kernel.scheduler.enqueue(pid)

    def __repr__(self) -> str:
        return f"SyscallHandler(kernel={self._kernel})"
