# ProcMgrSim - 进程管理模拟器

<div align="center">

[![简体中文](https://img.shields.io/badge/🇨🇳-简体中文-blueviolet?style=flat-square)](README.md)
[![繁體中文](https://img.shields.io/badge/🇭🇰-繁體中文-orange?style=flat-square)](README_zh-TW.md)
[![English](https://img.shields.io/badge/🇺🇸-English-blue?style=flat-square)](README_en.md)
[![日本語](https://img.shields.io/badge/🇯🇵-日本語-red?style=flat-square)](README_ja.md)
[![한국어](https://img.shields.io/badge/🇰🇷-한국어-green?style=flat-square)](README_ko.md)

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-Apache_2.0-blue?style=for-the-badge)
![Tests](https://img.shields.io/badge/Tests-40%2B-brightgreen?style=for-the-badge)
![LOC](https://img.shields.io/badge/Code-5000%2B%20lines-gray?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey?style=for-the-badge)
![Gitee](https://img.shields.io/badge/Gitee-Zavci-red?style=for-the-badge&logo=gitee&logoColor=white)

</div>

---

**操作系统校赛 · 内核实现赛道**

## 项目简介

### 背景

操作系统是计算机系统的核心，而进程管理是操作系统最核心的功能之一。
本项目实现了一个进程管理内核模拟器，完整模拟了 Linux 内核的进程管理机制，
包括进程创建、调度、通信、回收等全生命周期管理。

### 项目定位

ProcMgrSim 是一个**用户态内核模拟器**，在 Python 中完整还原了 Linux 内核的进程管理机制：

1. COW 写时复制——fork 时零内存拷贝，引用计数 + 脏页追踪 + 按需复制
2. Stride 公平调度——基于 Linux CFS 的数学基础，O(log n) 最小堆调度
3. 管道 IPC——单向管道，4KB 缓冲区，文件描述符继承
4. 完整生命周期——六状态机 + 级联退出 + 孤儿回收 + Fork Bomb 防护

### 核心系统调用

本项目实现了操作系统最核心的 4 个系统调用：

| 系统调用 | 功能 | 对应真实内核 |
|----------|------|-------------|
| **fork** | 创建子进程（基于 COW 写时复制） | `sys_fork()` |
| **waitpid** | 等待子进程退出并回收资源 | `sys_waitpid()` |
| **exit** | 终止进程（含级联退出和孤儿回收） | `sys_exit()` |
| **getpid** | 获取当前进程 ID | `sys_getpid()` |

### 扩展功能

除了核心系统调用，还实现了以下内核机制：

| 功能 | 说明 | 对应真实内核 |
|------|------|-------------|
| **pipe** | 管道进程间通信，支持文件描述符继承 | `sys_pipe()` |
| **dmesg** | 内核日志系统，记录所有操作 | `/var/log/kmsg` |
| **Stride 调度** | 基于 Linux CFS 的公平调度算法 | CFS 调度器 |
| **COW 写时复制** | fork 时零内存拷贝，写入时按需复制 | `copy_on_write()` |
| **级联退出** | 三阶段退出协议，含孤儿进程回收 | `do_exit()` |

### 核心创新

| 创新点 | 技术细节 |
|--------|----------|
| **COW 写时复制** | 引用计数 + 脏页追踪 + 按需复制，fork 时零内存拷贝 |
| **Stride 调度** | 基于 Linux CFS 的数学基础，优先级比例精确可控 |
| **级联退出** | 完整的三阶段退出协议，含孤儿进程自动回收到 init |
| **管道 IPC** | 父子进程通过管道通信，支持文件描述符继承 |
| **内核日志** | 记录所有内核操作，支持 dmesg 命令回放 |
| **实时可视化** | 进程树 + 甘特图 + 内存映射 + 上下文切换时间线 |

### 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                   用户交互层 (CLI/TUI)                   │
│   命令: fork | wait | exit | ps | tree | pipe | dmesg   │
├─────────────────────────────────────────────────────────┤
│                  可视化引擎 (visualizer/)                │
│  进程树 | 甘特图 | 内存映射 | CPU利用率 | 上下文切换     │
├─────────────────────────────────────────────────────────┤
│                  系统调用层 (syscall/)                   │
│  sys_fork | sys_waitpid | sys_exit | sys_getpid         │
│  sys_pipe | sys_write | sys_read | sys_yield            │
├─────────────────────────────────────────────────────────┤
│                   内核核心层 (kernel/)                   │
│  进程管理器 | COW内存管理器 | Stride调度器 | IPC管理器   │
├─────────────────────────────────────────────────────────┤
│                   数据结构层 (core/)                     │
│  PCB | PageTable | ProcessTree | FrameManager           │
└─────────────────────────────────────────────────────────┘
```

### 项目数据

| 指标 | 数值 |
|------|------|
| 代码行数 | 5000+ 行 |
| 测试用例 | 40+ 个 |
| 演示脚本 | 6 个 |
| 交互命令 | 15+ 个 |
| 可视化图表 | 6 种 |

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

## 演示效果

```
============================================================
    进程管理模拟器 — 操作系统校赛作品
============================================================
  核心功能: fork + waitpid + exit + getpid
  创新特性: COW写时复制 | Stride公平调度 | 级联退出
  输入 help 查看命令列表
============================================================

[PID:0] os> fork shell
子进程已创建: PID=1

[PID:0] os> fork editor
子进程已创建: PID=2

[PID:0] os> ps
PID    PPID   名称           状态         优先级    CPU时间
------------------------------------------------------------
0      -1     init           READY        255      0.0      *
1      0      shell          RUNNING      128      5.0
2      0      editor         READY        128      0.0

  总计: 3 个进程

[PID:0] os> tree
进程树:
└── PID=0
    ├── PID=1
    └── PID=2

[PID:0] os> mem
内存状态:
  总帧数: 256 | 已使用: 4 | 空闲: 252
  共享帧: 0 | 页大小: 4096 字节

[PID:0] os> dmesg
[T=0] CREATE  pid=0 name=init parent=-1
[T=1] CREATE  pid=1 name=shell parent=0
[T=2] CREATE  pid=2 name=editor parent=0
共 3 条日志
```

## 常见问题

### Q: 运行时报 ModuleNotFoundError？

确保在项目根目录下运行：

```bash
cd process-management
python main.py
```

### Q: 中文显示乱码？

使用 VSCode 终端（推荐），或设置环境变量：

```bash
set PYTHONIOENCODING=utf-8
```

### Q: init 进程能被杀死吗？

不能。init 进程（PID=0）是所有进程的根，尝试杀死会提示"不能杀死 init 进程"。

### Q: 支持多核吗？

目前是单核模拟，每个时刻只运行一个进程。多核是后续扩展方向。

## 许可证

[Apache License 2.0](LICENSE)

## 开发工具

本项目使用 Claude Code 辅助代码调试、文档编写和测试用例生成。
