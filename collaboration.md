# 团队协作指南 — 5人如何用 AI 生成一致的代码

## 一、核心问题

5个人各用各的 AI 写代码，会出现：
- A 写的 PCB 有 `nice` 字段，B 写的没有
- C 调用 `scheduler.enqueue(pid)`，D 实现的是 `scheduler.add(pid)`
- 数据结构定义重复、命名冲突、接口不一致

**解法：先定契约，再写实现。**

---

## 二、协作架构

```
第1天（全员一起）          之后（各自独立开发）
─────────────────          ──────────────────────
interfaces.py   ────────►  A 按接口写 PCB
(Python Protocol)          B 按接口写 内存管理
     │                     C 按接口写 调度器
     ▼                     D 按接口写 系统调用
tests/                      E 按接口写 可视化
(测试用例=行为规范)    ────────►  所有人用同一套测试验证
```

---

## 三、Prompt 标准化方案

### 3.1 为什么需要标准 Prompt

每个人用 AI 的方式不同，生成的代码就不一致：
- 有人说"写一个PCB类"，AI 加了 `uid` 字段
- 有人说"实现PCB"，AI 用了 `NamedTuple` 而不是 `@dataclass`
- 有人说"写调度器"，AI 实现了 RR 而不是 Stride

**解法：Prompt 模板 + 共享上下文文件。**

### 3.2 标准 Prompt 模板

每个人写代码前，**必须**按这个格式发 prompt：

```markdown
## 角色
你是一个操作系统内核开发者，正在实现一个进程管理模拟器。

## 约束
1. 必须严格遵循 `interfaces.py` 中定义的所有接口
2. 必须使用 `pcb.py` 中定义的 PCB 类，不要自己重新定义
3. 必须通过 `tests/` 中的测试用例
4. 使用 Python 3.8+，类型注解
5. 中文注释，英文变量名

## 共享文件
以下是项目中已存在的核心文件，你的代码必须与它们兼容：

### interfaces.py（接口定义）
```python
[paste interfaces.py 内容]
```

### pcb.py（PCB 定义）
```python
[paste pcb.py 内容]
```

## 你的任务
[在这里写具体任务]

## 验收标准
[在这里写测试用例或验收条件]
```

### 3.3 各角色的标准 Prompt

#### A — PCB + 进程树

```markdown
## 你的任务
实现 `core/process_tree.py`，提供进程树管理功能。

## 接口要求
```python
class ProcessTree:
    def add_process(self, pid: int, ppid: int) -> None
    def remove_process(self, pid: int) -> None
    def get_children(self, pid: int) -> List[int]
    def reparent_orphans(self, dead_pid: int, new_parent: int) -> List[int]
    def visualize_ascii(self) -> str
```

## 验收测试
```python
def test_process_tree():
    tree = ProcessTree()
    tree.add_process(0, -1)  # init
    tree.add_process(1, 0)   # shell
    tree.add_process(2, 1)   # editor
    tree.add_process(3, 1)   # compiler

    assert tree.get_children(0) == [1]
    assert tree.get_children(1) == [2, 3]

    # 孤儿回收测试
    orphans = tree.reparent_orphans(1, 0)
    assert set(orphans) == {2, 3}
    assert tree.get_children(0) == [2, 3]
```
```

#### B — COW 内存管理

```markdown
## 你的任务
实现 `kernel/memory_manager.py`，包含 COW 写时复制和帧管理。

## 接口要求
```python
class FrameManager:
    def allocate(self) -> int           # 分配空闲帧，返回帧号
    def incref(self, frame: int)        # 增加引用计数
    def decref(self, frame: int)        # 减少引用计数，归零时回收
    def get_free_count(self) -> int     # 返回空闲帧数

class COWManager:
    def fork_page_table(self, parent_pt: PageTable) -> PageTable
    def on_page_write(self, pid: int, page_num: int) -> bool  # True=触发了COW
    def release_all_frames(self, pt: PageTable)
```

## 验收测试
```python
def test_cow_fork():
    fm = FrameManager(total_frames=16)
    cow = COWManager(fm)

    # 父进程分配2页
    parent_pt = PageTable()
    parent_pt.map(0, fm.allocate())
    parent_pt.map(1, fm.allocate())

    assert fm.get_free_count() == 14

    # fork — 应该零拷贝
    child_pt = cow.fork_page_table(parent_pt)
    assert fm.get_free_count() == 14  # 没有分配新帧！

    # 子进程写第0页 — 触发COW
    cow.on_page_write(child_pid, 0)
    assert fm.get_free_count() == 13  # 只复制了1页

    # 父进程写第1页 — 也触发COW
    cow.on_page_write(parent_pid, 1)
    assert fm.get_free_count() == 12
