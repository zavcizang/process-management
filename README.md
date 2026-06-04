# ProcMgrSim - 进程管理模拟器

操作系统校赛 — 内核实现赛道

## 项目简介

一个进程管理内核模拟器，实现了完整的进程生命周期管理和进程间通信：

### 核心系统调用
- **fork** — 基于写时复制（COW）的进程创建
- **waitpid** — 子进程回收与阻塞等待
- **exit** — 级联退出与孤儿进程回收
- **getpid** — 进程标识查询

### 扩展功能
- **pipe** — 管道进程间通信（IPC）
- **dmesg** — 内核日志系统
- **Stride 调度** — 基于 Linux CFS 的公平调度算法

### 核心创新

| 特性 | 说明 |
|------|------|
| **COW 写时复制** | 引用计数 + 脏页追踪 + 按需复制，fork 时零内存拷贝 |
| **Stride 调度** | 基于 Linux CFS 的公平调度算法，有严格的数学公平性证明 |
| **级联退出** | 完整的三阶段退出协议，含孤儿进程自动回收 |
| **管道 IPC** | 父子进程通过管道通信，支持文件描述符继承 |
| **内核日志** | 记录所有内核操作，支持 dmesg 命令回放 |
| **实时可视化** | 进程树 + 甘特图 + 内存映射 + 上下文切换时间线 |

## 快速开始

### 环境要求

- Python 3.8+
- Git

### 安装

```bash
# 克隆项目
git clone git@gitee.com:zjh3432512933/process-management.git
cd process-management

# 安装依赖（可选，本项目无外部依赖）
pip install -r requirements.txt
```

### 运行

```bash
# 交互式 Shell
python main.py

# 运行所有测试
python main.py --test

# 运行演示
python demos/basic_fork.py
python demos/cow_demo.py
python demos/stride_demo.py
python demos/zombie_demo.py
python demos/orphan_demo.py
python demos/pipe_demo.py
```

## 项目结构

```
process_management/
├── core/                        # 数据结构层
│   ├── __init__.py
│   ├── pcb.py                  # PCB 进程控制块
│   └── process_tree.py         # 进程树（父子关系）
│
├── kernel/                      # 内核核心层
│   ├── __init__.py
│   ├── kernel.py               # 内核核心（整合所有子系统）
│   ├── memory_manager.py       # COW 内存管理 + 帧分配
│   ├── process_manager.py      # 进程创建/销毁/状态转换
│   ├── scheduler.py            # Stride 调度器
│   ├── ipc.py                  # IPC 管道通信
│   └── logger.py               # 内核日志系统
│
├── syscall/                     # 系统调用层
│   ├── __init__.py
│   └── syscall.py              # fork/exit/waitpid/getpid/pipe/setpriority/yield
│
├── visualizer/                  # 可视化引擎
│   ├── __init__.py
│   ├── charts.py               # Matplotlib 图表（甘特图/CPU/内存/公平性/映射）
│   ├── dashboard.py            # 实时仪表盘
│   ├── memory_view.py          # 内存页表可视化
│   ├── scheduler_view.py       # 调度甘特图
│   └── tree_view.py            # 进程树可视化
│
├── demos/                       # 演示脚本
│   ├── __init__.py
│   ├── basic_fork.py           # 基础 fork/wait 演示
│   ├── cow_demo.py             # COW 写时复制演示
│   ├── orphan_demo.py          # 孤儿进程回收演示
│   ├── pipe_demo.py            # 管道 IPC 演示
│   ├── stride_demo.py          # Stride 调度公平性演示
│   └── zombie_demo.py          # 僵尸进程演示
│
├── tests/                       # 测试（40+ 测试用例）
│   ├── __init__.py
│   ├── test_kernel.py          # 内核集成测试
│   ├── test_memory.py          # 内存管理器测试
│   ├── test_pcb.py             # PCB 单元测试
│   ├── test_process_tree.py    # 进程树测试
│   ├── test_scheduler.py       # 调度器测试
│   └── test_visualizer.py      # 可视化测试
│
├── main.py                      # 主程序入口
├── interactive.py               # 交互式 Shell
├── interfaces.py                # 接口定义（Protocol）
├── error_codes.py               # 错误码定义
├── requirements.txt             # Python 依赖
├── README.md                    # 本文件
├── operation_guide.md           # 操作文档
├── plan.md                      # 技术方案
├── collaboration.md             # 团队协作指南
└── gitee_guide.md               # Gitee 使用指南
```

