# Gitee 使用指南 — 团队成员必读

## 一、首次配置（每人只需做一次）

### 1. 安装 Git
Windows 下载：https://git-scm.com/download/win
安装时一路默认即可。

### 2. 配置身份
打开 Git Bash，执行：
```bash
git config --global user.name "你的名字"
git config --global user.email "你的邮箱"
```

### 3. 生成 SSH 密钥
```bash
ssh-keygen -t ed25519 -C "你的邮箱"
# 一路回车，不要设密码
```

### 4. 复制公钥
```bash
cat ~/.ssh/id_ed25519.pub
# 复制输出的整行内容
```

### 5. 添加到 Gitee
1. 登录 gitee.com
2. 右上角头像 → 设置 → SSH公钥
3. 粘贴公钥 → 确定

### 6. 验证连接
```bash
ssh -T git@gitee.com
# 看到 "Hi xxx! You've successfully authenticated" 就成功了
```

---

## 二、克隆项目（每人只需做一次）

```bash
# 选择一个目录，比如 D:\python
cd D:\python
git clone git@gitee.com:zjh3432512933/process-management.git
cd process-management
```

---

## 三、日常开发流程

### 每天开始工作前
```bash
# 1. 切到 main 分支
git checkout main

# 2. 拉取最新代码
git pull origin main

# 3. 创建/切换到自己的分支
git checkout feature/你的名字
# 如果分支已存在：
git checkout feature/你的名字
```

### 写完代码后
```bash
# 1. 查看你改了哪些文件
git status

# 2. 添加修改的文件
git add .
# 或者只添加特定文件：
git add kernel/scheduler.py

# 3. 提交
git commit -m "feat: 描述你做了什么"
```

### 推送到远程
```bash
# 第一次推送自己的分支
git push -u origin feature/你的名字

# 之后推送
git push
```

### 请求合并到 main
1. 在 Gitee 网页上发起 Pull Request（Gitee 叫"合并请求"）
2. 或者在群里通知架构师手动合并

### 合并别人的代码后，同步到自己分支
```bash
# 1. 切到自己的分支
git checkout feature/你的名字

# 2. 合并 main 的最新代码
git merge main

# 3. 如果有冲突，手动解决后：
git add .
git commit -m "merge: 同步 main 最新代码"
```

---

## 四、分支命名规范

| 角色 | 分支名 |
|------|--------|
| A（PCB+进程树） | `feature/pcb` |
| B（内存管理） | `feature/memory` |
| C（调度器） | `feature/scheduler` |
| D（系统调用） | `feature/syscall` |
| E（可视化） | `feature/visualizer` |

---

## 五、提交信息规范

格式：`类型: 简短描述`

| 类型 | 含义 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat: 实现 Stride 调度器` |
| `fix` | 修bug | `fix: 修复孤儿回收逻辑` |
| `test` | 添加测试 | `test: 添加 COW 测试用例` |
| `docs` | 文档 | `docs: 更新 README` |
| `refactor` | 重构 | `refactor: 优化页表结构` |

---

## 六、常用命令速查

| 操作 | 命令 |
|------|------|
| 查看当前分支 | `git branch` |
| 查看所有分支 | `git branch -a` |
| 切换分支 | `git checkout 分支名` |
| 创建并切换分支 | `git checkout -b 分支名` |
| 查看修改状态 | `git status` |
| 查看修改内容 | `git diff` |
| 添加所有文件 | `git add .` |
| 提交 | `git commit -m "描述"` |
| 推送 | `git push` |
| 拉取最新 | `git pull origin main` |
| 合并分支 | `git merge 分支名` |
| 查看提交历史 | `git log --oneline` |
| 撤销未提交的修改 | `git checkout -- 文件名` |

---

## 七、常见问题

### Q: push 被拒绝了怎么办？
```bash
# 先拉取最新代码
git pull origin main
# 解决冲突（如果有）
# 再 push
git push
```

### Q: 我改错文件了，想撤销？
```bash
# 撤销单个文件
git checkout -- 文件名

# 撤销所有修改
git checkout -- .
```

### Q: 我想看别人改了什么？
```bash
# 查看 main 分支的最新提交
git log origin/main --oneline -10

# 查看某个文件的修改历史
git log --oneline 文件名
```

### Q: 合并时有冲突怎么办？
1. 打开冲突的文件，搜索 `<<<<<<<`
2. 手动选择保留哪部分代码
3. 删掉 `<<<<<<<`、`=======`、`>>>>>>>` 标记
4. `git add .` → `git commit`

### Q: 我不小心把大文件 commit 了？
```bash
# 撤销最后一次 commit（保留修改）
git reset --soft HEAD~1
# 把大文件从暂存区移除
git reset HEAD 大文件名
# 重新 commit
git commit -m "去掉大文件"
```

---

## 八、每日工作流（总结）

```
早上：
  git checkout main
  git pull origin main
  git checkout feature/你的名字
  git merge main

白天：
  写代码...
  git add .
  git commit -m "feat: xxx"

晚上：
  git push
  群里通知："我的代码已推送，请求合并"
```