```
```

#### C — Stride 调度器

```markdown
## 你的任务
实现 `kernel/scheduler.py`，包含 Stride 公平调度算法。

## 接口要求
```python
class StrideScheduler:
    def __init__(self)

    def enqueue(self, pid: int) -> None
    def dequeue(self) -> Optional[int]     # 返回 pid 或 None
    def remove(self, pid: int) -> None
    def update_after_run(self, pid: int, ticks: int) -> None
    def set_priority(self, pid: int, priority: int) -> None
    def get_queue_snapshot(self) -> List[Tuple[int, float]]  # [(pid, pass_value)]
```

## 验收测试
```python
def test_stride_fairness():
    sched = StrideScheduler()

    # 注册3个进程，优先级比 2:1:1
    sched.set_priority(1, 10)  # 高优先级
    sched.set_priority(2, 5)   # 低优先级
    sched.set_priority(3, 5)   # 低优先级

    sched.enqueue(1)
    sched.enqueue(2)
    sched.enqueue(3)

    # 运行100个tick，统计每个进程的CPU时间
    cpu_count = {1: 0, 2: 0, 3: 0}
    for _ in range(100):
        pid = sched.dequeue()
        if pid:
            cpu_count[pid] += 1
            sched.update_after_run(pid, 1)
            sched.enqueue(pid)

    # A应该获得约50% CPU，B和C各约25%
    assert 45 <= cpu_count[1] <= 55  # ~50%
    assert 20 <= cpu_count[2] <= 30  # ~25%
    assert 20 <= cpu_count[3] <= 30  # ~25%
```
```

#### D — 系统调用层

```markdown
## 你的任务
实现 `syscall/syscall.py`，整合 PCB、内存、调度器、进程树。

## 接口要求
```python
class SyscallHandler:
    def __init__(self, kernel: 'Kernel')

    def sys_fork(self, parent_pid: int) -> int
    def sys_exit(self, pid: int, exit_code: int) -> None
    def sys_waitpid(self, pid: int, target: int = -1) -> Union[int, str]
    def sys_getpid(self, pid: int) -> int
    def sys_setpriority(self, pid: int, priority: int) -> None
    def sys_yield(self, pid: int) -> None
```

## 验收测试
```python
def test_fork_and_wait():
    kernel = Kernel()
    syscall = SyscallHandler(kernel)

    parent = kernel.create_process("parent")
    child = syscall.sys_fork(parent)

    assert child > 0
    assert kernel.get_process(child).ppid == parent

    syscall.sys_exit(child, 42)
    assert kernel.get_process(child).state == ProcessState.ZOMBIE

    result = syscall.sys_waitpid(parent, child)
    assert result == 42
    assert kernel.get_process(child).state == ProcessState.TERMINATED

def test_orphan_reparenting():
    kernel = Kernel()
    syscall = SyscallHandler(kernel)

    parent = kernel.create_process("parent")
    child = syscall.sys_fork(parent)
    grandchild = syscall.sys_fork(child)

    # 杀死中间进程
    syscall.sys_exit(child, 0)

    # 孤儿应该被挂到 init 下
    assert kernel.get_process(grandchild).ppid == 0  # init PID=0
    assert grandchild in kernel.process_tree.get_children(0)
```
```

#### E — 可视化 + 演示

```markdown
## 你的任务
实现 `visualizer/` 和 `demos/`。

## 你依赖的接口（只读，不要修改）
- kernel.get_all_processes() -> Dict[int, PCB]
- kernel.process_tree.visualize_ascii() -> str
- kernel.scheduler.get_queue_snapshot() -> List[Tuple[int, float]]
- kernel.memory_manager.get_frame_map() -> Dict[int, FrameInfo]

## 验收
运行 `demos/basic_fork.py` 后，终端应输出：
1. 进程树的 ASCII 可视化
2. 调度过程的甘特图
3. 内存页表状态
4. 统计数据（CPU利用率、公平性指标）
```
```

---

## 四、接口文件（第1天产出）

### 4.1 interfaces.py — 所有人的"宪法"

```python
"""
interfaces.py — 项目接口定义

规则：
1. 所有模块必须实现或调用这些接口
2. 接口只能由架构师(A)修改
3. 修改接口前必须通知全员
4. 所有接口都有对应的测试用例
"""

from typing import Protocol, Dict, List, Optional, Tuple, Union
from enum import Enum

