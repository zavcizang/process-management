"""
test_memory.py — COW 内存管理器单元测试

测试内容：
1. 帧分配和回收
2. 引用计数管理
3. COW 页表复制（零拷贝）
4. 写时复制触发
5. 页表释放
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kernel.memory_manager import FrameManager, PageTable, PageTableEntry, COWManager


def test_frame_allocate():
    """测试帧分配"""
    fm = FrameManager(total_frames=10)

    # 分配帧
    frame1 = fm.allocate()
    frame2 = fm.allocate()

    assert frame1 != frame2
    assert fm.get_free_count() == 8
    assert fm.get_ref_count(frame1) == 1
    assert fm.get_ref_count(frame2) == 1

    print("[PASS] 帧分配测试通过")


def test_frame_reference_count():
    """测试引用计数"""
    fm = FrameManager(total_frames=10)
    frame = fm.allocate()

    # 增加引用
    fm.incref(frame)
    assert fm.get_ref_count(frame) == 2
    assert fm.is_shared(frame)

    # 减少引用
    fm.decref(frame)
    assert fm.get_ref_count(frame) == 1
    assert not fm.is_shared(frame)

    # 引用归零，自动回收
    fm.decref(frame)
    assert fm.get_ref_count(frame) == 0
    assert fm.get_free_count() == 10

    print("[PASS] 引用计数测试通过")


def test_cow_fork_zero_copy():
    """测试 COW fork 零拷贝"""
    fm = FrameManager(total_frames=16, page_size=4096)
    cow = COWManager(fm)

    # 父进程分配 2 页
    parent_pt = PageTable(page_size=4096)
    frame0 = fm.allocate()
    frame1 = fm.allocate()
    parent_pt.map(0, frame0)
    parent_pt.map(1, frame1)

    free_before = fm.get_free_count()  # 14

    # fork — 应该零拷贝
    child_pt = cow.fork_page_table(parent_pt)

    free_after = fm.get_free_count()
    assert free_after == free_before, f"COW fork 应该零拷贝，但分配了 {free_before - free_after} 帧"

    # 父子进程共享同一物理帧
    parent_entry0 = parent_pt.get_entry(0)
    child_entry0 = child_pt.get_entry(0)
    assert parent_entry0.frame_id == child_entry0.frame_id

    # 帧引用计数应该为 2
    assert fm.get_ref_count(frame0) == 2
    assert fm.get_ref_count(frame1) == 2

    # 父子进程都是只读
    assert not parent_entry0.is_writable
    assert not child_entry0.is_writable

    print("[PASS] COW fork 零拷贝测试通过")


def test_cow_write_trigger():
    """测试 COW 写时复制触发"""
    fm = FrameManager(total_frames=16, page_size=4096)
    cow = COWManager(fm)

    # 父进程分配 1 页
    parent_pt = PageTable(page_size=4096)
    frame0 = fm.allocate()
    parent_pt.map(0, frame0)

    # fork
    child_pt = cow.fork_page_table(parent_pt)

    free_before = fm.get_free_count()  # 15

    # 子进程写入第 0 页 — 应该触发 COW
    triggered = cow.on_page_write(child_pt, 0)
    assert triggered == True

    free_after = fm.get_free_count()
    assert free_after == free_before - 1, f"COW 应该复制 1 帧，但分配了 {free_before - free_after} 帧"

    # 子进程现在有独立的帧
    child_entry0 = child_pt.get_entry(0)
    assert child_entry0.is_writable
    assert child_entry0.is_dirty

    # 父子进程不再共享同一帧
    parent_entry0 = parent_pt.get_entry(0)
    assert parent_entry0.frame_id != child_entry0.frame_id

    # 父进程仍然是只读（因为还有其他共享者）
    # 但此时 ref_count 已经是 1，所以应该是可写的
    # 注意：这里父进程需要再触发一次 COW 才能写

    print("[PASS] COW 写时复制触发测试通过")


def test_cow_write_no_trigger():
    """测试非 COW 写入（帧已独立）"""
    fm = FrameManager(total_frames=16, page_size=4096)
    cow = COWManager(fm)

    # 父进程分配 1 页
    parent_pt = PageTable(page_size=4096)
    frame0 = fm.allocate()
    parent_pt.map(0, frame0, is_writable=True)

    # 直接写入（不触发 COW）
    triggered = cow.on_page_write(parent_pt, 0)
    assert triggered == False

    entry = parent_pt.get_entry(0)
    assert entry.is_dirty

    print("[PASS] 非 COW 写入测试通过")


def test_release_all_frames():
    """测试释放所有帧"""
    fm = FrameManager(total_frames=16, page_size=4096)
    cow = COWManager(fm)

    # 父进程分配 2 页
    parent_pt = PageTable(page_size=4096)
    frame0 = fm.allocate()
    frame1 = fm.allocate()
    parent_pt.map(0, frame0)
    parent_pt.map(1, frame1)

    # fork
    child_pt = cow.fork_page_table(parent_pt)

    # 释放子进程的帧
    cow.release_all_frames(child_pt)

    # 帧引用计数应该减少
    assert fm.get_ref_count(frame0) == 1
    assert fm.get_ref_count(frame1) == 1

    # 子进程页表应该为空
    assert len(child_pt.get_all_entries()) == 0

    print("[PASS] 释放帧测试通过")


def test_multiple_forks():
    """测试多次 fork"""
    fm = FrameManager(total_frames=16, page_size=4096)
    cow = COWManager(fm)

    # 父进程分配 1 页
    parent_pt = PageTable(page_size=4096)
    frame0 = fm.allocate()
    parent_pt.map(0, frame0)

    # fork 3 次
    child1_pt = cow.fork_page_table(parent_pt)
    child2_pt = cow.fork_page_table(parent_pt)
    child3_pt = cow.fork_page_table(parent_pt)

    # 帧引用计数应该为 4
    assert fm.get_ref_count(frame0) == 4

    # 释放所有子进程
    cow.release_all_frames(child1_pt)
    cow.release_all_frames(child2_pt)
    cow.release_all_frames(child3_pt)

    # 帧引用计数应该为 1
    assert fm.get_ref_count(frame0) == 1

    print("[PASS] 多次 fork 测试通过")


def test_memory_stats():
    """测试内存统计"""
    fm = FrameManager(total_frames=16, page_size=4096)
    stats = fm.get_stats()

    assert stats['total_frames'] == 16
    assert stats['used_frames'] == 0
    assert stats['free_frames'] == 16
    assert stats['shared_frames'] == 0
    assert stats['page_size'] == 4096

    print("[PASS] 内存统计测试通过")


if __name__ == "__main__":
    test_frame_allocate()
    test_frame_reference_count()
    test_cow_fork_zero_copy()
    test_cow_write_trigger()
    test_cow_write_no_trigger()
    test_release_all_frames()
    test_multiple_forks()
    test_memory_stats()
    print("\n[DONE] 所有内存管理器测试通过！")
