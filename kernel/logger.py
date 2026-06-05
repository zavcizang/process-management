"""
logger.py — StrideCOWScheduler 内核日志系统

项目: StrideCOWScheduler — 进程管理内核模拟器
作者: zavci (zjh3432512933)
仓库: https://gitee.com/zjh3432512933/process-management

记录内核的所有操作，用于调试和演示。

使用方式：
    logger = KernelLogger()
    logger.log("CREATE", "pid=1 name=shell")
    logger.log("FORK", "pid=1 → pid=2")
    logger.dump()  # 输出所有日志
"""

from typing import List, Tuple
from datetime import datetime


class KernelLogger:
    """
    内核日志记录器

    记录所有内核操作，支持：
    - 按时间戳记录
    - 按类型过滤
    - 输出到文件或控制台

    使用示例：
        logger = KernelLogger()
        logger.log_event("CREATE", 1, "name=shell")
        logger.log_event("FORK", 1, "→ pid=2")
        logger.dump()
    """

    # 日志颜色（ANSI）
    COLORS = {
        'CREATE': '\033[32m',    # 绿色
        'DESTROY': '\033[31m',   # 红色
        'FORK': '\033[36m',      # 青色
        'EXIT': '\033[33m',      # 黄色
        'WAIT': '\033[35m',      # 紫色
        'SIGNAL': '\033[31m',    # 红色
        'SCHEDULE': '\033[34m',  # 蓝色
        'MEMORY': '\033[37m',    # 白色
        'IPC': '\033[32m',       # 绿色
        'CONTEXT': '\033[36m',   # 青色
        'INFO': '\033[37m',      # 白色
    }

    RESET = '\033[0m'

    def __init__(self, enabled: bool = True, colored: bool = True):
        """
        Args:
            enabled: 是否启用日志
            colored: 是否使用颜色输出
        """
        self._enabled = enabled
        self._colored = colored
        self._events: List[Tuple[float, str, int, str]] = []
        self._start_time = datetime.now()

    def log_event(self, event_type: str, pid: int, detail: str, tick: int = -1):
        """
        记录一个内核事件。

        Args:
            event_type: 事件类型（CREATE, DESTROY, FORK, EXIT, WAIT, SCHEDULE, MEMORY, IPC）
            pid: 相关进程 PID
            detail: 事件详情
            tick: 时钟周期（可选）
        """
        if not self._enabled:
            return

        timestamp = (datetime.now() - self._start_time).total_seconds()
        self._events.append((timestamp, event_type, pid, detail))

    def log_create(self, pid: int, name: str, parent_pid: int = -1):
        """记录进程创建"""
        detail = f"name={name}"
        if parent_pid >= 0:
            detail += f" parent={parent_pid}"
        self.log_event("CREATE", pid, detail)

    def log_destroy(self, pid: int, reason: str = ""):
        """记录进程销毁"""
        detail = reason if reason else "normal"
        self.log_event("DESTROY", pid, detail)

    def log_fork(self, parent_pid: int, child_pid: int):
        """记录 fork 操作"""
        self.log_event("FORK", parent_pid, f"→ pid={child_pid}")

    def log_exit(self, pid: int, exit_code: int):
        """记录进程退出"""
        self.log_event("EXIT", pid, f"code={exit_code}")

    def log_wait(self, pid: int, target_pid: int, result):
        """记录 waitpid 操作"""
        if isinstance(result, int) and result >= 0:
            self.log_event("WAIT", pid, f"waits_for={target_pid} → exit_code={result}")
        else:
            self.log_event("WAIT", pid, f"waits_for={target_pid} → blocked")

    def log_schedule(self, old_pid: int, new_pid: int):
        """记录上下文切换"""
        self.log_event("SCHEDULE", new_pid, f"from={old_pid}")

    def log_memory(self, pid: int, detail: str):
        """记录内存操作"""
        self.log_event("MEMORY", pid, detail)

    def log_ipc(self, detail: str):
        """记录 IPC 操作"""
        self.log_event("IPC", -1, detail)

    def dump(self, last_n: int = 0) -> str:
        """
        输出所有日志。

        Args:
            last_n: 只输出最后 N 条（0=全部）

        Returns:
            日志字符串
        """
        events = self._events
        if last_n > 0:
            events = events[-last_n:]

        lines = []
        lines.append("=" * 60)
        lines.append("内核日志 (dmesg)")
        lines.append("=" * 60)

        for i, (timestamp, event_type, pid, detail) in enumerate(events):
            # 时间戳
            ts_str = f"T={i:4d}"

            # 事件类型（带颜色）
            if self._colored:
                color = self.COLORS.get(event_type, self.RESET)
                type_str = f"{color}{event_type:<10}{self.RESET}"
            else:
                type_str = f"{event_type:<10}"

            # 进程 PID
            pid_str = f"pid={pid:4d}" if pid >= 0 else "pid=  -1"

            # 完整行
            line = f"[{ts_str}] {type_str} {pid_str} {detail}"
            lines.append(line)

        lines.append("=" * 60)
        lines.append(f"共 {len(events)} 条日志")
        lines.append("=" * 60)

        return "\n".join(lines)

    def get_events(self, event_type: str = None) -> List[Tuple]:
        """
        获取日志事件（可按类型过滤）。

        Args:
            event_type: 事件类型过滤（None=全部）

        Returns:
            [(timestamp, type, pid, detail), ...]
        """
        if event_type:
            return [e for e in self._events if e[1] == event_type]
        return self._events.copy()

    def get_summary(self) -> dict:
        """获取日志统计摘要"""
        summary = {}
        for _, event_type, _, _ in self._events:
            summary[event_type] = summary.get(event_type, 0) + 1
        return summary

    def clear(self):
        """清空日志"""
        self._events.clear()
        self._start_time = datetime.now()

    def save_to_file(self, filename: str):
        """保存日志到文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(self.dump())
        print(f"[日志] 已保存到 {filename}")

    def __repr__(self) -> str:
        return f"KernelLogger(events={len(self._events)}, enabled={self._enabled})"
