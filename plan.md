# 进程管理模拟器 — 校赛规划

## 一、项目定位与核心创新点

### 为什么选用户态模拟

5人新手团队，1-2周时间。裸机内核（xv6改造）的学习成本太高，容易卡在环境搭建上。**用户态模拟**能把全部精力放在算法创新和演示效果上，这是评委看得到的东西。

关键认知：评委看重的不是"你在哪一层跑"，而是：
1. **你对 OS 概念的理解深度** — PCB、状态机、COW、调度算法
2. **算法的创新性** — 不是照抄课本，而是有自己的设计
3. **演示效果** — 能直观看到进程树、调度过程、资源回收

### 五大创新点（核心卖点）

| # | 创新点 | 难度 | 亮点 |
|---|--------|------|------|
| 1 | **COW Fork（写时复制）** | ⭐⭐⭐ | 不是简化版，而是真正的引用计数+脏页追踪+按需复制 |
| 2 | **Stride 调度算法** | ⭐⭐⭐ | 公平调度的数学保证，比 RR/MLFQ 更高级 |
| 3 | **级联退出 + 孤儿进程回收** | ⭐⭐ | 完整的进程树生命周期管理，含 init 进程兜底 |
| 4 | **实时可视化引擎** | ⭐⭐ | 进程树 + 甘特图 + 内存页表 三合一动画 |
| 5 | **竞态条件模拟** | ⭐⭐⭐ | 可选加分项：展示 fork 在并发下的 race condition |

---

## 二、系统架构

```
┌─────────────────────────────────────────────────────────┐
│                   用户交互层 (CLI/TUI)                   │
│   命令: fork | wait | exit | ps | tree | sched | mem    │
├─────────────────────────────────────────────────────────┤
│                  可视化引擎 (visualizer/)                │
│  进程树动画 | 调度甘特图 | 内存页表热力图 | 实时仪表盘      │
├─────────────────────────────────────────────────────────┤
│                  系统调用层 (syscall/)                   │
│  sys_fork | sys_waitpid | sys_exit | sys_getpid         │
│  sys_setpriority | sys_yield                            │
├─────────────────────────────────────────────────────────┤
│                   内核核心层 (kernel/)                   │
│  进程管理器 | COW内存管理器 | 调度器 | 资源回收器          │
├─────────────────────────────────────────────────────────┤
│                   数据结构层 (core/)                     │
│  PCB | PageTable | VirtualMemory | ProcessTree          │
└─────────────────────────────────────────────────────────┘
```

---

## 三、核心数据结构设计

### 3.1 进程控制块 (PCB)

```python
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, List
import time

class ProcessState(Enum):
    NEW = "NEW"              # 刚创建
    READY = "READY"          # 就绪，等待调度
    RUNNING = "RUNNING"      # 正在CPU上执行
    SLEEPING = "SLEEPING"    # 阻塞等待（如 waitpid 等子进程）
    ZOMBIE = "ZOMBIE"        # 已退出，等待父进程回收
    TERMINATED = "TERMINATED" # 彻底销毁

@dataclass
class PCB:
    pid: int                          # 进程ID
    ppid: int                         # 父进程ID
    name: str                         # 进程名
    state: ProcessState = ProcessState.NEW

    # 调度相关
    priority: int = 128               # 静态优先级 (0-255, 越小越高)
    dynamic_priority: float = 128.0   # 动态优先级（Stride调度用）
    stride: float = 0.0              # 步长 = BIG_CONSTANT / priority
    pass_value: float = 0.0          # 累计步长（调度决策依据）
    nice: int = 0                     # nice值 (-20 ~ 19)

    # 时间统计
    arrival_time: float = 0.0         # 创建时间
    start_time: float = -1.0          # 首次运行时间
    cpu_time: float = 0.0            # 累计CPU时间
    wait_time: float = 0.0           # 累计等待时间
    burst_time: float = 0.0          # 本次突发执行时间

    # COW内存
    page_table: Optional['PageTable'] = None  # 虚拟页表
    memory_usage: int = 0             # 实际物理内存占用(bytes)

    # 进程树
    children: List[int] = field(default_factory=list)  # 子进程PID列表
    exit_code: int = 0               # 退出码
    wait_queue: List[int] = field(default_factory=list) # 等待此进程的父进程PID

    # 统计信息
    page_faults: int = 0             # 缺页次数
    cow_copies: int = 0              # COW触发次数
    context_switches: int = 0        # 上下文切换次数
```

