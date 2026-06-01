"""
interactive.py — 交互式操作系统 Shell

提供类似真实 Shell 的交互界面，支持：
- fork: 创建子进程
- wait: 等待子进程退出
- exit: 终止当前进程
- pid: 显示当前进程 PID
- ps: 列出所有进程
- tree: 显示进程树
- sched: 显示调度队列状态
- mem: 显示内存页表
- nice: 调整优先级
- stat: 显示进程统计信息
- kill: 强制杀死进程
- tick: 推进时钟
- help: 显示帮助
- quit: 退出模拟器
"""

from typing import Optional

from core.pcb import PCB, ProcessState
from kernel.kernel import Kernel
from error_codes import ErrorCode


class OSShell:
    """
    交互式操作系统 Shell

    使用示例：
        kernel = Kernel()
        shell = OSShell(kernel)
        shell.run()
    """

    def __init__(self, kernel: Kernel):
        self._kernel = kernel
        self._current_pid = 0  # 当前 shell 进程的 PID
        self._running = True

        # 命令映射
        self._commands = {
            'fork': self._cmd_fork,
            'wait': self._cmd_wait,
            'exit': self._cmd_exit,
            'pid': self._cmd_pid,
            'ps': self._cmd_ps,
            'tree': self._cmd_tree,
            'sched': self._cmd_sched,
            'mem': self._cmd_mem,
            'nice': self._cmd_nice,
            'stat': self._cmd_stat,
            'kill': self._cmd_kill,
            'tick': self._cmd_tick,
            'help': self._cmd_help,
            'quit': self._cmd_quit,
            'q': self._cmd_quit,
            'demo': self._cmd_demo,
            'chart': self._cmd_chart,
            'pipe': self._cmd_pipe,
            'write': self._cmd_write,
            'read': self._cmd_read,
            'dmesg': self._cmd_dmesg,
            'fd': self._cmd_fd,
        }

    def run(self):
        """启动 Shell 主循环"""
        while self._running:
            try:
                prompt = f"[PID:{self._current_pid}] os> "
                cmd_input = input(prompt).strip()

                if not cmd_input:
                    continue

                parts = cmd_input.split()
                cmd = parts[0].lower()
                args = parts[1:]

                if cmd in self._commands:
                    self._commands[cmd](args)
                else:
                    print(f"未知命令: {cmd}，输入 help 查看帮助")

            except KeyboardInterrupt:
                print("\n使用 quit 退出")
            except EOFError:
                break

    def _cmd_fork(self, args: list):
        """fork [name] — 创建子进程"""
        name = args[0] if args else f"child"

        result = self._kernel.syscall.sys_fork(self._current_pid)

        if isinstance(result, int) and result > 0:
            # 父进程
            print(f"子进程已创建: PID={result}")

            # 推进时钟让子进程有机会运行
            for _ in range(3):
                self._kernel.tick()

        elif result == 0:
            # 子进程
            print(f"[子进程] PID={self._kernel.current_pid}")
        else:
            print(f"fork 失败: {ErrorCode.to_string(result)}")

    def _cmd_wait(self, args: list):
        """wait [pid] — 等待子进程退出（-1=任意）"""
        target = int(args[0]) if args else -1

        result = self._kernel.syscall.sys_waitpid(self._current_pid, target)

        if result == ErrorCode.BLOCKED:
            print("等待子进程退出...")
            # 推进时钟直到子进程退出
            for _ in range(100):
                self._kernel.tick()
                # 检查是否有 ZOMBIE 子进程
                pcb = self._kernel.get_process(self._current_pid)
                if pcb and pcb.state == ProcessState.READY:
                    break
            # 再次尝试 waitpid
            result = self._kernel.syscall.sys_waitpid(self._current_pid, target)

        if isinstance(result, int) and result >= 0:
            print(f"子进程退出，exit_code={result}")
        elif result == ErrorCode.ECHILD:
            print("没有子进程")
        else:
            print(f"waitpid 失败: {ErrorCode.to_string(result)}")

    def _cmd_exit(self, args: list):
        """exit [code] — 终止当前进程"""
        exit_code = int(args[0]) if args else 0

        if self._current_pid == 0:
            print("不能退出 init 进程")
            return

        self._kernel.syscall.sys_exit(self._current_pid, exit_code)
        print(f"进程 {self._current_pid} 已退出，exit_code={exit_code}")

        # 切换到父进程
        pcb = self._kernel.get_process(self._current_pid)
        if pcb:
            self._current_pid = pcb.ppid
        else:
            self._current_pid = 0

    def _cmd_pid(self, args: list):
        """pid — 显示当前进程 PID"""
        print(f"当前进程: PID={self._current_pid}")

        pcb = self._kernel.get_process(self._current_pid)
        if pcb:
            print(f"  名称: {pcb.name}")
            print(f"  状态: {pcb.state}")
            print(f"  父进程: PID={pcb.ppid}")

    def _cmd_ps(self, args: list):
        """ps — 列出所有进程"""
        processes = self._kernel.get_all_processes()

        print(f"{'PID':<6} {'PPID':<6} {'名称':<12} {'状态':<10} {'优先级':<8} {'CPU时间':<8}")
        print("-" * 60)

        for pid in sorted(processes.keys()):
            pcb = processes[pid]
            marker = " *" if pid == self._current_pid else ""
            print(f"{pcb.pid:<6} {pcb.ppid:<6} {pcb.name:<12} {pcb.state:<10} {pcb.priority:<8} {pcb.cpu_time:<8.1f}{marker}")

        print(f"\n  总计: {len(processes)} 个进程")

    def _cmd_tree(self, args: list):
        """tree — 显示进程树"""
        viz = self._kernel.process_tree.visualize_ascii()
        print("\n进程树:")
        print(viz)

    def _cmd_sched(self, args: list):
        """sched — 显示调度队列状态"""
        snapshot = self._kernel.scheduler.get_queue_snapshot()
        stats = self._kernel.scheduler.get_stats()

        print("\n调度队列:")
        print(f"{'PID':<8} {'pass_value':<12} {'优先级':<8}")
        print("-" * 30)

        for pid, pass_value in snapshot:
            pcb = self._kernel.get_process(pid)
            priority = pcb.priority if pcb else -1
            print(f"{pid:<8} {pass_value:<12.2f} {priority:<8}")

        print(f"\n统计:")
        print(f"  总时间片: {stats['total_ticks']}")
        print(f"  调度次数: {stats['schedule_count']}")
        print(f"  注册进程: {stats['registered_count']}")

    def _cmd_mem(self, args: list):
        """mem — 显示内存页表"""
        stats = self._kernel.memory_manager._fm.get_stats()

        print("\n内存状态:")
        print(f"  总帧数: {stats['total_frames']}")
        print(f"  已使用: {stats['used_frames']}")
        print(f"  空闲: {stats['free_frames']}")
        print(f"  共享帧: {stats['shared_frames']}")
        print(f"  页大小: {stats['page_size']} 字节")
        print(f"  总内存: {stats['total_memory_mb']:.2f} MB")
        print(f"  已使用: {stats['used_memory_mb']:.2f} MB")

        # 显示当前进程的页表
        pcb = self._kernel.get_process(self._current_pid)
        if pcb and pcb.page_table:
            entries = pcb.page_table.get_all_entries()
            print(f"\n进程 {self._current_pid} 的页表:")
            print(f"  {'页号':<8} {'帧号':<8} {'可写':<6} {'脏页':<6} {'引用':<6}")
            print("  " + "-" * 36)
            for page_num, entry in sorted(entries.items()):
                print(f"  {page_num:<8} {entry.frame_id:<8} {'是' if entry.is_writable else '否':<6} {'是' if entry.is_dirty else '否':<6} {entry.ref_count:<6}")

    def _cmd_nice(self, args: list):
        """nice [pid] [priority] — 调整优先级"""
        if len(args) < 2:
            print("用法: nice <pid> <priority>")
            print("  priority: 0-255，越小越高")
            return

        pid = int(args[0])
        priority = int(args[1])

        result = self._kernel.syscall.sys_setpriority(pid, priority)
        if result == ErrorCode.SUCCESS:
            print(f"进程 {pid} 优先级已设为 {priority}")
        else:
            print(f"设置失败: {ErrorCode.to_string(result)}")

    def _cmd_stat(self, args: list):
        """stat [pid] — 显示进程统计信息"""
        pid = int(args[0]) if args else self._current_pid

        pcb = self._kernel.get_process(pid)
        if pcb is None:
            print(f"进程 {pid} 不存在")
            return

        print(f"\n进程 {pid} 统计:")
        print(f"  名称: {pcb.name}")
        print(f"  状态: {pcb.state}")
        print(f"  父进程: PID={pcb.ppid}")
        print(f"  子进程: {pcb.children}")
        print(f"  优先级: {pcb.priority}")
        print(f"  到达时间: {pcb.arrival_time}")
        print(f"  首次运行: {pcb.start_time}")
        print(f"  CPU时间: {pcb.cpu_time}")
        print(f"  等待时间: {pcb.wait_time}")
        print(f"  上下文切换: {pcb.context_switches}")
        print(f"  缺页次数: {pcb.page_faults}")
        print(f"  COW复制: {pcb.cow_copies}")
        print(f"  内存使用: {pcb.memory_usage} 字节")

    def _cmd_kill(self, args: list):
        """kill <pid> — 强制杀死进程"""
        if not args:
            print("用法: kill <pid>")
            return

        pid = int(args[0])

        if pid == 0:
            print("不能杀死 init 进程")
            return

        pcb = self._kernel.get_process(pid)
        if pcb is None:
            print(f"进程 {pid} 不存在")
            return

        # 先设置为 RUNNING 才能转 ZOMBIE
        if pcb.state == ProcessState.READY:
            pcb.set_state(ProcessState.RUNNING)
        self._kernel.syscall.sys_exit(pid, exit_code=-1)
        print(f"进程 {pid} 已被杀死")

    def _cmd_tick(self, args: list):
        """tick [n] — 推进 n 个时钟周期"""
        n = int(args[0]) if args else 1

        for _ in range(n):
            self._kernel.tick()

        print(f"已推进 {n} 个时钟周期，当前 tick={self._kernel._tick_count}")

    def _cmd_demo(self, args: list):
        """demo <name> — 运行演示脚本"""
        from main import run_demo
        if args:
            run_demo(args[0])
        else:
            print("可用演示: basic, cow, stride, zombie, orphan")

    def _cmd_chart(self, args: list):
        """chart [type] — 生成 matplotlib 图表"""
        from visualizer.charts import ChartGenerator

        chart = ChartGenerator(output_dir='output')

        chart_type = args[0] if args else 'all'

        if chart_type == 'all':
            chart.plot_all(self._kernel)
        elif chart_type == 'gantt':
            chart.plot_gantt(self._kernel)
        elif chart_type == 'cpu':
            chart.plot_cpu_utilization(self._kernel)
        elif chart_type == 'memory':
            chart.plot_memory_usage(self._kernel)
        elif chart_type == 'stride':
            chart.plot_stride_fairness(self._kernel.get_all_processes())
        elif chart_type == 'switch':
            chart.plot_context_switches(self._kernel)
        elif chart_type == 'mapping':
            chart.plot_memory_mapping(self._kernel)
        else:
            print("可用图表: all, gantt, cpu, memory, stride, switch, mapping")

    def _cmd_pipe(self, args: list):
        """pipe — 创建管道"""
        read_fd, write_fd = self._kernel.ipc_manager.create_pipe(self._current_pid)
        print(f"管道已创建: read_fd={read_fd}, write_fd={write_fd}")

    def _cmd_write(self, args: list):
        """write <fd> <data> — 写入管道"""
        if len(args) < 2:
            print("用法: write <fd> <data>")
            return

        fd = int(args[0])
        data = ' '.join(args[1:]).encode('utf-8')

        try:
            bytes_written = self._kernel.ipc_manager.write(fd, data)
            print(f"写入 {bytes_written} 字节: {data.decode('utf-8')}")
        except Exception as e:
            print(f"写入失败: {e}")

    def _cmd_read(self, args: list):
        """read <fd> [size] — 读取管道"""
        if not args:
            print("用法: read <fd> [size]")
            return

        fd = int(args[0])
        size = int(args[1]) if len(args) > 1 else 1024

        try:
            data = self._kernel.ipc_manager.read(fd, size)
            if data:
                print(f"读取 {len(data)} 字节: {data.decode('utf-8')}")
            else:
                print("管道为空")
        except Exception as e:
            print(f"读取失败: {e}")

    def _cmd_dmesg(self, args: list):
        """dmesg — 查看内核日志"""
        last_n = int(args[0]) if args else 0
        print(self._kernel.dmesg(last_n))

    def _cmd_fd(self, args: list):
        """fd [pid] — 查看进程文件描述符"""
        pid = int(args[0]) if args else self._current_pid
        fds = self._kernel.ipc_manager.get_process_fds(pid)

        if not fds:
            print(f"进程 {pid} 没有打开的文件描述符")
            return

        print(f"\n进程 {pid} 的文件描述符:")
        print(f"  {'FD':<6} {'类型':<6} {'管道ID':<8} {'缓冲区':<8}")
        print("  " + "-" * 30)

        for fd, info in sorted(fds.items()):
            mode_str = "读" if info['mode'] == 'r' else "写"
            print(f"  {fd:<6} {mode_str:<6} {info['pipe_id']:<8} {info['pipe_size']:<8}")

    def _cmd_help(self, args: list):
        """help — 显示帮助"""
        print("\n可用命令:")
        print("  --- 进程管理 ---")
        print("  fork [name]         创建子进程")
        print("  wait [pid]          等待子进程退出（-1=任意）")
        print("  exit [code]         终止当前进程")
        print("  pid                 显示当前进程 PID")
        print("  ps                  列出所有进程")
        print("  tree                显示进程树")
        print("  stat [pid]          显示进程统计信息")
        print("  kill <pid>          强制杀死进程")
        print("  --- IPC（管道通信）---")
        print("  pipe                创建管道")
        print("  write <fd> <data>   写入管道")
        print("  read <fd> [size]    读取管道")
        print("  fd [pid]            查看文件描述符")
        print("  --- 调度和内存 ---")
        print("  sched               显示调度队列状态")
        print("  mem                 显示内存页表")
        print("  nice <pid> <pri>    调整优先级")
        print("  --- 工具 ---")
        print("  tick [n]            推进 n 个时钟周期")
        print("  dmesg               查看内核日志")
        print("  chart [type]        生成图表 (all/gantt/cpu/memory/stride/switch/mapping)")
        print("  demo <name>         运行演示脚本")
        print("  --- 系统 ---")
        print("  help                显示帮助")
        print("  quit / q            退出模拟器")

    def _cmd_quit(self, args: list):
        """quit — 退出模拟器"""
        print("再见！")
        self._running = False