## 交互式命令

```
--- 进程管理 ---
fork [name]         - 创建子进程
wait [pid]          - 等待子进程退出（-1=任意）
exit [code]         - 终止当前进程
pid                 - 显示当前进程PID
ps                  - 列出所有进程
tree                - 显示进程树
stat [pid]          - 显示进程统计信息
kill [pid]          - 强制杀死进程

--- IPC（管道通信）---
pipe                - 创建管道
write <fd> <data>   - 写入管道
read <fd> [size]    - 读取管道
fd [pid]            - 查看文件描述符

--- 调度和内存 ---
sched               - 显示调度队列状态
mem                 - 显示内存页表
nice [pid] [pri]    - 调整优先级

--- 工具 ---
tick [n]            - 推进 n 个时钟周期
dmesg               - 查看内核日志
chart [type]        - 生成图表 (all/gantt/cpu/memory/stride/switch/mapping)
demo [name]         - 运行演示脚本

--- 系统 ---
help                - 显示帮助
quit / q            - 退出模拟器
```

## 算法详解

### COW 写时复制

```
fork 时：
  父进程页表 → [帧0, 帧1, 帧2]
  子进程页表 → [帧0, 帧1, 帧2]  ← 共享同一份物理内存
  帧0 引用计数 = 2
  总物理内存 = 12KB（而不是 24KB）

子进程写入帧0 时：
  触发 COW → 复制帧0 → 帧3
  子进程页表 → [帧3, 帧1, 帧2]
  帧0 引用计数 = 1
  总物理内存 = 16KB（只多了 4KB）
```

### Stride 调度

```
stride = BIG_STRIDE / (256 - priority)

进程A: priority=10  → stride=4065（小步长，多CPU）
进程B: priority=133 → stride=8130（大步长，少CPU）

调度规则：选 pass_value 最小的进程运行
运行后：pass_value += stride

结果：A 获得 50% CPU，B 获得 25% CPU（2:1 比例）
```

### 级联退出

```
进程树：init → A → B → C

A 退出时：
  1. A 状态变为 ZOMBIE
  2. B 成为孤儿，重新挂到 init 下
  3. C 的父进程仍然是 B
  4. 如果 A 的父进程在 wait，唤醒它
```

## 测试覆盖

| 测试文件 | 测试内容 | 测试数量 |
|----------|----------|----------|
| test_pcb.py | PCB 创建、状态转换、reset | 6 |
| test_process_tree.py | 进程树、孤儿回收、可视化 | 10 |
| test_scheduler.py | Stride 调度、公平性、溢出 | 7 |
| test_memory.py | COW、帧分配、引用计数 | 8 |
| test_kernel.py | 内核集成、fork+waitpid、级联退出 | 9 |
| test_visualizer.py | 可视化组件 | 8 |

## 开发团队

| 姓名 | 角色 | 负责模块 |
|------|------|----------|
| zavci | 架构师 | 项目架构、核心模块实现、系统调用、IPC、可视化、测试、文档 |
| [队友1] | 开发 | 后续负责模块 |
| [队友2] | 开发 | 后续负责模块 |
| [队友3] | 开发 | 后续负责模块 |
| [队友4] | 开发 | 后续负责模块 |

## 许可证

本项目为操作系统课程校赛作品，仅供学习交流使用。

### 开发工具

本项目使用 Claude Code 辅助代码调试、文档编写和测试用例生成。
