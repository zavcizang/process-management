"""
test_process_tree.py — StrideCOWScheduler 进程树单元测试

项目: StrideCOWScheduler — 进程管理内核模拟器
作者: zavci (zjh3432512933)
仓库: https://gitee.com/zjh3432512933/process-management

测试内容：
1. 添加/移除进程
2. 父子关系查询
3. 孤儿进程回收
4. 后代进程获取
5. ASCII 可视化
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.process_tree import ProcessTree


def test_add_and_remove():
    """测试添加和移除进程"""
    tree = ProcessTree()

    # 添加 init 进程
    tree.add_process(0, -1)
    assert tree.has_process(0)
    assert tree.get_parent(0) == -1

    # 添加子进程
    tree.add_process(1, 0)
    tree.add_process(2, 0)
    assert tree.has_process(1)
    assert tree.has_process(2)

    # 移除子进程（无子进程，可以直接移除）
    tree.remove_process(2)
    assert not tree.has_process(2)

    print("[PASS] 添加/移除进程测试通过")


def test_add_duplicate_raises():
    """测试添加重复 PID 抛出异常"""
    tree = ProcessTree()
    tree.add_process(0, -1)

    try:
        tree.add_process(0, -1)
        assert False, "应该抛出 ValueError"
    except ValueError as e:
        assert "已存在" in str(e)

    print("[PASS] 重复 PID 异常测试通过")


def test_add_with_missing_parent_raises():
    """测试添加进程时父进程不存在抛出异常"""
    tree = ProcessTree()

    try:
        tree.add_process(1, 999)  # 父进程 999 不存在
        assert False, "应该抛出 ValueError"
    except ValueError as e:
        assert "不存在" in str(e)

    print("[PASS] 父进程不存在异常测试通过")


def test_get_children():
    """测试获取子进程"""
    tree = ProcessTree()
    tree.add_process(0, -1)  # init
    tree.add_process(1, 0)   # shell
    tree.add_process(2, 0)   # daemon
    tree.add_process(3, 1)   # editor
    tree.add_process(4, 1)   # compiler

    assert tree.get_children(0) == [1, 2]
    assert tree.get_children(1) == [3, 4]
    assert tree.get_children(2) == []
    assert tree.get_children(999) == []  # 不存在的进程返回空列表

    print("[PASS] 获取子进程测试通过")


def test_reparent_orphans():
    """测试孤儿进程回收"""
    tree = ProcessTree()
    tree.add_process(0, -1)  # init
    tree.add_process(1, 0)   # shell
    tree.add_process(2, 1)   # editor
    tree.add_process(3, 1)   # compiler
    tree.add_process(4, 2)   # linker (editor 的子进程)

    # shell 退出，子进程挂到 init 下
    orphans = tree.reparent_orphans(1, 0)
    assert set(orphans) == {2, 3}
    assert tree.get_parent(2) == 0
    assert tree.get_parent(3) == 0
    assert tree.get_children(0) == [1, 2, 3]
    assert tree.get_children(1) == []

    # editor 退出，linker 挂到 init 下
    orphans = tree.reparent_orphans(2, 0)
    assert orphans == [4]
    assert tree.get_parent(4) == 0

    print("[PASS] 孤儿进程回收测试通过")


def test_remove_with_children_raises():
    """测试移除仍有子进程的节点抛出异常"""
    tree = ProcessTree()
    tree.add_process(0, -1)
    tree.add_process(1, 0)

    try:
        tree.remove_process(0)  # init 还有子进程
        assert False, "应该抛出 ValueError"
    except ValueError as e:
        assert "仍有子进程" in str(e)

    print("[PASS] 移除有子进程节点异常测试通过")


def test_get_all_descendants():
    """测试获取所有后代进程"""
    tree = ProcessTree()
    tree.add_process(0, -1)  # init
    tree.add_process(1, 0)   # shell
    tree.add_process(2, 0)   # daemon
    tree.add_process(3, 1)   # editor
    tree.add_process(4, 1)   # compiler
    tree.add_process(5, 2)   # worker

    descendants = tree.get_all_descendants(0)
    assert set(descendants) == {1, 2, 3, 4, 5}

    descendants = tree.get_all_descendants(1)
    assert set(descendants) == {3, 4}

    descendants = tree.get_all_descendants(2)
    assert descendants == [5]

    descendants = tree.get_all_descendants(3)
    assert descendants == []

    print("[PASS] 获取后代进程测试通过")


def test_get_process_count():
    """测试进程计数"""
    tree = ProcessTree()
    assert tree.get_process_count() == 0

    tree.add_process(0, -1)
    assert tree.get_process_count() == 1

    tree.add_process(1, 0)
    tree.add_process(2, 0)
    assert tree.get_process_count() == 3

    tree.remove_process(2)
    assert tree.get_process_count() == 2

    print("[PASS] 进程计数测试通过")


def test_visualize_ascii():
    """测试 ASCII 可视化"""
    tree = ProcessTree()
    tree.add_process(0, -1)  # init
    tree.add_process(1, 0)   # shell
    tree.add_process(2, 0)   # daemon
    tree.add_process(3, 1)   # editor

    viz = tree.visualize_ascii()
    assert "PID=0" in viz
    assert "PID=1" in viz
    assert "PID=2" in viz
    assert "PID=3" in viz

    print("[PASS] ASCII 可视化测试通过")
    print("  输出：")
    for line in viz.split("\n"):
        print(f"    {line}")


def test_cascade_scenario():
    """测试完整的级联退出场景"""
    tree = ProcessTree()

    # 构建进程树：init → A → B → C
    tree.add_process(0, -1)  # init
    tree.add_process(1, 0)   # A
    tree.add_process(2, 1)   # B
    tree.add_process(3, 2)   # C

    # A 退出，B 成为孤儿
    orphans = tree.reparent_orphans(1, 0)
    assert orphans == [2]
    assert tree.get_parent(2) == 0

    # B 退出，C 成为孤儿
    orphans = tree.reparent_orphans(2, 0)
    assert orphans == [3]
    assert tree.get_parent(3) == 0

    # 清理
    tree.remove_process(3)
    tree.remove_process(2)
    tree.remove_process(1)

    assert tree.get_process_count() == 1  # 只剩 init

    print("[PASS] 级联退出场景测试通过")


if __name__ == "__main__":
    test_add_and_remove()
    test_add_duplicate_raises()
    test_add_with_missing_parent_raises()
    test_get_children()
    test_reparent_orphans()
    test_remove_with_children_raises()
    test_get_all_descendants()
    test_get_process_count()
    test_visualize_ascii()
    test_cascade_scenario()
    print("\n[DONE] 所有进程树测试通过！")
