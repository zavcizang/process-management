"""
test_pcb.py — StrideCOWScheduler PCB 单元测试

项目: StrideCOWScheduler — 进程管理内核模拟器
作者: zavci (zjh3432512933)
仓库: https://gitee.com/zjh3432512933/process-management

测试内容：
1. PCB 创建和默认值
2. 状态转换合法性
3. reset 功能
4. to_dict 序列化
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.pcb import PCB, ProcessState


def test_pcb_creation():
    """测试 PCB 创建和默认值"""
    pcb = PCB(pid=1, ppid=0, name="test")

    assert pcb.pid == 1
    assert pcb.ppid == 0
    assert pcb.name == "test"
    assert pcb.state == ProcessState.NEW
    assert pcb.priority == 128
    assert pcb.nice == 0
    assert pcb.cpu_time == 0.0
    assert pcb.wait_time == 0.0
    assert pcb.arrival_time == 0.0
    assert pcb.start_time == -1.0
    assert pcb.children == []
    assert pcb.exit_code == 0
    assert pcb.wait_queue == []
    assert pcb.page_faults == 0
    assert pcb.cow_copies == 0
    assert pcb.context_switches == 0
    print("[PASS] PCB 创建和默认值测试通过")


def test_state_transitions():
    """测试状态转换合法性"""
    pcb = PCB(pid=1, ppid=0, name="test")

    # NEW → READY（合法）
    assert pcb.set_state(ProcessState.READY) == True
    assert pcb.state == ProcessState.READY

    # READY → RUNNING（合法）
    assert pcb.set_state(ProcessState.RUNNING) == True
    assert pcb.state == ProcessState.RUNNING

    # RUNNING → ZOMBIE（合法）
    assert pcb.set_state(ProcessState.ZOMBIE) == True
    assert pcb.state == ProcessState.ZOMBIE

    # ZOMBIE → TERMINATED（合法）
    assert pcb.set_state(ProcessState.TERMINATED) == True
    assert pcb.state == ProcessState.TERMINATED

    # TERMINATED → 任何状态（非法）
    assert pcb.set_state(ProcessState.NEW) == False
    assert pcb.state == ProcessState.TERMINATED  # 状态不变

    print("[PASS] 状态转换测试通过")


def test_invalid_transitions():
    """测试非法状态转换"""
    pcb = PCB(pid=1, ppid=0, name="test")

    # NEW → RUNNING（非法，必须经过 READY）
    assert pcb.set_state(ProcessState.RUNNING) == False
    assert pcb.state == ProcessState.NEW  # 状态不变

    # NEW → ZOMBIE（非法）
    assert pcb.set_state(ProcessState.ZOMBIE) == False
    assert pcb.state == ProcessState.NEW

    print("[PASS] 非法状态转换测试通过")


def test_reset():
    """测试 reset 功能"""
    pcb = PCB(pid=1, ppid=0, name="test")
    pcb.set_state(ProcessState.RUNNING)
    pcb.cpu_time = 10.0
    pcb.wait_time = 5.0
    pcb.start_time = 2.0
    pcb.children = [2, 3]
    pcb.exit_code = 42
    pcb.page_faults = 5
    pcb.cow_copies = 3

    pcb.reset()

    # 保留的字段
    assert pcb.pid == 1
    assert pcb.ppid == 0
    assert pcb.name == "test"

    # 重置的字段
    assert pcb.state == ProcessState.NEW
    assert pcb.cpu_time == 0.0
    assert pcb.wait_time == 0.0
    assert pcb.start_time == -1.0
    assert pcb.children == []
    assert pcb.exit_code == 0
    assert pcb.page_faults == 0
    assert pcb.cow_copies == 0

    print("[PASS] Reset 功能测试通过")


def test_to_dict():
    """测试 to_dict 序列化"""
    pcb = PCB(pid=1, ppid=0, name="test", priority=10, nice=5)
    pcb.set_state(ProcessState.READY)
    pcb.cpu_time = 3.14159

    d = pcb.to_dict()

    assert d['pid'] == 1
    assert d['ppid'] == 0
    assert d['name'] == "test"
    assert d['state'] == ProcessState.READY
    assert d['priority'] == 10
    assert d['nice'] == 5
    assert d['cpu_time'] == 3.14159
    assert isinstance(d['children'], list)
    assert isinstance(d['wait_queue'], list)

    print("[PASS] to_dict 序列化测试通过")


def test_repr():
    """测试 __repr__ 输出"""
    pcb = PCB(pid=1, ppid=0, name="test")
    r = repr(pcb)
    assert "pid=1" in r
    assert "name='test'" in r
    assert "NEW" in r
    print("[PASS] __repr__ 输出测试通过")


if __name__ == "__main__":
    test_pcb_creation()
    test_state_transitions()
    test_invalid_transitions()
    test_reset()
    test_to_dict()
    test_repr()
    print("\n[DONE] 所有 PCB 测试通过！")
