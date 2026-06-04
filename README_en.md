# ProcMgrSim — Process Management Kernel Simulator

<div align="center">

[![中文](https://img.shields.io/badge/🇨🇳-中文-blueviolet?style=flat-square)](README.md)
[![English](https://img.shields.io/badge/🇺🇸-English-blue?style=flat-square)](README_en.md)

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-Apache_2.0-blue?style=for-the-badge)
![Tests](https://img.shields.io/badge/Tests-40%2B-brightgreen?style=for-the-badge)
![LOC](https://img.shields.io/badge/Code-5000%2B%20lines-gray?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey?style=for-the-badge)

</div>

---

**Operating System Competition · Kernel Implementation Track**

## Overview

ProcMgrSim is a **user-space kernel simulator** that faithfully reproduces Linux kernel process management mechanisms in pure Python — including process creation, scheduling, communication, and lifecycle management.

### Core Features

| Feature | Description | Linux Counterpart |
|---------|-------------|-------------------|
| **COW Copy-On-Write** | Zero-copy fork with reference counting + dirty page tracking + on-demand replication | `copy_on_write()` |
| **Stride Scheduling** | Fair scheduling based on Linux CFS mathematical foundation, O(log n) min-heap | CFS Scheduler |
| **Pipe IPC** | Unidirectional pipe with 4KB buffer, file descriptor inheritance | `sys_pipe()` |
| **Cascade Exit** | Three-phase exit protocol with orphan process reclamation to init | `do_exit()` |

### System Calls Implemented

| Syscall | Function | Real Kernel |
|---------|----------|-------------|
| **fork** | Create child process (COW-based) | `sys_fork()` |
| **waitpid** | Wait for child process exit | `sys_waitpid()` |
| **exit** | Terminate process (cascade exit + orphan recovery) | `sys_exit()` |
| **getpid** | Get current process ID | `sys_getpid()` |

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│              User Interaction Layer (CLI/TUI)            │
│   Commands: fork | wait | exit | ps | tree | pipe       │
├─────────────────────────────────────────────────────────┤
│              Visualization Engine (visualizer/)          │
│  Process Tree | Gantt Chart | Memory Map | CPU Usage    │
├─────────────────────────────────────────────────────────┤
│              System Call Layer (syscall/)                │
│  sys_fork | sys_waitpid | sys_exit | sys_getpid         │
├─────────────────────────────────────────────────────────┤
│              Kernel Core Layer (kernel/)                 │
│  ProcessManager | COWManager | StrideScheduler | IPC    │
├─────────────────────────────────────────────────────────┤
│              Data Structure Layer (core/)                │
│  PCB | PageTable | ProcessTree | FrameManager           │
└─────────────────────────────────────────────────────────┘
```

### Project Stats

| Metric | Value |
|--------|-------|
| Lines of Code | 5000+ |
| Test Cases | 40+ |
| Demo Scripts | 6 |
| Shell Commands | 15+ |
| Visualizations | 6 types |

## Quick Start

### Prerequisites

- Python 3.8+
- Git

### Installation

```bash
git clone git@gitee.com:zjh3432512933/process-management.git
cd process-management

# Optional: install dependencies (no external deps required)
pip install -r requirements.txt
```

### Run

```bash
# Interactive Shell
python main.py

# Run all tests
python main.py --test

# Run demos
python demos/basic_fork.py
python demos/cow_demo.py
python demos/stride_demo.py
python demos/pipe_demo.py
```

## Project Structure

```
process_management/
├── core/                    # Data Structure Layer
│   ├── pcb.py              # Process Control Block
│   └── process_tree.py     # Process Tree (parent-child)
├── kernel/                  # Kernel Core Layer
│   ├── kernel.py           # Kernel (orchestrates all subsystems)
│   ├── memory_manager.py   # COW Memory Manager + Frame Allocation
│   ├── process_manager.py  # Process Create/Destroy/State Transition
│   ├── scheduler.py        # Stride Scheduler
│   ├── ipc.py              # IPC Pipe Communication
│   └── logger.py           # Kernel Logger
├── syscall/                 # System Call Layer
│   └── syscall.py          # fork/exit/waitpid/getpid/pipe
├── visualizer/              # Visualization Engine
│   ├── charts.py           # Matplotlib Charts
│   ├── dashboard.py        # Real-time Dashboard
│   ├── memory_view.py      # Memory Page Table View
│   ├── scheduler_view.py   # Scheduler Gantt Chart
│   └── tree_view.py        # Process Tree View
├── demos/                   # Demo Scripts (6 demos)
├── tests/                   # Tests (40+ cases)
├── main.py                  # Entry Point
└── interactive.py           # Interactive Shell
```

## Interactive Commands

```
--- Process Management ---
fork [name]         Create child process
wait [pid]          Wait for child exit (-1=any)
exit [code]         Terminate current process
pid                 Show current process PID
ps                  List all processes
tree                Show process tree
stat [pid]          Show process statistics

--- IPC (Pipe) ---
pipe                Create pipe
write <fd> <data>   Write to pipe
read <fd> [size]    Read from pipe

--- Scheduling & Memory ---
sched               Show scheduler queue status
mem                 Show memory page table
nice [pid] [pri]    Adjust priority

--- Utilities ---
tick [n]            Advance n clock cycles
dmesg               View kernel log
demo [name]         Run demo script
```

## Algorithms

### COW Copy-On-Write

```
Before fork:
  Parent page table → [frame0, frame1, frame2]
  frame0 ref_count = 1

After fork:
  Parent page table → [frame0, frame1, frame2]  ← shared
  Child page table  → [frame0, frame1, frame2]  ← shared
  frame0 ref_count = 2
  Total memory = 12KB (not 24KB)

After child writes to frame0:
  COW triggered → copy frame0 → frame3
  Child page table → [frame3, frame1, frame2]
  frame0 ref_count = 1
  Total memory = 16KB (only 4KB extra)
```

### Stride Scheduling

```
stride = BIG_STRIDE / (256 - priority)

Process A: priority=10  → stride=4065 (small stride, more CPU)
Process B: priority=133 → stride=8130 (large stride, less CPU)

Rule: always run the process with the smallest pass_value
After running: pass_value += stride

Result: A gets 50% CPU, B gets 25% CPU (2:1 ratio)
```

## Test Coverage

| Test File | Coverage | Cases |
|-----------|----------|-------|
| test_pcb.py | PCB creation, state transitions, reset | 6 |
| test_process_tree.py | Process tree, orphan recovery | 10 |
| test_scheduler.py | Stride scheduling, fairness, overflow | 7 |
| test_memory.py | COW, frame allocation, ref counting | 8 |
| test_kernel.py | Kernel integration, fork+waitpid | 9 |
| test_visualizer.py | Visualization components | 8 |

## Demo Output

```
============================================================
    Process Management Simulator — OS Competition
============================================================
  Core: fork + waitpid + exit + getpid
  Features: COW | Stride Scheduling | Cascade Exit
  Type 'help' for command list
============================================================

[PID:0] os> fork shell
Child created: PID=1

[PID:0] os> ps
PID    PPID   NAME           STATE        PRIORITY  CPU_TIME
------------------------------------------------------------
0      -1     init           READY        255       0.0      *
1      0      shell          RUNNING      128       5.0

[PID:0] os> tree
Process Tree:
└── PID=0
    └── PID=1
```

## FAQ

### Q: ModuleNotFoundError on run?

Run from the project root directory:

```bash
cd process-management
python main.py
```

### Q: Can init process be killed?

No. init (PID=0) is the root of all processes. Attempting to kill it returns an error.

### Q: Multi-core support?

Currently single-core simulation. Multi-core is a planned extension.

## License

[Apache License 2.0](LICENSE)

## Development

Built with Claude Code for code debugging, documentation, and test generation.
