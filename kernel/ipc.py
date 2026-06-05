"""
ipc.py — StrideCOWScheduler 进程间通信（IPC）模块

项目: StrideCOWScheduler — 进程管理内核模拟器
作者: zavci (zjh3432512933)
仓库: https://gitee.com/zjh3432512933/process-management

实现管道（Pipe）机制，支持父子进程之间的数据通信。

管道原理：
- 管道是一个内核缓冲区，有读端和写端
- 父进程 fork 后，父子进程共享同一管道
- 写端写入数据，读端读取数据
- 管道是单向的：一端写，另一端读
- 管道是阻塞的：读端没数据时阻塞，写端满时阻塞

使用示例：
    ipc = IPCManager()
    read_fd, write_fd = ipc.create_pipe()
    ipc.write(write_fd, b"Hello")
    data = ipc.read(read_fd, 1024)
"""

from typing import Dict, List, Optional, Tuple
from collections import deque
import threading


class Pipe:
    """
    管道

    内核中的管道缓冲区，支持阻塞读写。
    """

    # 管道缓冲区大小（模拟）
    BUFFER_SIZE = 4096

    def __init__(self, pipe_id: int):
        self.pipe_id = pipe_id
        self._buffer: deque = deque()
        self._read_fd: int = -1
        self._write_fd: int = -1
        self._readers: int = 0
        self._writers: int = 0
        self._closed: bool = False

    def set_fds(self, read_fd: int, write_fd: int):
        """设置文件描述符"""
        self._read_fd = read_fd
        self._write_fd = write_fd

    def write(self, data: bytes) -> int:
        """
        写入数据到管道。

        Args:
            data: 要写入的数据

        Returns:
            实际写入的字节数

        Raises:
            BrokenPipeError: 管道已关闭
        """
        if self._closed or self._writers <= 0:
            raise BrokenPipeError("管道已关闭")

        # 限制缓冲区大小
        available = self.BUFFER_SIZE - len(self._buffer)
        write_size = min(len(data), available)

        for i in range(write_size):
            self._buffer.append(data[i])

        return write_size

    def read(self, size: int) -> bytes:
        """
        从管道读取数据。

        Args:
            size: 最大读取字节数

        Returns:
            读取到的数据

        Raises:
            EOFError: 管道已关闭且无数据
        """
        if not self._buffer:
            if self._closed:
                raise EOFError("管道已关闭")
            return b""

        result = bytearray()
        while self._buffer and len(result) < size:
            result.append(self._buffer.popleft())

        return bytes(result)

    def is_empty(self) -> bool:
        """检查管道缓冲区是否为空"""
        return len(self._buffer) == 0

    def is_full(self) -> bool:
        """检查管道缓冲区是否已满"""
        return len(self._buffer) >= self.BUFFER_SIZE

    def close_write(self):
        """关闭写端"""
        self._writers -= 1
        if self._writers <= 0:
            self._closed = True

    def close_read(self):
        """关闭读端"""
        self._readers -= 1

    def __len__(self) -> int:
        return len(self._buffer)

    def __repr__(self) -> str:
        return f"Pipe(id={self.pipe_id}, size={len(self._buffer)}, closed={self._closed})"