# ─────────────────────────────────────────────
# 进程状态枚举
# ─────────────────────────────────────────────
class ProcessState(Enum):
    NEW = "NEW"
    READY = "READY"
    RUNNING = "RUNNING"
    SLEEPING = "SLEEPING"
    ZOMBIE = "ZOMBIE"
    TERMINATED = "TERMINATED"

# ─────────────────────────────────────────────
# PCB 接口
# ─────────────────────────────────────────────
class PCBInterface(Protocol):
    pid: int
    ppid: int
    name: str
    state: ProcessState

    # 调度
    priority: int           # 0-255, 越小越高
    stride: float           # BIG_STRIDE / priority
    pass_value: float       # 累计步长
    nice: int               # -20 ~ 19

    # 时间统计
    cpu_time: float
    wait_time: float
    arrival_time: float
    start_time: float

    # 内存
    page_table: object      # PageTable 类型
    memory_usage: int

    # 进程树
    children: List[int]
    exit_code: int
    wait_queue: List[int]

    # 统计
    page_faults: int
    cow_copies: int
    context_switches: int

    def reset(self) -> None: ...

# ─────────────────────────────────────────────
# 进程树接口（A 实现）
# ─────────────────────────────────────────────
class ProcessTreeInterface(Protocol):
    def add_process(self, pid: int, ppid: int) -> None: ...
    def remove_process(self, pid: int) -> None: ...
    def get_children(self, pid: int) -> List[int]: ...
    def reparent_orphans(self, dead_pid: int, new_parent: int) -> List[int]: ...
    def visualize_ascii(self) -> str: ...

# ─────────────────────────────────────────────
# 帧管理器接口（B 实现）
# ─────────────────────────────────────────────
class FrameManagerInterface(Protocol):
    def allocate(self) -> int: ...
    def incref(self, frame: int) -> None: ...
    def decref(self, frame: int) -> None: ...
    def get_free_count(self) -> int: ...
    def get_total_count(self) -> int: ...

# ─────────────────────────────────────────────
# COW 内存管理接口（B 实现）
# ─────────────────────────────────────────────
class COWManagerInterface(Protocol):
    def fork_page_table(self, parent_pt: object) -> object: ...
    def on_page_write(self, pid: int, page_num: int) -> bool: ...
    def release_all_frames(self, pt: object) -> None: ...

# ─────────────────────────────────────────────
# 调度器接口（C 实现）
# ─────────────────────────────────────────────
class SchedulerInterface(Protocol):
    def enqueue(self, pid: int) -> None: ...
    def dequeue(self) -> Optional[int]: ...
    def remove(self, pid: int) -> None: ...
    def update_after_run(self, pid: int, ticks: int) -> None: ...
    def set_priority(self, pid: int, priority: int) -> None: ...
    def get_queue_snapshot(self) -> List[Tuple[int, float]]: ...

# ─────────────────────────────────────────────
# 内核接口（D 实现，其他人调用）
# ─────────────────────────────────────────────
class KernelInterface(Protocol):
    def create_process(self, name: str, parent_pid: int = 0) -> int: ...
    def destroy_process(self, pid: int) -> None: ...
    def get_process(self, pid: int) -> Optional[PCBInterface]: ...
    def get_all_processes(self) -> Dict[int, PCBInterface]: ...
    def tick(self) -> None: ...

    # 进程树（只读访问）
    @property
    def process_tree(self) -> ProcessTreeInterface: ...

    # 调度器（只读访问）
    @property
    def scheduler(self) -> SchedulerInterface: ...

    # 内存管理（只读访问）
    @property
    def memory_manager(self) -> COWManagerInterface: ...

# ─────────────────────────────────────────────
# 系统调用接口（D 实现）
# ─────────────────────────────────────────────
class SyscallInterface(Protocol):
    def sys_fork(self, parent_pid: int) -> int: ...
    def sys_exit(self, pid: int, exit_code: int) -> None: ...
    def sys_waitpid(self, pid: int, target: int = -1) -> Union[int, str]: ...
    def sys_getpid(self, pid: int) -> int: ...
    def sys_setpriority(self, pid: int, priority: int) -> None: ...
    def sys_yield(self, pid: int) -> None: ...
```

### 4.2 错误码定义

```python
"""
error_codes.py — 系统调用错误码

所有 sys_* 函数在出错时返回对应错误码
"""

class ErrorCode:
    SUCCESS = 0
    ECHILD = -1      # 没有子进程
    EAGAIN = -2      # 资源限制，无法创建更多进程
    EINVAL = -3      # 无效参数
    ESRCH = -4       # 进程不存在
    ENOMEM = -5      # 内存不足
    EPERM = -6       # 权限不足（如 kill init）
    BLOCKED = "BLOCKED"  # waitpid 阻塞中