### 3.2 COW 页表结构

```python
@dataclass
class PageTableEntry:
    frame_id: int                     # 物理帧号
    is_valid: bool = True             # 有效位
    is_writable: bool = True          # 可写位（COW时设为False）
    is_dirty: bool = False            # 脏位（写过才置1）
    ref_count: int = 1                # 引用计数（COW核心）
    last_access: float = 0.0          # 最后访问时间（LRU用）

class PageTable:
    def __init__(self, page_size: int = 4096):
        self.page_size = page_size
        self.entries: Dict[int, PageTableEntry] = {}  # 页号 -> PTE
```

### 3.3 进程树

```python
class ProcessTree:
    """维护进程父子关系，支持级联退出和孤儿回收"""
    def __init__(self):
        self.root: int = 0            # init进程 PID=0
        self.nodes: Dict[int, 'ProcessTreeNode'] = {}

    def add_process(self, pid: int, ppid: int): ...
    def remove_process(self, pid: int): ...
    def get_children(self, pid: int) -> List[int]: ...
    def get_orphans(self, dead_pid: int) -> List[int]: ...
    def reparent_orphans(self, dead_pid: int, new_parent: int): ...
    def visualize_ascii(self) -> str: ...  # 树形文本输出
```

---

## 四、创新算法详解

### 4.1 COW Fork（写时复制）— 创新点 #1

**为什么这是创新**：课本上 fork 只是"复制 PCB"，但真正的 COW 涉及引用计数、脏页追踪、按需复制三个机制的协同。

**完整流程**：

```
sys_fork(parent_pid):
  │
  ├─ 1. 分配新 PCB（浅拷贝父进程元数据）
  │     - 复制：priority, nice, page_table引用, 环境变量
  │     - 不复制：cpu_time, wait_time, children(空), pass_value(重置)
  │
  ├─ 2. COW 页表复制（关键创新）
  │     for each page in parent.page_table:
  │       - 子进程的 PTE 指向同一个物理帧
  │       - 父进程 PTE.is_writable = False
  │       - 子进程 PTE.is_writable = False
  │       - 物理帧 ref_count += 1
  │     （此时零内存拷贝！只复制了页表项）
  │
  ├─ 3. 注册到进程树
  │     - parent.children.append(child_pid)
  │     - process_tree.add_process(child_pid, parent_pid)
  │
  └─ 4. 加入就绪队列
        - scheduler.enqueue(child_pid)
        - 返回 child_pid 给父进程，0 给子进程
```

**写时复制触发**（页面写入时）：

```
on_page_write(pid, page_num):
  entry = page_table[page_num]
  if entry.is_writable:
    entry.is_dirty = True
    return  # 正常写入

  # COW 触发！
  if entry.ref_count == 1:
    # 只剩自己引用，直接改权限
    entry.is_writable = True
    entry.is_dirty = True
  else:
    # 多人共享，需要复制物理帧
    old_frame = entry.frame_id
    new_frame = allocate_frame()
    memcpy(new_frame, old_frame)  # 真正的内存拷贝
    entry.frame_id = new_frame
    entry.is_writable = True
    entry.is_dirty = True
    entry.ref_count = 1
    # 原帧引用计数减1
    frame_manager.decref(old_frame)
  pcb.cow_copies += 1
```

**页帧管理器**：