class IPCManager:
    """
    进程间通信管理器

    管理所有管道和文件描述符。

    使用示例：
        ipc = IPCManager()
        read_fd, write_fd = ipc.create_pipe()

        # 父进程写入
        ipc.write(write_fd, b"Hello")

        # 子进程读取
        data = ipc.read(read_fd, 1024)
    """

    def __init__(self):
        # 管道表：{pipe_id: Pipe}
        self._pipes: Dict[int, Pipe] = {}
        self._next_pipe_id = 0

        # 文件描述符表：{fd: (pipe_id, mode)}
        # mode: 'r' = 读, 'w' = 写
        self._fd_table: Dict[int, Tuple[int, str]] = {}
        self._next_fd = 3  # 0, 1, 2 保留给 stdin/stdout/stderr

        # 每个进程的文件描述符表：{pid: {fd: pipe_id}}
        self._process_fds: Dict[int, Dict[int, int]] = {}

        # 日志（可选）
        self._log_callback = None

    def set_log_callback(self, callback):
        """设置日志回调函数"""
        self._log_callback = callback

    def _log(self, message: str):
        """记录日志"""
        if self._log_callback:
            self._log_callback(message)

    def create_pipe(self, pid: int = 0) -> Tuple[int, int]:
        """
        创建管道。

        Args:
            pid: 创建管道的进程 PID

        Returns:
            (read_fd, write_fd) 读写文件描述符
        """
        pipe_id = self._next_pipe_id
        self._next_pipe_id += 1

        pipe = Pipe(pipe_id)
        self._pipes[pipe_id] = pipe

        # 分配文件描述符
        read_fd = self._next_fd
        self._next_fd += 1
        write_fd = self._next_fd
        self._next_fd += 1

        pipe.set_fds(read_fd, write_fd)

        # 更新文件描述符表
        self._fd_table[read_fd] = (pipe_id, 'r')
        self._fd_table[write_fd] = (pipe_id, 'w')

        # 更新进程文件描述符表
        if pid not in self._process_fds:
            self._process_fds[pid] = {}
        self._process_fds[pid][read_fd] = pipe_id
        self._process_fds[pid][write_fd] = pipe_id

        pipe._readers += 1
        pipe._writers += 1

        self._log(f"IPC: 创建管道 pipe_id={pipe_id}, read_fd={read_fd}, write_fd={write_fd}")

        return read_fd, write_fd

    def fork_pipe(self, parent_pid: int, child_pid: int):
        """
        fork 时复制文件描述符。

        子进程继承父进程的所有文件描述符。

        Args:
            parent_pid: 父进程 PID
            child_pid: 子进程 PID
        """
        if parent_pid not in self._process_fds:
            return

        # 复制父进程的文件描述符表
        self._process_fds[child_pid] = self._process_fds[parent_pid].copy()

        # 增加管道的引用计数
        for pipe_id in self._process_fds[child_pid].values():
            if pipe_id in self._pipes:
                pipe = self._pipes[pipe_id]
                # 根据 fd 类型增加 readers 或 writers
                for fd, (pid, mode) in self._fd_table.items():
                    if pid == pipe_id and mode == 'r':
                        pipe._readers += 1
                    elif pid == pipe_id and mode == 'w':
                        pipe._writers += 1

        self._log(f"IPC: fork 复制文件描述符 parent={parent_pid} → child={child_pid}")

    def write(self, fd: int, data: bytes) -> int:
        """
        写入数据到管道。

        Args:
            fd: 写文件描述符
            data: 要写入的数据

        Returns:
            实际写入的字节数
        """
        if fd not in self._fd_table:
            raise ValueError(f"无效的文件描述符: {fd}")

        pipe_id, mode = self._fd_table[fd]
        if mode != 'w':
            raise ValueError(f"文件描述符 {fd} 不是写端")

        if pipe_id not in self._pipes:
            raise ValueError(f"管道不存在: pipe_id={pipe_id}")

        pipe = self._pipes[pipe_id]
        bytes_written = pipe.write(data)

        self._log(f"IPC: 写入管道 pipe_id={pipe_id}, 写入 {bytes_written} 字节, 数据={data[:20]}")

        return bytes_written

    def read(self, fd: int, size: int) -> bytes:
        """
        从管道读取数据。

        Args:
            fd: 读文件描述符
            size: 最大读取字节数

        Returns:
            读取到的数据
        """
        if fd not in self._fd_table:
            raise ValueError(f"无效的文件描述符: {fd}")

        pipe_id, mode = self._fd_table[fd]
        if mode != 'r':
            raise ValueError(f"文件描述符 {fd} 不是读端")

        if pipe_id not in self._pipes:
            raise ValueError(f"管道不存在: pipe_id={pipe_id}")

        pipe = self._pipes[pipe_id]
        data = pipe.read(size)

        self._log(f"IPC: 读取管道 pipe_id={pipe_id}, 读取 {len(data)} 字节, 数据={data[:20]}")

        return data

    def close_fd(self, fd: int, pid: int = 0):
        """
        关闭文件描述符。

        Args:
            fd: 要关闭的文件描述符
            pid: 进程 PID
        """
        if fd not in self._fd_table:
            return

        pipe_id, mode = self._fd_table[fd]

        if pipe_id in self._pipes:
            pipe = self._pipes[pipe_id]
            if mode == 'w':
                pipe.close_write()
            else:
                pipe.close_read()

        # 从进程文件描述符表中移除
        if pid in self._process_fds and fd in self._process_fds[pid]:
            del self._process_fds[pid][fd]

        self._log(f"IPC: 关闭文件描述符 fd={fd}, pipe_id={pipe_id}")

    def close_process_fds(self, pid: int):
        """
        关闭进程的所有文件描述符（进程退出时调用）。

        Args:
            pid: 进程 PID
        """
        if pid not in self._process_fds:
            return

        for fd in list(self._process_fds[pid].keys()):
            self.close_fd(fd, pid)

        del self._process_fds[pid]

        self._log(f"IPC: 关闭进程 {pid} 的所有文件描述符")

    def get_pipe_info(self, pipe_id: int) -> Optional[dict]:
        """获取管道信息"""
        if pipe_id not in self._pipes:
            return None

        pipe = self._pipes[pipe_id]
        return {
            'pipe_id': pipe_id,
            'size': len(pipe),
            'buffer_size': Pipe.BUFFER_SIZE,
            'closed': pipe._closed,
            'readers': pipe._readers,
            'writers': pipe._writers,
        }

    def get_process_fds(self, pid: int) -> Dict[int, dict]:
        """获取进程的文件描述符表"""
        if pid not in self._process_fds:
            return {}

        result = {}
        for fd, pipe_id in self._process_fds[pid].items():
            pipe_info = self.get_pipe_info(pipe_id)
            if pipe_info:
                _, mode = self._fd_table[fd]
                result[fd] = {
                    'pipe_id': pipe_id,
                    'mode': mode,
                    'pipe_size': pipe_info['size'],
                }

        return result

    def __repr__(self) -> str:
        return f"IPCManager(pipes={len(self._pipes)}, fd_count={self._next_fd})"