```

---

## 五、Git 工作流

### 5.1 分支策略

```
main                     ← 稳定版，随时能跑
├── feature/pcb          ← A 的分支
├── feature/memory       ← B 的分支
├── feature/scheduler    ← C 的分支
├── feature/syscall      ← D 的分支
└── feature/visualizer   ← E 的分支
```

### 5.2 提交规范

```
feat: 新功能
fix: 修 bug
test: 添加测试
docs: 文档
refactor: 重构（不改变行为）
```

示例：
```
feat: 实现 Stride 调度器基础功能
test: 添加 COW fork 测试用例
fix: 修复孤儿回收时 init 进程未被唤醒的问题
```

### 5.3 合并流程

```
1. 在自己分支开发
2. 跑测试：python -m pytest tests/ -v
3. 测试全绿 → push
4. 在群里发："请求合并 feature/xxx"
5. 至少 1 人 review（看 diff，跑测试）
6. Review 通过 → merge 到 main
7. 所有人 pull main
```

### 5.4 冲突预防

| 规则 | 说明 |
|------|------|
| **不要改别人的文件** | A 写 core/pcb.py，B 不要碰 |
| **不要改 interfaces.py** | 只有架构师可以改，且必须通知全员 |
| **import 别人的模块** | B 需要 PCB，直接 `from core.pcb import PCB` |
| **用 mock 测试** | D 的 syscall 测试可以 mock 调度器和内存管理器 |

---

## 六、进度追踪

### 6.1 飞书看板

| 列 | 含义 |
|----|------|
| **待做** | 还没开始的任务 |
| **进行中** | 正在开发 |
| **已完成** | 代码写完 + 测试通过 |
| **阻塞** | 等别人的接口/数据 |

### 6.2 每日站会模板（每晚 21:00，15分钟）

```markdown
## [姓名] 今日汇报

### 今日完成
- [x] PCB 类实现 + 测试通过
- [x] 进程树 add/remove 功能

### 遇到的阻塞
- 无 / 需要 B 的内存管理接口才能继续

### 明日计划
- [ ] 进程树 reparent_orphans
- [ ] 进程树可视化
```

### 6.3 接口变更通知模板

```markdown
## ⚠️ 接口变更通知

### 变更内容
`interfaces.py` 中 `KernelInterface` 新增方法：
```python
def get_process_count(self) -> int: ...
```

### 影响范围
- D（系统调用）：需要实现此方法
- E（可视化）：可以直接调用

### 需要做的事
请 D 在下次合并前实现此方法。
```

---

## 七、常见问题

### Q: A 的 PCB 改了字段，B/C/D 的代码全崩了怎么办？

**答**：interfaces.py 是契约。A 改 PCB 字段 = 改接口 = 必须通知全员 + 更新所有测试。不通知就改 = 罚请奶茶。

### Q: D 等 B 的内存管理，但 B 还没写完怎么办？

**答**：D 先用 mock 写测试：

```python
# D 先写一个假的内存管理器
class MockMemoryManager:
    def fork_page_table(self, pt):
        return PageTable()  # 返回空页表
    def on_page_write(self, pid, page_num):
        return False
    def release_all_frames(self, pt):
        pass

# 用 mock 跑测试
def test_fork():
    kernel = Kernel(memory_manager=MockMemoryManager())
    ...
```

等 B 写完后，换掉 mock 就行。

### Q: 5 个人的 AI 生成的代码风格不一样怎么办？

**答**：
1. 加 `pyproject.toml` 统一格式化规则（black + isort）
2. Prompt 模板里加"使用 black 格式化"
3. Review 时检查风格一致性

### Q: 谁负责集成？

**答**：D（系统调用层）天然就是集成者，因为 syscall 调用所有其他模块。D 的分支合并到 main 后，其他人 rebase 到最新 main。

---

## 八、第一天 Checklist

所有人聚在一起（线上/线下），花 2-3 小时完成：

- [ ] **确认 interfaces.py** — 全员审阅，无异议后提交
- [ ] **确认 error_codes.py** — 全员审阅
- [ ] **确认 PCB 字段** — A 负责，其他人确认够用
- [ ] **确认测试用例** — 每个模块至少 3 个测试
- [ ] **创建 Git 仓库** — GitHub/Gitee，5 人加为 collaborator
- [ ] **创建分支** — 每人创建自己的 feature 分支
- [ ] **建飞书群 + 看板** — 确认每日站会时间
- [ ] **确认 Prompt 模板** — 每人存一份，写代码前先贴模板

完成后，各自回家独立开发，每晚同步进度。