```python
class FrameManager:
    """管理物理内存帧，支持引用计数"""
    def __init__(self, total_frames: int = 256):  # 256帧 = 1MB (4KB/帧)
        self.total_frames = total_frames
        self.ref_counts: List[int] = [0] * total_frames
        self.free_list: List[int] = list(range(total_frames))

    def allocate(self) -> int:
        """分配一个空闲帧"""
        if not self.free_list:
            return self._evict()  # 触发页面置换
        frame = self.free_list.pop(0)
        self.ref_counts[frame] = 1
        return frame

    def incref(self, frame: int):
        self.ref_counts[frame] += 1

    def decref(self, frame: int):
        self.ref_counts[frame] -= 1
        if self.ref_counts[frame] == 0:
            self.free_list.append(frame)  # 回收

    def _evict(self) -> int:
        """页面置换（结合 LRU + 访问频率）"""
        # 详见 4.4 节
```

### 4.2 Stride 调度算法 — 创新点 #2

**为什么选 Stride 而不是 MLFQ**：MLFQ 是教科书算法，大家都做。Stride 是 **Linux CFS 的数学基础**，有严格的公平性证明，而且实现起来有技巧（溢出处理、优先级映射）。

**核心思想**：每个进程有一个 `stride = BIG / priority`。每次调度选 `pass_value` 最小的进程运行。运行一次后 `pass_value += stride`。

**数学证明**：对于两个进程 A(priority=10) 和 B(priority=5)：
- stride_A = 1000/10 = 100, stride_B = 1000/5 = 200
- 经过 3 次调度后：pass_A = 300, pass_B = 400
- CPU 时间比 = 1/stride_A : 1/stride_B = 1/100 : 1/200 = 2:1
- 优先级高的进程获得 2 倍 CPU 时间 ✓

**完整实现**：

```python
BIG_STRIDE = 1_000_000  # 大常数

class StrideScheduler:
    """Stride 公平调度器

    特性：
    1. 严格公平：优先级高的进程获得更多CPU时间，比例精确可控
    2. 无饥饿：所有进程最终都会被调度
    3. O(1) 调度：使用最小堆
    4. 优先级动态调整：基于进程行为（I/O密集 vs CPU密集）
    """

    def __init__(self):
        self.ready_queue = []  # 最小堆: (pass_value, pid)
        self.processes: Dict[int, PCB] = {}

    def enqueue(self, pid: int, pcb: PCB):
        stride = BIG_STRIDE / max(pcb.priority, 1)
        pcb.stride = stride
        heapq.heappush(self.ready_queue, (pcb.pass_value, pid))

    def dequeue(self) -> Optional[int]:
        if not self.ready_queue:
            return None
        pass_val, pid = heapq.heappop(self.ready_queue)
        return pid

    def update_after_run(self, pid: int, tick: int):
        """进程运行一个tick后更新"""
        pcb = self.processes[pid]
        pcb.pass_value += pcb.stride
        pcb.cpu_time += 1

        # 动态优先级调整（创新扩展）
        self._adjust_priority(pcb)

    def _adjust_priority(self, pcb: PCB):
        """基于进程行为动态调整优先级

        - I/O密集型进程（频繁sleep）：提升优先级（降低stride）
          理由：I/O密集型进程通常需要快速响应
        - CPU密集型进程（长时间运行）：降低优先级（增加stride）
          理由：CPU密集型进程可以容忍更长等待
        """
        if pcb.cpu_time > 0 and pcb.burst_time > 0:
            io_ratio = 1.0 - (pcb.burst_time / (pcb.cpu_time + pcb.burst_time))
            # io_ratio 高 → I/O密集 → 提升优先级
            adjustment = int(io_ratio * 30 - 15)  # [-15, +15]
            pcb.priority = max(1, min(255, pcb.priority - adjustment))
            pcb.stride = BIG_STRIDE / max(pcb.priority, 1)
```

**溢出处理**（竞赛加分细节）：

```python
def _handle_overflow(self):
    """当 pass_value 接近溢出时，重置所有进程的 pass_value

    策略：减去所有进程中最小的 pass_value，保持相对差值不变
    """
    if self.ready_queue and self.ready_queue[0][0] > BIG_STRIDE * 100:
        min_pass = self.ready_queue[0][0]
        self.ready_queue = [(p - min_pass, pid) for p, pid in self.ready_queue]
        heapq.heapify(self.ready_queue)
        for pcb in self.processes.values():
            pcb.pass_value -= min_pass
```

### 4.3 级联退出与孤儿进程回收 — 创新点 #3

