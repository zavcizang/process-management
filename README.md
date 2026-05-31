# 进程管理模拟器

操作系统校赛 — 内核实现赛道

## 项目简介

一个用户态的进程管理模拟器，实现了完整的进程生命周期管理：

- **fork** — 基于写时复制（COW）的进程创建
- **waitpid** — 子进程回收与阻塞等待
- **exit** — 级联退出与孤儿进程回收
- **getpid** — 进程标识查询

### 核心创新

| 特性 | 说明 |
|------|------|
| **COW 写时复制** | 引用计数 + 脏页追踪 + 按需复制，fork 时零内存拷贝 |
| **Stride 调度** | 基于 Linux CFS 的公平调度算法，有严格的数学公平性证明 |
| **级联退出** | 完整的三阶段退出协议，含孤儿进程自动回收 |
| **智能页面置换** | LFU + 访问时间的双因子策略，动态调整权重 |
| **实时可视化** | 进程树 + 甘特图 + 内存页表三合一动画 |

## 快速开始

### 环境要求

- Python 3.8+
- Git

### 安装

```bash
# 克隆项目
git clone git@gitee.com:zjh3432512933/process-management.git
cd process-management

# 安装依赖
pip install -r requirements.txt
```

### 运行

```bash
# 交互式 Shell
python main.py

# 运行演示
python demos/basic_fork.py
python demos/cow_demo.py
python demos/stride_demo.py
python demos/zombie_demo.py
python demos/orphan_demo.py
```

### 测试

```bash
python -m pytest tests/ -v
```

## 项目结构

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
│   ├── tree_view.py            # 进程树可视化
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
├── interactive.py               # 交互式 Shell
├── interfaces.py                # 接口定义（所有人必须遵循）
└── error_codes.py               # 错误码定义
```

## 交互式命令

```
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
```

## 算法详解

### COW 写时复制

```
fork 时：
  父进程页表 → [帧0, 帧1, 帧2]
  子进程页表 → [帧0, 帧1, 帧2]  ← 共享同一份物理内存
  帧0 引用计数 = 2
  帧1 引用计数 = 2
  帧2 引用计数 = 2
  总物理内存 = 12KB（而不是 24KB）

子进程写入帧0 时：
  触发 COW → 复制帧0 → 帧3
  子进程页表 → [帧3, 帧1, 帧2]
  帧0 引用计数 = 1
  帧3 引用计数 = 1
  总物理内存 = 16KB（只多了 4KB）
```

### Stride 调度

```
BIG_STRIDE = 1,000,000
stride = BIG_STRIDE / priority

进程A: priority=10 → stride=100,000
进程B: priority=5  → stride=200,000

调度规则：选 pass_value 最小的进程运行
运行后：pass_value += stride

结果：A 获得 2x CPU 时间（priority 比例 2:1）
```

## 开发团队

| 角色 | 负责模块 |
|------|----------|
| A | PCB + 进程树 |
| B | COW 内存管理 |
| C | Stride 调度器 |
| D | 系统调用层 |
| E | 可视化 + 演示 |

## 许可证

本项目为操作系统课程校赛作品。
