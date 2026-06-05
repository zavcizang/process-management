"""
process_tree.py — StrideCOWScheduler 进程树管理

项目: StrideCOWScheduler — 进程管理内核模拟器
作者: zavci (zjh3432512933)
仓库: https://gitee.com/zjh3432512933/process-management

维护进程之间的父子关系，支持：
- 进程添加/移除
- 孤儿进程回收（父进程退出时，子进程重新挂到 init 下）
- 获取所有后代进程
- ASCII 可视化输出

设计原则：
- 使用字典存储树结构 {pid: [child_pid, ...]}，O(1) 查找子进程
- reparent_orphans 实现级联退出中的孤儿回收机制
- visualize_ascii 用于调试和演示
"""

from typing import Dict, List, Optional, Set


class ProcessTree:
    """
    进程树管理器

    核心职责：
    1. 维护进程的父子关系
    2. 在父进程退出时，将子进程重新挂到 init 进程下
    3. 提供树形结构的查询和可视化

    使用示例：
        tree = ProcessTree()
        tree.add_process(0, -1)  # init 进程
        tree.add_process(1, 0)   # shell，父进程是 init
        tree.add_process(2, 1)   # editor，父进程是 shell

        tree.get_children(1)     # → [2]
        tree.reparent_orphans(1, 0)  # shell 退出，editor 挂到 init 下
        tree.get_children(0)     # → [1, 2] (init 收养了 editor)
    """

    def __init__(self):
        # 核心数据结构：{pid: [child_pid, ...]}
        self._children: Dict[int, List[int]] = {}
        # 父进程映射：{pid: ppid}，方便快速查找父进程
        self._parent: Dict[int, int] = {}

    def add_process(self, pid: int, ppid: int) -> None:
        """
        添加进程节点到树中。

        Args:
            pid: 新进程的 PID
            ppid: 父进程的 PID（init 进程的 ppid 应为 -1）

        Raises:
            ValueError: 如果 pid 已存在或 ppid 不存在（除 init 外）
        """
        if pid in self._children:
            raise ValueError(f"进程 PID={pid} 已存在于进程树中")

        # init 进程的父进程为 -1，不需要检查 ppid 是否存在
        if ppid != -1 and ppid not in self._children:
            raise ValueError(f"父进程 PID={ppid} 不存在于进程树中")

        # 添加到树中
        self._children[pid] = []
        self._parent[pid] = ppid

        # 如果有父进程，将自己加入父进程的子进程列表
        if ppid != -1:
            self._children[ppid].append(pid)

    def remove_process(self, pid: int) -> None:
        """
        从树中移除进程节点。

        注意：调用前必须先处理子进程（reparent 或 cascade exit）。

        Args:
            pid: 要移除的进程 PID

        Raises:
            ValueError: 如果进程不存在或仍有子进程
        """
        if pid not in self._children:
            raise ValueError(f"进程 PID={pid} 不存在于进程树中")

        if self._children[pid]:
            raise ValueError(
                f"进程 PID={pid} 仍有子进程 {self._children[pid]}，"
                f"请先调用 reparent_orphans 处理子进程"
            )

        # 从父进程的子进程列表中移除自己
        ppid = self._parent.get(pid, -1)
        if ppid != -1 and ppid in self._children:
            if pid in self._children[ppid]:
                self._children[ppid].remove(pid)

        # 从树中删除
        del self._children[pid]
        del self._parent[pid]

    def get_children(self, pid: int) -> List[int]:
        """
        获取指定进程的直接子进程列表。

        Args:
            pid: 进程 PID

        Returns:
            子进程 PID 列表（副本）
        """
        if pid not in self._children:
            return []
        return self._children[pid][:]

    def get_parent(self, pid: int) -> int:
        """
        获取指定进程的父进程 PID。

        Args:
            pid: 进程 PID

        Returns:
            父进程 PID，如果进程不存在返回 -1
        """
        return self._parent.get(pid, -1)

    def reparent_orphans(self, dead_pid: int, new_parent: int) -> List[int]:
        """
        将 dead_pid 的子进程重新挂到 new_parent 下。

        这是级联退出机制的核心：当一个进程退出时，它的子进程变成孤儿，
        需要重新挂到 init 进程（或其他指定进程）下。

        Args:
            dead_pid: 退出的进程 PID
            new_parent: 新的父进程 PID（通常是 init）

        Returns:
            被重新挂载的孤儿进程 PID 列表

        Raises:
            ValueError: 如果 dead_pid 或 new_parent 不存在
        """
        if dead_pid not in self._children:
            raise ValueError(f"进程 PID={dead_pid} 不存在于进程树中")
        if new_parent not in self._children:
            raise ValueError(f"新父进程 PID={new_parent} 不存在于进程树中")

        orphans = self._children[dead_pid][:]

        for orphan_pid in orphans:
            # 更新父进程映射
            self._parent[orphan_pid] = new_parent
            # 从旧父进程的子列表中移除
            # （dead_pid 的子列表会在 remove_process 时清空）
            # 加入新父进程的子列表
            self._children[new_parent].append(orphan_pid)

        # 清空 dead_pid 的子列表
        self._children[dead_pid] = []

        return orphans

    def get_all_descendants(self, pid: int) -> List[int]:
        """
        获取指定进程的所有后代进程（递归遍历）。

        Args:
            pid: 进程 PID

        Returns:
            所有后代进程的 PID 列表（广度优先顺序）
        """
        descendants = []
        queue = [pid]

        while queue:
            current = queue.pop(0)
            children = self._children.get(current, [])
            descendants.extend(children)
            queue.extend(children)

        return descendants

    def get_process_count(self) -> int:
        """返回进程树中的进程总数"""
        return len(self._children)

    def has_process(self, pid: int) -> bool:
        """检查进程是否存在于树中"""
        return pid in self._children

    def visualize_ascii(self) -> str:
        """
        生成进程树的 ASCII 可视化字符串。

        示例输出：
            init (PID=0)
            ├── shell (PID=1)
            │   ├── editor (PID=3)
            │   └── compiler (PID=5)
            └── daemon (PID=2)
                └── worker (PID=4)

        Returns:
            树形字符串
        """
        # 找到根进程（ppid == -1 的进程）
        root = None
        for pid, ppid in self._parent.items():
            if ppid == -1:
                root = pid
                break

        if root is None:
            return "(空进程树)"

        lines = []
        self._build_ascii(root, lines, "", True)
        return "\n".join(lines)

    def _build_ascii(self, pid: int, lines: List[str], prefix: str, is_last: bool) -> None:
        """递归构建 ASCII 树的辅助方法"""
        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}PID={pid}")

        children = self._children.get(pid, [])
        for i, child in enumerate(children):
            is_child_last = (i == len(children) - 1)
            extension = "    " if is_last else "│   "
            self._build_ascii(child, lines, prefix + extension, is_child_last)

    def __repr__(self) -> str:
        return f"ProcessTree(processes={len(self._children)})"
