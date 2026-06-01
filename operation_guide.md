# 操作文档 — 进程管理模拟器使用指南

本文档面向使用者和评委，详细介绍如何运行和体验本项目。

---

## 一、环境准备

### 1.1 安装 Python

本项目需要 Python 3.8 或更高版本。

```bash
# 检查 Python 版本
python --version
```

### 1.2 克隆项目

```bash
git clone git@gitee.com:zjh3432512933/process-management.git
cd process-management
```

### 1.3 安装依赖（可选）

本项目无外部依赖，纯 Python 实现。可选安装 matplotlib 用于图表生成：

```bash
pip install -r requirements.txt
```

---

## 二、运行方式

### 2.1 交互式 Shell（推荐体验方式）

```bash
python main.py
```

启动后进入交互式 Shell，可以手动操作系统：

```
============================================================
    进程管理模拟器 — 操作系统校赛作品
============================================================
  核心功能: fork + waitpid + exit + getpid
  创新特性: COW写时复制 | Stride公平调度 | 级联退出
  输入 help 查看命令列表
============================================================
[PID:0] os>
```

### 2.2 运行演示脚本

```bash
# 基础 fork/wait 流程
python demos/basic_fork.py

# COW 写时复制效率演示
python demos/cow_demo.py

# Stride 调度公平性演示
python demos/stride_demo.py

# 僵尸进程演示
python demos/zombie_demo.py

# 孤儿进程回收演示
python demos/orphan_demo.py
```

### 2.3 运行测试

```bash
# 运行所有测试
python main.py --test

# 或单独运行某个测试
python tests/test_pcb.py
python tests/test_kernel.py
```

---

## 三、交互式命令详解

### 3.1 进程管理命令

#### fork [name] — 创建子进程

```
[PID:0] os> fork shell
子进程已创建: PID=1
```

父进程收到子进程的 PID，子进程自动加入就绪队列。

#### wait [pid] — 等待子进程退出

```
[PID:0] os> wait -1
子进程退出，exit_code=42
```

- `wait -1`：等待任意子进程退出
- `wait 1`：等待 PID=1 的子进程退出

如果子进程还未退出，父进程会阻塞等待。

#### exit [code] — 终止当前进程

```
[PID:1] os> exit 0
进程 1 已退出，exit_code=0
```

当前进程变为 ZOMBIE 状态，等待父进程回收。

#### kill <pid> — 强制杀死进程

```
[PID:0] os> kill 1
进程 1 已被杀死
```

### 3.2 信息查看命令

#### pid — 显示当前进程信息

```
[PID:1] os> pid
当前进程: PID=1
  名称: shell
  状态: RUNNING
  父进程: PID=0
```

#### ps — 列出所有进程

```
[PID:0] os> ps
PID    PPID   名称           状态         优先级    CPU时间
------------------------------------------------------------
0      -1     init           READY        255      0.0      *
1      0      shell          RUNNING      128      5.0
2      0      daemon         READY        128      0.0

  总计: 3 个进程
```

#### tree — 显示进程树

```
[PID:0] os> tree

进程树:
└── PID=0
    ├── PID=1
    │   └── PID=3
    └── PID=2
```

#### stat [pid] — 显示进程统计信息

```
[PID:0] os> stat 1

进程 1 统计:
  名称: shell
  状态: RUNNING
  父进程: PID=0
  子进程: [3]
  优先级: 128
  CPU时间: 5.0
  等待时间: 2.0
  上下文切换: 3
  缺页次数: 0
  COW复制: 0
```

### 3.3 调度和内存命令

#### sched — 显示调度队列状态

```
[PID:0] os> sched

调度队列:
PID      pass_value   优先级
------------------------------
2        4065.04      128
3        8130.08      128

统计:
  总时间片: 10
  调度次数: 8
  注册进程: 3
```

#### mem — 显示内存页表

```
[PID:0] os> mem

内存状态:
  总帧数: 256
  已使用: 4
  空闲: 252
  共享帧: 0
  页大小: 4096 字节
  总内存: 1.00 MB
  已使用: 0.02 MB

进程 1 的页表:
  页号     帧号     可写   脏页   引用
  ------------------------------------
     0        5     是     否        1
     1        8     是     否        1
```

#### nice <pid> <priority> — 调整优先级

```
[PID:0] os> nice 1 10
进程 1 优先级已设为 10
```

优先级范围：0-255，数值越小优先级越高。

### 3.4 时钟控制命令

#### tick [n] — 推进 n 个时钟周期

