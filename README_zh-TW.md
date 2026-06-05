# StrideCOWScheduler — 進程管理模擬器

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

</div>

---

**作業系統校賽 · 內核實作賽道**

## 專案簡介

### 背景

作業系統是電腦系統的核心，而進程管理是作業系統最核心的功能之一。
本專案實作了一個進程管理內核模擬器，完整模擬了 Linux 內核的進程管理機制，
包括進程建立、排程、通訊、回收等全生命週期管理。

### 專案定位

StrideCOWScheduler 是一個**使用者態內核模擬器**，在 Python 中完整還原了 Linux 內核的進程管理機制：

1. COW 寫時複製——fork 時零記憶體拷貝，引用計數 + 髒頁追蹤 + 按需複製
2. Stride 公平排程——基於 Linux CFS 的數學基礎，O(log n) 最小堆排程
3. 管道 IPC——單向管道，4KB 緩衝區，檔案描述符繼承
4. 完整生命週期——六狀態機 + 級聯退出 + 孤兒回收 + Fork Bomb 防護

### 核心系統呼叫

本專案實作了作業系統最核心的 4 個系統呼叫：

| 系統呼叫 | 功能 | 對應真實內核 |
|----------|------|-------------|
| **fork** | 建立子進程（基於 COW 寫時複製） | `sys_fork()` |
| **waitpid** | 等待子進程退出並回收資源 | `sys_waitpid()` |
| **exit** | 終止進程（含級聯退出與孤兒回收） | `sys_exit()` |
| **getpid** | 取得當前進程 ID | `sys_getpid()` |

### 擴充功能

| 功能 | 說明 | 對應真實內核 |
|------|------|-------------|
| **pipe** | 管道進程間通訊，支援檔案描述符繼承 | `sys_pipe()` |
| **dmesg** | 內核日誌系統，記錄所有操作 | `/var/log/kmsg` |
| **Stride 排程** | 基於 Linux CFS 的公平排程演算法 | CFS 排程器 |
| **COW 寫時複製** | fork 時零記憶體拷貝，寫入時按需複製 | `copy_on_write()` |
| **級聯退出** | 三階段退出協定，含孤兒進程回收 | `do_exit()` |

### 技術架構

```
┌─────────────────────────────────────────────────────────┐
│                 使用者互動層 (CLI/TUI)                    │
│   命令: fork | wait | exit | ps | tree | pipe | dmesg   │
├─────────────────────────────────────────────────────────┤
│                 視覺化引擎 (visualizer/)                 │
│  進程樹 | 甘特圖 | 記憶體映射 | CPU利用率 | 上下文切換   │
├─────────────────────────────────────────────────────────┤
│                 系統呼叫層 (syscall/)                     │
│  sys_fork | sys_waitpid | sys_exit | sys_getpid         │
├─────────────────────────────────────────────────────────┤
│                 內核核心層 (kernel/)                      │
│  進程管理器 | COW記憶體管理器 | Stride排程器 | IPC管理器  │
├─────────────────────────────────────────────────────────┤
│                 資料結構層 (core/)                        │
│  PCB | PageTable | ProcessTree | FrameManager           │
└─────────────────────────────────────────────────────────┘
```

### 專案數據

| 指標 | 數值 |
|------|------|
| 程式碼行數 | 5000+ 行 |
| 測試案例 | 40+ 個 |
| 演示腳本 | 6 個 |
| 互動命令 | 15+ 個 |
| 視覺化圖表 | 6 種 |

## 快速開始

### 環境需求

- Python 3.8+
- Git

### 安裝

```bash
git clone git@gitee.com:zjh3432512933/process-management.git
cd process-management
pip install -r requirements.txt
```

### 運行

```bash
python main.py              # 互動式 Shell
python main.py --test       # 運行所有測試
python demos/cow_demo.py    # 運行 COW 演示
```

## 互動式命令

```
--- 進程管理 ---
fork [name]         建立子進程
wait [pid]          等待子進程退出
exit [code]         終止當前進程
ps                  列出所有進程
tree                顯示進程樹

--- IPC（管道通訊）---
pipe                建立管道
write <fd> <data>   寫入管道
read <fd> [size]    讀取管道

--- 排程和記憶體 ---
sched               顯示排程佇列狀態
mem                 顯示記憶體頁表
nice [pid] [pri]    調整優先順序
```

## 演演效果

```
============================================================
    進程管理模擬器 — 作業系統校賽作品
============================================================
  核心功能: fork + waitpid + exit + getpid
  創新特性: COW寫時複製 | Stride公平排程 | 級聯退出
============================================================

[PID:0] os> fork shell
子進程已建立: PID=1

[PID:0] os> ps
PID    PPID   名稱           狀態         優先順序  CPU時間
------------------------------------------------------------
0      -1     init           READY        255       0.0      *
1      0      shell          RUNNING      128       5.0

[PID:0] os> tree
進程樹:
└── PID=0
    └── PID=1
```

## 常見問題

### Q: 運行時報 ModuleNotFoundError？

確保在專案根目錄下運行：`cd process-management && python main.py`

### Q: init 進程能被殺死嗎？

不能。init 進程（PID=0）是所有進程的根。

### Q: 支援多核嗎？

目前是單核模擬，多核是後續擴充方向。

## 授權條款

[Apache License 2.0](LICENSE)