**三阶段退出协议**：

```
sys_exit(pid, exit_code):
  │
  ├─ 阶段1：自身状态转换
  │   pcb.state = ZOMBIE
  │   pcb.exit_code = exit_code
  │   释放所有物理内存帧（COW引用计数递减）
  │   从调度队列移除
  │
  ├─ 阶段2：子进程处理（级联退出）
  │   for child_pid in pcb.children:
  │     if child is ZOMBIE:
  │       直接销毁（子进程已退出，只是等回收）
  │     else:
  │       # 孤儿进程！重新挂到 init 进程下
  │       child.ppid = INIT_PID (0)
  │       init.children.append(child_pid)
  │       # 如果 init 正在 wait，唤醒它
  │       if INIT_PID in pcb.wait_queue:
  │         wakeup(INIT_PID)
  │
  └─ 阶段3：通知父进程
      parent = get_process(pcb.ppid)
      if parent.state == SLEEPING and pcb.ppid in parent.wait_queue:
        # 父进程正在 waitpid 等这个子进程
        parent.state = READY
        scheduler.enqueue(parent.pid)
      else:
        # 父进程还没 wait，保持 ZOMBIE 等待回收
        pass

sys_waitpid(parent_pid, target_pid=-1):
  │
  ├─ 查找已退出的子进程
  │   parent = get_process(parent_pid)
  │   for child_pid in parent.children[:]:
  │     child = get_process(child_pid)
  │     if child.state == ZOMBIE:
  │       # 回收成功
  │       result = child.exit_code
  │       destroy_process(child_pid)
  │       parent.children.remove(child_pid)
  │       return result
  │
  └─ 没有已退出的子进程
      if has_children(parent_pid):
        # 阻塞等待
        parent.state = SLEEPING
        parent.wait_queue.append(target_pid)  # -1表示等待任意子进程
        return BLOCKED
      else:
        # 没有子进程，返回错误
        return -1  # ECHILD
```

**init 进程（PID=0）的特殊角色**：

```python
class InitProcess:
    """init 进程，所有孤儿进程的最终归宿

    模拟 systemd/init 的职责：
    1. 永远不会退出
    2. 自动回收所有孤儿进程
    3. 周期性清理 ZOMBIE 子进程
    """
    PID = 0

    def run(self, kernel):
        while True:
            # 主动清理 ZOMBIE 子进程
            for child_pid in kernel.process_tree.get_children(self.PID):
                child = kernel.get_process(child_pid)
                if child.state == ProcessState.ZOMBIE:
                    kernel.destroy_process(child_pid)
                    kernel.process_tree.remove_process(child_pid)
            kernel.tick()
```

### 4.4 智能页面置换（COW 的后备策略）— 附加创新

当物理帧耗尽时，需要选择一个帧换出。结合 **LFU + 访问时间** 的双因子策略：

```python
class SmartEviction:
    """双因子页面置换算法

    score(frame) = α * recency(frame) + β * frequency(frame)

    recency: 距离上次访问的时间（越大越应该换出）
    frequency: 访问次数的倒数（越大越应该换出）

    创新点：α/β 比值根据系统负载动态调整
    - 内存压力大时（free < 10%）：α 增大，优先换出最近没用的
    - 内存压力小时：β 增大，优先换出不常用的
    """

    def __init__(self, frame_manager: 'FrameManager'):
        self.fm = frame_manager
        self.access_log: Dict[int, List[float]] = {}  # frame -> [access_times]
        self.alpha = 0.6  # recency 权重
        self.beta = 0.4   # frequency 权重

    def select_victim(self, current_time: float) -> int:
        # 动态调整 α/β
        free_ratio = len(self.fm.free_list) / self.fm.total_frames
        if free_ratio < 0.1:
            self.alpha, self.beta = 0.8, 0.2  # 内存紧张，重 recency
        elif free_ratio > 0.3:
            self.alpha, self.beta = 0.4, 0.6  # 内存充裕，重 frequency

        best_score = -1
        victim = -1

        for frame in range(self.fm.total_frames):
            if self.fm.ref_counts[frame] == 0:
                continue  # 空帧跳过

            # 计算 recency（距离上次访问的时间）
            last_access = self._get_last_access(frame)
            recency = current_time - last_access

            # 计算 frequency（访问频率的倒数）
            freq = self._get_frequency(frame)
            inv_freq = 1.0 / max(freq, 0.001)

            # 归一化
            norm_recency = min(recency / 1000.0, 1.0)
            norm_inv_freq = min(inv_freq / 100.0, 1.0)

            score = self.alpha * norm_recency + self.beta * norm_inv_freq
            if score > best_score:
                best_score = score
                victim = frame

        return victim
```