```
[PID:0] os> tick 10
已推进 10 个时钟周期，当前 tick=10
```

用于观察调度过程和进程状态变化。

#### demo <name> — 运行演示脚本

```
[PID:0] os> demo basic
[PID:0] os> demo cow
[PID:0] os> demo stride
[PID:0] os> demo zombie
[PID:0] os> demo orphan
```

---

## 四、典型使用场景

### 场景 1：体验 fork + waitpid 完整流程

```bash
python main.py
```

```
[PID:0] os> fork parent
子进程已创建: PID=1

[PID:0] os> tick 5
已推进 5 个时钟周期

[PID:0] os> ps
...

[PID:0] os> wait -1
子进程退出，exit_code=0

[PID:0] os> quit
```

### 场景 2：观察 COW 写时复制

```bash
python demos/cow_demo.py
```

输出会展示：
- fork 前内存占用
- fork 后零拷贝
- 写入时触发 COW
- 内存节省百分比

### 场景 3：验证 Stride 调度公平性

```bash
python demos/stride_demo.py
```

输出会展示：
- 3 个不同优先级进程
- 200 个时间片的调度结果
- CPU 时间比例（约 50%:25%:25%）
- 公平性验证结论

### 场景 4：观察僵尸进程

```bash
python demos/zombie_demo.py
```

输出会展示：
- 创建 5 个子进程
- 子进程退出但父进程不 wait
- 子进程变为 ZOMBIE
- 父进程调用 waitpid 回收

### 场景 5：观察孤儿进程回收

```bash
python demos/orphan_demo.py
```

输出会展示：
- 创建进程树 init → A → B → C
- 杀死进程 A
- B 和 C 成为孤儿
- 孤儿被重新挂到 init 下

---

## 五、测试验证

### 5.1 运行全部测试

```bash
python main.py --test
```

预期输出：

```
运行所有测试...

[PASS] test_pcb.py
[PASS] test_process_tree.py
[PASS] test_scheduler.py
[PASS] test_memory.py
[PASS] test_kernel.py
[PASS] test_visualizer.py

[DONE] 所有测试通过！
```

### 5.2 测试覆盖范围

| 测试文件 | 测试内容 |
|----------|----------|
| test_pcb.py | PCB 创建、状态转换合法性、reset、序列化 |
| test_process_tree.py | 进程树增删、父子关系、孤儿回收、可视化 |
| test_scheduler.py | Stride 调度、公平性验证、优先级调整、溢出处理 |
| test_memory.py | COW 零拷贝、写时复制触发、帧分配回收 |
| test_kernel.py | 内核初始化、fork+waitpid、级联退出、孤儿回收 |
| test_visualizer.py | 进程树/调度队列/内存页表可视化 |

---

## 六、常见问题

### Q: 运行时报错 ModuleNotFoundError

确保在项目根目录下运行：

```bash
cd process-management
python main.py
```

### Q: 中文显示乱码

Windows 控制台默认使用 GBK 编码，中文会显示为乱码。解决方法：

1. 使用 VS Code 终端（推荐）
2. 或在 Git Bash 中运行
3. 或设置环境变量：`set PYTHONIOENCODING=utf-8`

### Q: 如何退出交互式 Shell？

输入 `quit` 或按 `Ctrl+C`。

### Q: init 进程能被杀死吗？

不能。init 进程（PID=0）是所有进程的根，尝试杀死会提示"不能杀死 init 进程"。

---

## 七、技术架构

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

## 八、比赛演示建议

### 演示流程（5-10分钟）

1. **开场**（1分钟）
   - 介绍项目主题和核心功能
   - 展示项目结构

2. **交互式演示**（3-4分钟）
   - 启动交互式 Shell
   - 执行 fork、wait、exit 操作
   - 用 ps、tree 观察进程状态变化
   - 用 sched 观察调度队列

3. **COW 演示**（2分钟）
   - 运行 `python demos/cow_demo.py`
   - 解释零拷贝和写时复制原理
   - 展示内存节省效果

4. **Stride 调度演示**（2分钟）
   - 运行 `python demos/stride_demo.py`
   - 解释公平调度原理
   - 展示 CPU 时间比例

5. **总结**（1分钟）
   - 回顾创新点
   - 展示测试结果

### 演示技巧

- 使用 VS Code 终端（中文显示正常）
- 提前运行一遍演示确保无误
- 准备好解释每个算法的原理
- 用 `tick` 命令逐步展示调度过程
