"""
tree_view.py — StrideCOWScheduler 进程树可视化

项目: StrideCOWScheduler — 进程管理内核模拟器
作者: zavci (zjh3432512933)
仓库: https://gitee.com/zjh3432512933/process-management

提供进程树的多种可视化方式：
1. ASCII 树形图（终端友好）
2. 状态统计摘要
"""

from typing import Dict, List, Optional
from core.pcb import PCB, ProcessState


def visualize_tree(processes: Dict[int, PCB], tree) -> str:
    """
    生成进程树的 ASCII 可视化。

    Args:
        processes: 进程字典 {pid: pcb}
        tree: ProcessTree 实例

    Returns:
        树形字符串
    """
    return tree.visualize_ascii()


def visualize_tree_with_status(processes: Dict[int, PCB], tree) -> str:
    """
    生成带状态信息的进程树。

    示例输出：
        init (PID=0) [READY]
        ├── shell (PID=1) [RUNNING] ← 当前进程
        │   ├── editor (PID=3) [SLEEPING]
        │   └── compiler (PID=5) [ZOMBIE] ⚠️
        └── daemon (PID=2) [READY]
            └── worker (PID=4) [READY]

    Args:
        processes: 进程字典
        tree: ProcessTree 实例

    Returns:
        带状态的树形字符串
    """
    # 找到根进程
    root = None
    for pid, ppid in tree._parent.items():
        if ppid == -1:
            root = pid
            break

    if root is None:
        return "(空进程树)"

    lines = []
    _build_tree_with_status(root, processes, tree, lines, "", True)
    return "\n".join(lines)


def _build_tree_with_status(pid: int, processes: Dict[int, PCB],
                            tree, lines: List[str], prefix: str, is_last: bool):
    """递归构建带状态的树"""
    pcb = processes.get(pid)
    if pcb is None:
        return

    connector = "└── " if is_last else "├── "

    # 状态图标
    state_icon = {
        ProcessState.NEW: "○",
        ProcessState.READY: "◐",
        ProcessState.RUNNING: "●",
        ProcessState.SLEEPING: "◑",
        ProcessState.ZOMBIE: "☠",
        ProcessState.TERMINATED: "✗",
    }.get(pcb.state, "?")

    # 构建节点文本
    node_text = f"{pcb.name} (PID={pid}) [{pcb.state}] {state_icon}"

    lines.append(f"{prefix}{connector}{node_text}")

    # 递归子进程
    children = tree.get_children(pid)
    for i, child in enumerate(children):
        is_child_last = (i == len(children) - 1)
        extension = "    " if is_last else "│   "
        _build_tree_with_status(child, processes, tree, lines,
                               prefix + extension, is_child_last)


def get_process_summary(processes: Dict[int, PCB]) -> str:
    """
    获取进程状态统计摘要。

    Args:
        processes: 进程字典

    Returns:
        统计摘要字符串
    """
    states = {}
    for pcb in processes.values():
        states[pcb.state] = states.get(pcb.state, 0) + 1

    total = len(processes)
    lines = [
        f"进程统计:",
        f"  总计: {total}",
        f"  运行: {states.get(ProcessState.RUNNING, 0)}",
        f"  就绪: {states.get(ProcessState.READY, 0)}",
        f"  阻塞: {states.get(ProcessState.SLEEPING, 0)}",
        f"  僵尸: {states.get(ProcessState.ZOMBIE, 0)}",
        f"  终止: {states.get(ProcessState.TERMINATED, 0)}",
    ]

    return "\n".join(lines)