### 4.5 竞态条件模拟（可选加分项）— 创新点 #5

展示 fork 在并发场景下的问题和解决方案：

```python
class RaceConditionDemo:
    """演示 fork 的竞态条件

    场景1：fork-bomb（进程爆炸）
    - 展示无限制 fork 会导致系统资源耗尽
    - 演示 ulimit 机制如何限制最大进程数

    场景2：竞争条件
    - 父子进程同时写同一文件（COW下是安全的）
    - 父子进程竞争 stdout（输出交错）
    - 演示 waitpid 如何解决同步问题

    场景3：僵尸进程堆积
    - 父进程不调用 waitpid
    - 展示 ZOMBIE 状态的 PCB 如何消耗资源
    - 演示 init 进程的兜底回收
    """

    @staticmethod
    def fork_bomb_demo(kernel, max_processes=50):
        """Fork bomb 演示，带安全限制"""
        print("[!] Fork Bomb 演示 - 展示资源限制机制")
        kernel.set_process_limit(max_processes)

        # 创建初始进程
        pid = kernel.create_process("fork_bomb")

        # 尝试无限 fork
        attempts = 0
        while True:
            result = kernel.sys_fork(pid)
            attempts += 1
            if result == -1:  # EAGAIN - 资源限制
                print(f"  [限制] 达到进程上限 {max_processes}，fork 被拒绝")
                print(f"  [统计] 尝试 {attempts} 次 fork，成功 {attempts-1} 次")
                break

    @staticmethod
    def zombie_demo(kernel):
        """僵尸进程堆积演示"""
        print("[!] 僵尸进程演示 - 展示资源回收机制")
        parent = kernel.create_process("lazy_parent")

        # 创建多个子进程但不 wait
        for i in range(5):
            child = kernel.sys_fork(parent)
            kernel.sys_exit(child, exit_code=i)

        # 此时子进程都是 ZOMBIE
        zombies = [p for p in kernel.get_children(parent)
                   if kernel.get_process(p).state == ProcessState.ZOMBIE]
        print(f"  [状态] {len(zombies)} 个僵尸进程等待回收")

        # 现在调用 waitpid
        for _ in zombies:
            kernel.sys_waitpid(parent, -1)
        print("  [恢复] 所有僵尸进程已被回收")
```

---

## 五、完整文件结构

```
process_management/
├── core/                        # 数据结构层
│   ├── pcb.py                  # PCB 进程控制块
│   ├── page_table.py           # 页表和页表项
│   ├── process_tree.py         # 进程树（父子关系）
│   └── virtual_memory.py       # 虚拟内存管理
│
├── kernel/                      # 内核核心层
│   ├── process_manager.py      # 进程创建/销毁/状态转换
│   ├── memory_manager.py       # COW 内存管理 + 帧分配
│   ├── scheduler.py            # Stride 调度器
│   └── resource_reaper.py      # 资源回收器（僵尸清理）
│
├── syscall/                     # 系统调用层
│   └── syscall.py              # sys_fork, sys_waitpid, sys_exit, sys_getpid
│
├── visualizer/                  # 可视化引擎
│   ├── tree_view.py            # 进程树可视化（ASCII + 图形）
│   ├── scheduler_view.py       # 调度甘特图
│   ├── memory_view.py          # 内存页表可视化
│   └── dashboard.py            # 实时仪表盘
│
├── demos/                       # 演示脚本
│   ├── basic_fork.py           # 基础 fork/wait 演示
│   ├── cow_demo.py             # COW 写时复制演示
│   ├── stride_demo.py          # Stride 调度公平性演示
│   ├── zombie_demo.py          # 僵尸进程演示
│   ├── orphan_demo.py          # 孤儿进程回收演示
│   └── race_condition.py       # 竞态条件演示
│
├── tests/                       # 测试
│   ├── test_fork.py
│   ├── test_cow.py
│   ├── test_scheduler.py
│   └── test_process_tree.py
│
├── main.py                      # 主程序入口
├── interactive.py               # 交互式 shell
└── README.md
```

