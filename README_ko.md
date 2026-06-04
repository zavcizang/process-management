# ProcMgrSim — 프로세스 관리 커널 시뮬레이터

<div align="center">

[![简体中文](https://img.shields.io/badge/🇨🇳-简体中文-blueviolet?style=flat-square)](README.md)
[![繁體中文](https://img.shields.io/badge/🇹🇼-繁體中文-orange?style=flat-square)](README_zh-TW.md)
[![English](https://img.shields.io/badge/🇺🇸-English-blue?style=flat-square)](README_en.md)
[![日本語](https://img.shields.io/badge/🇯🇵-日本語-red?style=flat-square)](README_ja.md)
[![한국어](https://img.shields.io/badge/🇰🇷-한국어-green?style=flat-square)](README_ko.md)

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-Apache_2.0-blue?style=for-the-badge)
![Tests](https://img.shields.io/badge/Tests-40%2B-brightgreen?style=for-the-badge)
![LOC](https://img.shields.io/badge/Code-5000%2B%20lines-gray?style=for-the-badge)

</div>

---

**OS 경진대회 · 커널 구현 트랙**

## 개요

ProcMgrSim은 Linux 커널의 프로세스 관리 메커니즘을 Pure Python으로 완벽히 재현한 **유저空间 커널 시뮬레이터**입니다.

### 핵심 기능

| 기능 | 설명 | Linux 대응 |
|------|------|------------|
| **COW Copy-On-Write** | fork 시 제로 카피 메모리, 참조 카운트 + 더티 페이지 추적 | `copy_on_write()` |
| **Stride 스케줄링** | Linux CFS 수학적 기반의 공정 스케줄링 | CFS 스케줄러 |
| **파이프 IPC** | 4KB 버퍼 단방향 파이프, 파일 디스크립터 상속 | `sys_pipe()` |
| **캐스케이드 종료** | 3단계 종료 프로토콜, 고아 프로세스 회수 | `do_exit()` |

### 구현된 시스템 호출

| 시스템 호출 | 기능 | 실제 커널 |
|-------------|------|-----------|
| **fork** | 자식 프로세스 생성 (COW 기반) | `sys_fork()` |
| **waitpid** | 자식 프로세스 종료 대기 | `sys_waitpid()` |
| **exit** | 프로세스 종료 (캐스케이드 + 고아 회수) | `sys_exit()` |
| **getpid** | 현재 프로세스 ID 반환 | `sys_getpid()` |

### 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│              사용자 상호작용 레이어 (CLI/TUI)              │
├─────────────────────────────────────────────────────────┤
│              시각화 엔진 (visualizer/)                    │
├─────────────────────────────────────────────────────────┤
│              시스템 호출 레이어 (syscall/)                 │
├─────────────────────────────────────────────────────────┤
│              커널 코어 레이어 (kernel/)                    │
├─────────────────────────────────────────────────────────┤
│              데이터 구조 레이어 (core/)                    │
└─────────────────────────────────────────────────────────┘
```

## 빠른 시작

```bash
git clone git@gitee.com:zjh3432512933/process-management.git
cd process-management
python main.py          # 대화형 셸
python main.py --test   # 전체 테스트 실행
```

## 대화형 명령어

```
fork [name]         자식 프로세스 생성
wait [pid]          자식 프로세스 종료 대기
exit [code]         프로세스 종료
ps                  모든 프로세스 목록
tree                프로세스 트리 표시
pipe                파이프 생성
sched               스케줄러 상태 표시
mem                 메모리 페이지 테이블 표시
dmesg               커널 로그 표시
```

## 라이선스

[Apache License 2.0](LICENSE)
