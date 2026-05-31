# Gitee 使用指南 — 团队成员必读

> 📌 本指南面向零 Git 经验的同学，按顺序操作即可。

---

## 〇、注册 Gitee 账号（没有账号的同学先做这步）

### 1. 打开注册页面
浏览器访问：https://gitee.com/signup

### 2. 填写注册信息
- **手机号/邮箱**：用你常用的邮箱
- **用户名**：建议用英文，比如 `zhangsan`（以后代码里显示的就是这个名字）
- **密码**：设一个你能记住的
- 完成验证码 → 点击"注册"

### 3. 验证邮箱
去你的邮箱收一封来自 Gitee 的验证邮件，点里面的链接完成验证。

### 4. 告诉我你的用户名
注册完成后，把你的 **Gitee 用户名** 发给我（架构师），我把你加到项目仓库里。

### 5. 确认你已被添加
登录 Gitee → 右上角头像 → 「我加入的」→ 应该能看到 `process-management` 这个项目。

---

## 一、首次配置（每人只需做一次）

### 1. 安装 Git

Windows 下载：https://git-scm.com/download/win

安装时：
- 选默认编辑器时，选 **Use Visual Studio Code**（或你习惯的编辑器）
- 其他全部点 **Next**，一路默认即可
- 安装完成后，右键桌面 → 出现「Git Bash Here」就成功了

### 2. 打开 Git Bash

方法一：右键桌面/文件夹空白处 → 「Git Bash Here」
方法二：开始菜单搜索「Git Bash」打开

**以下所有命令都在 Git Bash 里执行。**

### 3. 配置身份
```bash
git config --global user.name "你的名字（拼音或英文）"
git config --global user.email "你注册Gitee用的邮箱"
```

### 4. 生成 SSH 密钥
```bash
ssh-keygen -t ed25519 -C "你的邮箱"
```
出现提示一路按 **回车**（Enter），不要设密码。

### 5. 复制公钥
```bash
cat ~/.ssh/id_ed25519.pub
```
会输出一行很长的内容，**全部复制**（鼠标选中 → 右键 → Copy）。

### 6. 添加到 Gitee
1. 登录 gitee.com
2. 右上角头像 → **设置**（不是"个人主页"）
3. 左侧菜单 → **SSH公钥**
4. 「公钥」框里 **粘贴** 刚才复制的内容
5. 标题随便写（比如"我的电脑"）
6. 点 **确定**

### 7. 验证连接
```bash
ssh -T git@gitee.com
```
看到类似 `Hi Zavci! You've successfully authenticated` 就成功了。

> ⚠️ 如果提示 `Permission denied`，说明公钥没加对，回去检查第5步。

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