---

## 六、交互式 Shell 设计

```python
class OSShell:
    """交互式操作系统 Shell

    命令列表：
      fork [name]         - 创建子进程
      wait [pid]          - 等待子进程退出（-1=任意）
      exit [code]         - 终止当前进程
      pid                 - 显示当前进程PID
      ps                  - 列出所有进程
      tree                - 显示进程树
      sched               - 显示调度队列状态
      mem                 - 显示内存页表
      nice [pid] [val]    - 调整优先级
      demo [name]         - 运行演示脚本
      stat [pid]          - 显示进程统计信息
      kill [pid]          - 强制杀死进程
      help                - 显示帮助
      quit                - 退出模拟器
    """

    def run(self):
        while True:
            pid = self.kernel.current_pid
            prompt = f"[PID:{pid}] os> "
            cmd = input(prompt).strip()
            self.execute(cmd)
```

---

## 七、可视化方案

### 7.1 进程树可视化

```
进程树状态 (T=15)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
init (PID=0) [RUNNING]
├── shell (PID=1) [READY]
│   ├── editor (PID=3) [RUNNING]  ← 当前进程
│   └── compiler (PID=5) [SLEEPING]
│       └── linker (PID=7) [ZOMBIE] ⚠️
└── daemon (PID=2) [READY]
    └── worker (PID=4) [READY]

统计: 运行=1 就绪=3 阻塞=1 僵尸=1 总计=6
```

### 7.2 Stride 调度甘特图

```
Stride 调度甘特图 (priority: A=10, B=5, C=5)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
T:  0  1  2  3  4  5  6  7  8  9  10 11 12 13 14
A: ██ ██    ██    ██    ██    ██    ██    ██
B:       ██       ██       ██       ██
C:             ██       ██       ██       ██

公平性: A:40% B:30% C:30% (priority比例 2:1:1) ✓
```

### 7.3 COW 内存页表

```
COW 内存状态 (T=10, fork后)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
物理帧分配:
  帧0: [PAGE: shell.code]     ref=1  dirty=0
  帧1: [PAGE: shell.data]     ref=2  dirty=1  ← COW共享 (父+子)
  帧2: [PAGE: editor.code]    ref=1  dirty=0
  帧3: [PAGE: editor.heap]    ref=1  dirty=1
  帧4: [PAGE: compiler.code]  ref=1  dirty=0
  ...
  空闲帧: 240/256 (93.75%)

COW 统计:
  共享帧: 12    脏帧: 3    总COW触发: 5次
  内存节省: 48KB (相比完全复制)
```

---

## 八、演示场景设计（比赛展示用）

### 场景1：基础 fork/wait 流程
```
$ demo basic_fork
创建父进程 (PID=1)
  父进程 fork 子进程 (PID=2)
  子进程开始执行 (PID=2)
  子进程退出 (exit_code=42)
  父进程 waitpid 回收子进程
  父进程获得子进程退出码: 42
✓ 基础流程验证通过
```

### 场景2：COW 写时复制效率
```
$ demo cow
创建父进程，分配 4 页内存 (16KB)
  fork 前: 物理内存占用 = 16KB
  执行 fork...
  fork 后: 物理内存占用 = 16KB (COW: 零拷贝！)
  子进程写入第 1 页...
  COW 触发: 复制帧 0 → 帧 4
  写入后: 物理内存占用 = 20KB (仅多 4KB)
  对比完全复制: 32KB
  内存节省: 37.5%
✓ COW 效率验证通过
```

