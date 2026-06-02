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
>
> ⚠️ 如果第一次连接提示 `Are you sure you want to continue connecting (yes/no)?`，输入 `yes` 回车即可（只会出现一次）。

---

## 二、确认 Python 环境

大部分同学应该已经有 Python 了，验证一下即可。

### 方法一：直接验证
打开命令提示符（Win+R 输入 `cmd` 回车）或 Git Bash：
```bash
python --version
```
看到 `Python 3.8` 或更高版本就行。

### 方法二：如果你用 Conda
```bash
conda --version
conda activate base   # 激活 base 环境
python --version
```

> ⚠️ 如果提示 `python 不是命令`，说明 Python 没加到 PATH。
> 解决方法：重新安装 Python，安装时勾选「**Add Python to PATH**」。
> 下载地址：https://www.python.org/downloads/

---

## 三、克隆项目（每人只需做一次）

> 克隆 = 把远程仓库的代码下载到你电脑上，并建立关联。

> ⚠️ **前提：你已经被加到仓库里了！**
> 检查方法：登录 gitee.com → 右上角头像 → 「**我加入的**」→ 能看到 `process-management` 就行。
> 如果看不到，联系架构师（Zavci）邀请你。

### 1. 选一个放代码的目录

比如你想把代码放在 `D:\python` 下面：

```bash
# 先进入你想放代码的目录
cd /d/python
```

> 💡 不知道怎么进？
> - 在你想放代码的文件夹空白处 **右键** → 「Git Bash Here」
> - 这样就自动在这个目录下了，不用手动 cd

### 2. 克隆仓库

```bash
git clone git@gitee.com:zjh3432512933/process-management.git
```

会看到类似输出：
```
Cloning into 'process-management'...
remote: Enumerating objects: 10, done.
remote: Counting objects: 100% (10/10), done.
Receiving objects: 100% (10/10), done.
```

### 3. 进入项目目录

```bash
cd process-management
```

### 4. 确认成功

```bash
ls
```

应该看到这些文件：
```
README.md  collaboration.md  gitee_guide.md  plan.md  requirements.txt
```

### 5. 创建你自己的分支

```bash
# 创建并切换到你的分支（把 "你的名字" 换成你的拼音，比如 zhangsan）
git checkout -b feature/你的名字
```

看到 `Switched to a new branch 'feature/xxx'` 就成功了。

> ⚠️ **如果第2步报错** `Permission denied`：
> - 说明 SSH 密钥没配好，回到「一、首次配置」的第5步检查
> - 或者用 HTTPS 方式克隆（不需要SSH密钥，但每次要输密码）：
>   ```bash
>   git clone https://gitee.com/zjh3432512933/process-management.git
>   ```

---

## 四、用 VS Code 打开项目（推荐）

### 1. 安装 VS Code（如果没装）
下载地址：https://code.visualstudio.com/
一路默认安装即可。

### 2. 打开项目

**方法一：命令行**
```bash
# 在项目目录下执行
code .
```

**方法二：手动打开**
1. 打开 VS Code
2. 文件 → 打开文件夹
3. 选择你 clone 下来的 `process-management` 文件夹

### 3. 安装 Python 扩展（推荐）
1. VS Code 左侧点「扩展」图标（方块拼图的那个）
2. 搜索「Python」
3. 安装第一个「Python」（Microsoft 出品的）

---

## 五、安装项目依赖

克隆下来后，需要安装 Python 依赖包才能运行项目。

```bash
# 确保你在项目目录下
cd process-management

# 安装依赖
pip install -r requirements.txt
```

如果提示 `pip` 不是命令，试试：
```bash
python -m pip install -r requirements.txt
```

---

## 六、验证一切正常

运行以下命令，确认环境没问题：

```bash
# 检查 Python
python --version

# 检查 Git
git version

# 检查 SSH 连接
ssh -T git@gitee.com

# 检查项目文件
ls
```

四条命令都没报错，环境就配好了！🎉

---

## 七、日常开发流程

### ⚠️ 重要规则
> **只在自己的分支上写代码，不要直接改 master！**
> 写完后推送到自己的分支，通知 zavci 审核，审核通过后才会合入 master。

### 第一步：每天开始（复制粘贴这段）
```bash
git checkout master
git pull origin master
git checkout feature/你的名字
git merge master
```

### 第二步：写代码、提交
```bash
# 1. 看你改了什么
git status

# 2. 添加修改
git add .

# 3. 提交（描述你做了什么）
git commit -m "feat: 描述你做了什么"
```

### 第三步：推送到自己的分支（不要推master！）
```bash
git push
```

### 第四步：通知 zavci
在群里发：
```
我的代码已推送到 feature/xxx，请审核合并
```

### 第五步：zavci 审核后合入 master
只有 zavci 有权合并到 master。其他人**不要手动合并**。

---

## 八、分支命名规范

| 角色 | 分支名 |
|------|--------|
| zavci | `feature/zavci` |
| 队友1 | `feature/你的拼音` |
| 队友2 | `feature/你的拼音` |
| 队友3 | `feature/你的拼音` |
| 队友4 | `feature/你的拼音` |

---

## 九、提交信息规范

格式：`类型: 简短描述`

| 类型 | 含义 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat: 实现 Stride 调度器` |
| `fix` | 修bug | `fix: 修复孤儿回收逻辑` |
| `test` | 添加测试 | `test: 添加 COW 测试用例` |
| `docs` | 文档 | `docs: 更新 README` |
| `refactor` | 重构 | `refactor: 优化页表结构` |

---

## 十、常用命令速查

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
| 拉取最新 | `git pull origin master` |
| 合并分支 | `git merge 分支名` |
| 查看提交历史 | `git log --oneline` |
| 撤销未提交的修改 | `git checkout -- 文件名` |

---

## 十一、常见问题

### Q: push 被拒绝了怎么办？
```bash
# 先拉取最新代码
git pull origin master
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
# 查看 master 分支的最新提交
git log origin/master --oneline -10

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

## 十二、每日工作流（总结）

```
早上：
  git checkout master
  git pull origin master
  git checkout feature/你的名字
  git merge master

白天：
  写代码...
  git add .
  git commit -m "feat: xxx"

晚上：
  git push
  群里通知："我的代码已推送，请求合并"
```

### 为什么要 `git merge master`？

你每天写代码时，别人也在写代码并合并到 master。如果你不 merge，你的分支会落后：

```
master:     A ── B ── C (最新)
                  ↑
你的分支:   A ── (落后了，在这继续写 D、E)
```

最后合并到 master 时，B 的代码和你的代码冲突，要手动解决。

**每天 merge master：**

```
你的分支:   A ── B ── C (和 master 同步)
                  ↑ 继续写 D、E
```

冲突少，容易解决。

> 💡 **建议：每天开工第一件事就是 `git merge master`，保持和最新代码同步。**
