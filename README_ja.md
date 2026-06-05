# StrideCOWScheduler — プロセス管理カーネルシミュレータ

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

</div>

---

**OSコンペティション · カーネル実装トラック**

## 概要

StrideCOWSchedulerは、Linuxカーネルのプロセス管理メカニズムをPure Pythonで忠実に再現した**ユーザー空間カーネルシミュレータ**です。

### コア機能

| 機能 | 説明 | Linux対応 |
|------|------|-----------|
| **COW Copy-On-Write** | fork時のゼロコピーメモリ、参照計数+ダーティページ追跡+オンデマンド複製 | `copy_on_write()` |
| **Stride スケジューリング** | Linux CFSの数学的基礎に基づく公平スケジューリング | CFSスケジューラ |
| **パイプ IPC** | 4KBバッファの単向パイプ、ファイルディスクリプタ継承 | `sys_pipe()` |
| **カスケード退出** | 3フェーズ退出プロトコル、オーファンプロセス回収 | `do_exit()` |

### 実装済みシステムコール

| システムコール | 機能 | 本物のカーネル |
|---------------|------|----------------|
| **fork** | 子プロセス作成（COWベース） | `sys_fork()` |
| **waitpid** | 子プロセスの終了待ち | `sys_waitpid()` |
| **exit** | プロセス終了（カスケード退出+オーファン回収） | `sys_exit()` |
| **getpid** | 現在のプロセスID取得 | `sys_getpid()` |

### アーキテクチャ

```
┌─────────────────────────────────────────────────────────┐
│           ユーザー対話層 (CLI/TUI)                        │
├─────────────────────────────────────────────────────────┤
│           可視化エンジン (visualizer/)                    │
├─────────────────────────────────────────────────────────┤
│           システムコール層 (syscall/)                     │
├─────────────────────────────────────────────────────────┤
│           カーネルコア層 (kernel/)                        │
├─────────────────────────────────────────────────────────┤
│           データ構造層 (core/)                            │
└─────────────────────────────────────────────────────────┘
```

## クイックスタート

```bash
git clone git@gitee.com:zjh3432512933/process-management.git
cd process-management
python main.py          # インタラクティブシェル
python main.py --test   # 全テスト実行
```

## インタラクティブコマンド

```
fork [name]         子プロセス作成
wait [pid]          子プロセス終了待ち
exit [code]         プロセス終了
ps                  全プロセス一覧
tree                プロセスツリー表示
pipe                パイプ作成
sched               スケジューラ状態表示
mem                 メモリページテーブル表示
dmesg               カーネルログ表示
```

## ライセンス

[Apache License 2.0](LICENSE)
