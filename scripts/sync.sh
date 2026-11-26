
#!/bin/bash

set -e

# 进入个人AI档案目录
cd "$HOME/MyAI" || exit 1

echo "================================"
echo "      MyAI 一键同步工具"
echo "================================"

# 检查Git仓库
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "错误：当前目录不是Git仓库"
    exit 1
fi

# 检查远程仓库
if ! git remote get-url origin >/dev/null 2>&1; then
    echo "错误：没有配置GitHub远程仓库"
    exit 1
fi

# 检查当前分支
BRANCH=$(git branch --show-current)

if [ -z "$BRANCH" ]; then
    echo "错误：无法确定当前分支"
    exit 1
fi

# 检查文件状态
echo ""
echo "正在检查档案..."

git status --short

# 添加文件
git add -A

# 没有变化就不创建空提交
if git diff --cached --quiet; then
    echo "没有新的档案修改。"
else
    # 自动提交
    TIME=$(date "+%Y-%m-%d %H:%M:%S")
    git commit -m "Update AI archive: $TIME"
fi

# 拉取远程最新版本
echo ""
echo "正在检查GitHub更新..."

git pull --rebase origin "$BRANCH"

# 推送本地提交
echo ""
echo "正在同步到GitHub..."

git push origin "$BRANCH"

echo ""
echo "================================"
echo "       同步成功！"
echo "================================"

echo "当前分支：$BRANCH"
echo "仓库地址：$(git remote get-url origin)"
echo "完成时间：$(date)"
echo ""

