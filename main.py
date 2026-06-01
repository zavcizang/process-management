"""
main.py — 进程管理模拟器主程序

功能：
1. 初始化内核
2. 启动交互式 Shell
3. 或运行指定的演示脚本

使用方式：
  python main.py              # 启动交互式 Shell
  python main.py --demo basic # 运行基础演示
  python main.py --test       # 运行所有测试
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kernel.kernel import Kernel
from interactive import OSShell


def print_banner():
    """打印启动横幅"""
    print("=" * 60)
    print("    进程管理模拟器 — 操作系统校赛作品")
    print("=" * 60)
    print("  核心功能: fork + waitpid + exit + getpid")
    print("  创新特性: COW写时复制 | Stride公平调度 | 级联退出")
    print("  输入 help 查看命令列表")
    print("=" * 60)


def run_tests():
    """运行所有测试"""
    import subprocess

    test_dir = os.path.join(os.path.dirname(__file__), 'tests')
    test_files = [
        'test_pcb.py',
        'test_process_tree.py',
        'test_scheduler.py',
        'test_memory.py',
        'test_kernel.py',
    ]

    print("运行所有测试...\n")
    all_passed = True

    for test_file in test_files:
        test_path = os.path.join(test_dir, test_file)
        result = subprocess.run([sys.executable, test_path], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[FAIL] {test_file}")
            print(result.stdout)
            print(result.stderr)
            all_passed = False
        else:
            print(f"[PASS] {test_file}")

    if all_passed:
        print("\n[DONE] 所有测试通过！")
    else:
        print("\n[FAIL] 部分测试失败！")
        sys.exit(1)


def main():
    """主函数"""
    if len(sys.argv) > 1:
        arg = sys.argv[1]

        if arg == '--test':
            run_tests()
            return

        elif arg == '--demo':
            if len(sys.argv) > 2:
                demo_name = sys.argv[2]
                run_demo(demo_name)
            else:
                print("用法: python main.py --demo <demo_name>")
                print("可用演示: basic, cow, stride, zombie, orphan")
            return

        elif arg == '--help':
            print("用法:")
            print("  python main.py              # 启动交互式 Shell")
            print("  python main.py --test       # 运行所有测试")
            print("  python main.py --demo basic # 运行基础演示")
            return

    # 默认启动交互式 Shell
    print_banner()
    kernel = Kernel(max_processes=64, total_frames=256)
    shell = OSShell(kernel)
    shell.run()


def run_demo(demo_name: str):
    """运行指定的演示脚本"""
    demos = {
        'basic': 'demos/basic_fork.py',
        'cow': 'demos/cow_demo.py',
        'stride': 'demos/stride_demo.py',
        'zombie': 'demos/zombie_demo.py',
        'orphan': 'demos/orphan_demo.py',
    }

    if demo_name not in demos:
        print(f"未知演示: {demo_name}")
        print(f"可用演示: {', '.join(demos.keys())}")
        return

    demo_path = os.path.join(os.path.dirname(__file__), demos[demo_name])
    if os.path.exists(demo_path):
        os.system(f'{sys.executable} {demo_path}')
    else:
        print(f"演示文件不存在: {demo_path}")


if __name__ == '__main__':
    main()