### 场景3：Stride 调度公平性
```
$ demo stride
创建 3 个进程: A(priority=10), B(priority=5), C(priority=5)
  运行 20 个时间片...
  结果:
    A: cpu_time=10 (50%)  expected=50%  ✓
    B: cpu_time=5  (25%)  expected=25%  ✓
    C: cpu_time=5  (25%)  expected=25%  ✓
  公平性偏差: < 1% (理论最优)
✓ Stride 公平性验证通过
```

### 场景4：级联退出 + 孤儿回收
```
$ demo orphan
创建进程树: init → A → B → C
  杀死进程 A (PID=2)
  [级联退出] A 变为 ZOMBIE
  [孤儿回收] B (PID=3) 重新挂到 init 下
  [孤儿回收] C (PID=4) 重新挂到 init 下
  [init 回收] init 清理 ZOMBIE 进程 A

最终进程树:
  init (PID=0)
  ├── B (PID=3) [READY]
  └── C (PID=4) [READY]
✓ 孤儿回收验证通过
```

---

## 九、分工建议（5人团队）

| 角色 | 人数 | 负责模块 | 关键文件 |
|------|------|----------|----------|
| **核心开发 A** | 1 | PCB + 进程管理器 + 系统调用 | `core/pcb.py`, `kernel/process_manager.py`, `syscall/syscall.py` |
| **核心开发 B** | 1 | COW 内存管理 + 帧分配器 | `core/page_table.py`, `core/virtual_memory.py`, `kernel/memory_manager.py` |
| **算法开发** | 1 | Stride 调度器 + 页面置换 | `kernel/scheduler.py`, `kernel/resource_reaper.py` |
| **可视化 + 演示** | 1 | 可视化引擎 + 演示脚本 | `visualizer/`, `demos/` |
| **整合 + 测试 + 文档** | 1 | 主程序 + Shell + 测试 + README | `main.py`, `interactive.py`, `tests/`, `README.md` |

---

## 十、开发时间线（2周）

### 第1周：核心实现
| 天 | 任务 |
|----|------|
| D1 | 项目搭建 + PCB + 进程状态机 |
| D2 | 进程管理器 (create/destroy/transition) |
| D3 | COW 内存管理 + 帧分配器 |
| D4 | sys_fork + sys_exit 实现 |
| D5 | sys_waitpid + 进程树 + 孤儿回收 |
| D6 | Stride 调度器实现 |
| D7 | 整合测试：fork/wait/exit 完整流程 |

### 第2周：创新+演示
| 天 | 任务 |
|----|------|
| D8 | 可视化引擎 (进程树 + 甘特图) |
| D9 | 智能页面置换 + COW 优化 |
| D10 | 交互式 Shell |
| D11 | 演示脚本 (6个场景) |
| D12 | 竞态条件演示 + 边界测试 |
| D13 | README + 文档 + 演练 |
| D14 | 最终调试 + 比赛准备 |

---

## 十一、技术依赖

```python
# 必需
python = ">=3.8"

# 可选（增强可视化）
rich = ">=13.0"        # 终端美化（表格、树形、进度条）
matplotlib = ">=3.5"   # 甘特图、统计图表
numpy = ">=1.21"       # 数值计算
```

---

## 十二、评分对标

| 评分维度 | 本项目如何得分 |
|----------|---------------|
| **功能完整性** | fork + waitpid + exit + getpid 全部实现，含错误处理 |
| **算法创新** | COW（引用计数+脏页追踪）、Stride（公平调度）、双因子页面置换 |
| **代码质量** | 分层架构、类型注解、完整测试 |
| **演示效果** | 6个场景演示、实时可视化、交互式Shell |
| **文档质量** | 架构图、算法证明、流程图 |

### 差异化优势（vs 其他团队）

1. **COW 不是简化版** — 真正的引用计数 + 按需复制，不是"假装复制"
2. **Stride 不是 MLFQ** — 有数学公平性证明，更高级
3. **完整的进程生命周期** — 从 NEW → RUNNING → ZOMBIE → TERMINATED，含孤儿回收
4. **交互式演示** — 不是"运行一次看结果"，而是可以实时操作
5. **竞态条件演示** — 展示对 OS 并发问题的理解
