# ProcMgrSim 10分钟精简版展示脚本

> 精确到每一步说什么、敲什么、看什么。
> 总时长 8-10 分钟，含 5 次现场演示。

---

## 时间总览

| 段落 | Slide | 演示 | 时长 |
|------|-------|------|------|
| 开场 | 01-03 | — | 1min |
| COW 写时复制 | 05-06 | demo×2 | 2.5min |
| Stride 公平调度 | 07 | demo×1 | 2min |
| 管道 IPC | — | demo×1 | 1.5min |
| 总结 | 08-13 | — | 1.5min |
| **合计** | **13页** | **5次** | **~8.5min** |

---

## ▌Slide 01 · 封面

**说什么**：
> 各位评审老师好，我们是 zavci 团队，项目叫 ProcMgrSim。
> 用 Python 在用户态完整还原了 Linux 内核的进程管理机制。
> 下面我一边演示一边介绍。

**要点**：等动画播完再开口，语速放慢。

---

## ▌Slide 02 · 项目定位

**说什么**：
> 我们实现了三个核心机制：
> COW 写时复制——fork 时零内存拷贝；
> Stride 公平调度——优先级决定 CPU 时间比例；
> 管道 IPC——父写子读，数据在内核缓冲区传递。
> 都是 Linux 内核的真实设计模式，5000 行纯 Python，零依赖。

---

## ▌Slide 03 · NEXT 五个场景

**说什么**：
> 五个场景覆盖进程管理全链路，接下来切到 VSCode 现场演示。

---

## ▌Slide 04 · DEMO TIME

**说什么**：
> 好，切到 VSCode。

**操作**：按 Esc → overview → 点 VSCode。

---

## ▌演示 1：Fork + ps + tree（~1min）

```bash
python main.py
```

```
[PID:0] os> fork shell
```

**说**：fork 创建子进程，PID=1。

```
[PID:0] os> fork editor
```

```
[PID:0] os> ps
```

**说**：ps 列出所有进程，init 是根进程，shell 和 editor 是子进程。

```
[PID:0] os> tree
```

**说**：进程树展示父子关系，和 Linux 的 pstree 一样。

```
[PID:0] os> kill 1
[PID:0] os> wait -1
```

**说**：kill 杀死进程，wait 回收僵尸进程。完整的 fork → waitpid 生命周期。

---

## ▌回到 Slide 05 · COW 核心原理

**操作**：按 ← 回到 PPT。

**说什么**：
> 第一个创新点：COW 写时复制。
> fork 时子进程页表指向同一物理帧，ref_count 加 1。
> 只有写入时才触发复制——按需复制，节省内存。

---

## ▌演示 2：COW 验证（~1.5min）

**操作**：切回 VSCode。

```
[PID:0] os> fork child
[PID:0] os> mem
```

**说**：fork 前，已使用 4 帧，共享帧为 0。

```
[PID:0] os> tick 5
[PID:0] os> mem
```

**说**：注意！已使用还是 4 帧，共享帧从 0 变成 4。零拷贝，零额外开销。

```
[PID:0] os> write 4 "test cow"
[PID:0] os> mem
```

**说**：写入后，已使用变成 5，共享帧变成 3。只复制了被修改的那一帧。
> 总结：fork 后共享 4 帧 → 写入后只复制 1 帧 → 其余继续共享。

---

## ▌Slide 07 · Stride 公平调度

**操作**：按 ← 回到 PPT。

**说什么**：
> 第二个创新点：Stride 公平调度。
> stride = 1,000,000 / (256 - priority)，A 的步长小所以跑得多。
> 200 个时间片后，A 约 50%，B 和 C 各约 25%，比例 2:1:1。
> 这不是经验调优，是数学证明的公平性。

**要点**：等柱状图动画播完再开口。

---

## ▌演示 3：Stride 验证（~1.5min）

**操作**：切回 VSCode。

```
[PID:0] os> fork A
[PID:0] os> nice 1 10
[PID:0] os> fork B
[PID:0] os> nice 2 133
[PID:0] os> fork C
[PID:0] os> nice 3 133
```

**说**：A 优先级 10，B 和 C 优先级 133。

```
[PID:0] os> tick 200
[PID:0] os> ps
```

**说**：A 约 100，B 和 C 各约 50，比例 2:1:1，和公式一致。

---

## ▌演示 4：管道 IPC（~1min）

```
[PID:0] os> pipe
```

**说**：创建管道，fd=3 读端，fd=4 写端。

```
[PID:0] os> fork child
[PID:0] os> write 4 "Hello from parent"
[PID:0] os> read 3
```

**说**：父写子读，数据在内核缓冲区传递。这就是 Linux 最基础的进程间通信。

---

## ▌回到 Slide 08-13 · 总结

**操作**：按 ← 回到 PPT，快速翻页。

**说什么**：
> 总结三个创新点：
> COW 写时复制——fork 时零内存拷贝；
> Stride 公平调度——基于 Linux CFS 的数学基础；
> 完整生命周期——六状态机 + 级联退出 + 孤儿回收。
>
> 5000 行纯 Python，40 多个测试用例，代码开源在 Gitee。
> 感谢各位老师，欢迎指导与交流。

---

## 附录：演示前 Checklist

- [ ] VSCode 终端路径在 `process-management/`
- [ ] 运行过 `python main.py` 确认无报错
- [ ] 字体 16pt 以上
- [ ] 终端深色背景
- [ ] PPT 全屏就绪
- [ ] 关闭系统通知

## 附录：常见意外处理

| 意外 | 处理 |
|------|------|
| 命令输错 | 重新输入，说「打错了」 |
| 数字有偏差 | 说「取整误差，核心逻辑不变」 |
| 程序卡住 | Ctrl+C，说「边界条件，后续优化」 |
| 时间不够 | 跳过管道演示，直接总结 |

## 附录：评委可能提问

**Q：COW 怎么触发的？**
> 真实 Linux 靠硬件 MMU 缺页中断，我们用软件检查 is_writable 标志模拟。逻辑一致，触发方式不同。

**Q：Stride 和 CFS 的关系？**
> Stride 是 CFS 的数学基础。CFS 用 vruntime 选最小，我们用 pass_value 选最小，同一个思想。

**Q：为什么用 Python？**
> 代码可读性高，评委能直接看懂。5000 行实现了 C 可能需要 2 万行的功能。

**Q：和真实内核的差距？**
> 没有硬件 MMU、没有真正的并发、没有多级页表。但核心设计模式一致。

**Q：init 能被 kill 吗？**
> 不能。Fork Bomb 防护的一部分。

**Q：管道支持多读者吗？**
> 不支持，1:1 单向管道，和 Linux 一样。
