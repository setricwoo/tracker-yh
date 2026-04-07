# GitHub 仓库设置指南

## 步骤1：在GitHub上创建仓库

1. 打开浏览器访问：https://github.com/new
2. 填写仓库信息：
   - Repository name: `tracker-yh`
   - Description: `银华基金中东地缘局势跟踪器`
   - 选择 Public（公开）
   - 不要勾选 "Initialize this repository with a README"
3. 点击 "Create repository"

## 步骤2：添加远程仓库并推送

创建仓库后，复制以下命令并在当前目录的PowerShell中执行：

```powershell
git remote add origin https://github.com/YOUR_USERNAME/tracker-yh.git
git branch -M main
git push -u origin main
```

（将 YOUR_USERNAME 替换为你的GitHub用户名）

## 或者使用SSH方式（如果你配置了SSH密钥）

```powershell
git remote add origin git@github.com:YOUR_USERNAME/tracker-yh.git
git branch -M main
git push -u origin main
```

## 步骤3：启用GitHub Pages（可选）

如果你想让网页可以直接访问：

1. 进入仓库 Settings -> Pages
2. Source 选择 "Deploy from a branch"
3. Branch 选择 "main"，文件夹选择 "/ (root)"
4. 点击 Save
5. 等待几分钟后，访问 https://YOUR_USERNAME.github.io/tracker-yh/

## 本地已准备就绪

本地git仓库已初始化并提交，等待远程仓库地址配置后即可推送。
