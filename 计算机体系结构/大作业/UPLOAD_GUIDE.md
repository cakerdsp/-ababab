# GitHub上传指南

本指南将帮助您将Tomasulo算法模拟器项目上传到GitHub。

## 📋 准备工作

### 1. 安装Git
如果您还没有安装Git，请访问 [git-scm.com](https://git-scm.com/) 下载并安装。

### 2. 创建GitHub账户
如果您还没有GitHub账户，请访问 [github.com](https://github.com) 注册。

### 3. 配置Git（首次使用）
打开命令行工具，设置您的用户名和邮箱：

```bash
git config --global user.name "您的用户名"
git config --global user.email "您的邮箱@example.com"
```

## 🚀 上传步骤

### 步骤1：在GitHub创建新仓库

1. 登录GitHub
2. 点击右上角的 "+" 号，选择 "New repository"
3. 填写仓库信息：
   - **Repository name**: `tomasulo-simulator` (或您喜欢的名称)
   - **Description**: `A comprehensive implementation of the Tomasulo algorithm for dynamic instruction scheduling`
   - **Visibility**: 选择 Public（公开）或 Private（私有）
   - **不要**初始化README、.gitignore或license（我们已经创建了这些文件）
4. 点击 "Create repository"

### 步骤2：在本地初始化Git仓库

在项目文件夹中打开命令行（PowerShell或命令提示符），执行以下命令：

```bash
# 初始化Git仓库
git init

# 添加所有文件到暂存区
git add .

# 创建第一次提交
git commit -m "Initial commit: Tomasulo algorithm simulator implementation"
```

### 步骤3：连接到GitHub仓库

```bash
# 添加远程仓库（替换YOUR_USERNAME为您的GitHub用户名，YOUR_REPO为仓库名）
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# 推送到GitHub
git push -u origin main
```

### 步骤4：验证上传

1. 回到GitHub页面，刷新您的仓库页面
2. 确认所有文件都已成功上传
3. 检查README.md是否正确显示

## 🔧 可能遇到的问题及解决方案

### 问题1：推送被拒绝
**错误信息**: `Updates were rejected because the remote contains work that you do not have locally`

**解决方案**:
```bash
git pull origin main --allow-unrelated-histories
git push origin main
```

### 问题2：认证失败
**错误信息**: `Authentication failed`

**解决方案**:
1. 使用Personal Access Token代替密码
2. 在GitHub设置中生成Token: Settings → Developer settings → Personal access tokens
3. 使用Token作为密码

### 问题3：文件过大
如果有大文件无法上传，可以使用Git LFS：

```bash
git lfs install
git lfs track "*.pdf"
git add .gitattributes
git commit -m "Add Git LFS support"
git push origin main
```

## 📝 后续管理

### 更新项目
当您修改代码后，使用以下命令更新：

```bash
git add .
git commit -m "描述您的更改"
git push origin main
```

### 创建发布版本
为重要的版本创建标签：

```bash
git tag -a v1.0.0 -m "First stable release"
git push origin v1.0.0
```

### 分支管理
为新功能创建分支：

```bash
git checkout -b feature/new-feature
# 进行修改...
git add .
git commit -m "Add new feature"
git push origin feature/new-feature
```

## 🎯 最佳实践

### 提交信息规范
使用清晰的提交信息：
- `feat: 添加新功能`
- `fix: 修复bug`
- `docs: 更新文档`
- `refactor: 重构代码`
- `test: 添加测试`

### 项目维护
1. 定期更新README.md
2. 及时回复Issues和Pull Requests
3. 保持代码质量
4. 添加适当的标签和里程碑

## 📞 获取帮助

如果遇到问题，可以：
1. 查看GitHub官方文档
2. 搜索相关错误信息
3. 在GitHub社区寻求帮助
4. 联系项目维护者

## ✅ 检查清单

上传前请确认：
- [ ] 已移除敏感信息（如绝对路径、个人信息）
- [ ] README.md内容完整且格式正确
- [ ] .gitignore包含了不需要版本控制的文件
- [ ] 代码可以在其他环境中运行
- [ ] 许可证文件存在且正确
- [ ] 项目结构清晰，文件命名规范

恭喜！您的项目现在已经专业地托管在GitHub上了！ 