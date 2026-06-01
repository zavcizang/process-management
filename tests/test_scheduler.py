"""
test_scheduler.py — Stride 调度器单元测试

测试内容：
1. 进程注册和注销
2. 就绪队列操作（enqueue/dequeue）
3. 调度公平性验证
4. 优先级动态调整
5. 溢出处理
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kernel.scheduler import StrideScheduler, BIG_STRIDE


def test_register_and_unregister():
    """测试进程注册和注销"""
    sched = StrideScheduler()

    sched.register(1, priority=10)
    sched.register(2, priority=20)

    # 注册后可以入队
    sched.enqueue(1)
    sched.enqueue(2)

    # 注销后不能入队
    sched.unregister(1)
    try:
        sched.enqueue(1)
        assert False, "应该抛出 ValueError"
    except ValueError:
        pass

    print("[PASS] 注册/注销测试通过")


def test_enqueue_dequeue():
    """测试入队和出队"""
    sched = StrideScheduler()

    sched.register(1, priority=10)
    sched.register(2, priority=10)

    sched.enqueue(1)
    sched.enqueue(2)

    # 第一次出队应该是 pass_value 最小的（都是 0，按 FIFO）
    pid1 = sched.dequeue()
    assert pid1 in [1, 2]

    pid2 = sched.dequeue()
    assert pid2 in [1, 2]
    assert pid2 != pid1

    # 队列为空
    assert sched.dequeue() is None

    print("[PASS] 入队/出队测试通过")


def test_stride_fairness():
    """测试 Stride 调度公平性

    优先级设计：
    - priority=10: stride = BIG/(256-10) = BIG/246 ≈ 4065
    - priority=133: stride = BIG/(256-133) = BIG/123 ≈ 8130

    stride 比值 ≈ 2:1，所以 CPU 时间比 ≈ 2:1
    """
    sched = StrideScheduler()

    # 注册 3 个进程，优先级使得 stride 比约为 2:1
    sched.register(1, priority=10)   # 高优先级，stride ≈ 4065
    sched.register(2, priority=133)  # 低优先级，stride ≈ 8130
    sched.register(3, priority=133)  # 低优先级，stride ≈ 8130

    sched.enqueue(1)
    sched.enqueue(2)
    sched.enqueue(3)

    # 运行 200 个 tick，统计每个进程的 CPU 时间
    cpu_count = {1: 0, 2: 0, 3: 0}

    for _ in range(200):
        pid = sched.dequeue()
        if pid:
            cpu_count[pid] += 1
            sched.update_after_run(pid, 1)
            sched.enqueue(pid)

    total = sum(cpu_count.values())
    ratio_1 = cpu_count[1] / total
    ratio_2 = cpu_count[2] / total
    ratio_3 = cpu_count[3] / total

    # 进程1应该获得约 50% CPU，进程2和3各约 25%
    # 允许 10% 的误差
    assert 0.40 <= ratio_1 <= 0.60, f"进程1 CPU比例异常: {ratio_1:.2%}"
    assert 0.15 <= ratio_2 <= 0.35, f"进程2 CPU比例异常: {ratio_2:.2%}"
    assert 0.15 <= ratio_3 <= 0.35, f"进程3 CPU比例异常: {ratio_3:.2%}"

    print(f"[PASS] 公平性测试通过: A={cpu_count[1]}({ratio_1:.1%}), B={cpu_count[2]}({ratio_2:.1%}), C={cpu_count[3]}({ratio_3:.1%})")


def test_set_priority():
    """测试优先级调整"""
    sched = StrideScheduler()

    sched.register(1, priority=10)
    stride_before = sched._registry[1]['stride']

    # 降低优先级（数值变大）
    sched.set_priority(1, priority=20)
    stride_after = sched._registry[1]['stride']

    # stride 应该变大（优先级降低）
    assert stride_after > stride_before

    print("[PASS] 优先级调整测试通过")


def test_overflow_handling():
    """测试溢出处理"""
    sched = StrideScheduler()

    sched.register(1, priority=10)
    sched.register(2, priority=20)

    # 手动设置 pass_value 很大
    sched._registry[1]['pass_value'] = BIG_STRIDE * 200
    sched._registry[2]['pass_value'] = BIG_STRIDE * 200 + 100

    sched.enqueue(1)
    sched.enqueue(2)

    # 更新后应该触发溢出处理
    pid = sched.dequeue()
    sched.update_after_run(pid, 1)

    # pass_value 应该被重置到较小的值
    for entry in sched._registry.values():
        assert entry['pass_value'] < BIG_STRIDE * 100

    print("[PASS] 溢出处理测试通过")


def test_get_queue_snapshot():
    """测试获取队列快照"""
    sched = StrideScheduler()

    sched.register(1, priority=10)
    sched.register(2, priority=20)

    sched.enqueue(1)
    sched.enqueue(2)

    snapshot = sched.get_queue_snapshot()
    assert len(snapshot) == 2
    assert isinstance(snapshot[0], tuple)
    assert isinstance(snapshot[0][0], int)  # pid
    assert isinstance(snapshot[0][1], float)  # pass_value

    print("[PASS] 队列快照测试通过")


def test_stats():
    """测试统计信息"""
    sched = StrideScheduler()

    sched.register(1, priority=10)
    sched.enqueue(1)

    pid = sched.dequeue()
    sched.update_after_run(pid, 1)

    stats = sched.get_stats()
    assert stats['total_ticks'] == 1
    assert stats['schedule_count'] == 1
    assert stats['registered_count'] == 1

    print("[PASS] 统计信息测试通过")


if __name__ == "__main__":
    test_register_and_unregister()
    test_enqueue_dequeue()
    test_stride_fairness()
    test_set_priority()
    test_overflow_handling()
    test_get_queue_snapshot()
    test_stats()
    print("\n[DONE] 所有调度器测试通过！")
