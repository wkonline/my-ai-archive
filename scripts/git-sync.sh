#!/bin/bash
set -euo pipefail

cd "$HOME/MyAI" || exit 1

echo "================================"
echo "      MyAI Git 同步工具"
echo "================================"

# 检查是否在Git仓库中
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "错误：当前目录不是Git仓库"
    exit 1
fi

# 检查远程仓库
if ! git remote get-url origin >/dev/null 2>&1; then
    echo "错误：没有配置GitHub远程仓库"
    exit 1
fi

# 显示当前状态
echo ""
echo "当前分支: $(git branch --show-current)"
echo "远程地址: $(git remote get-url origin)"
echo ""

# 拉取远程最新信息
echo "正在检查远程更新..."
git fetch origin

# 比较本地与远程
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main 2>/dev/null || git rev-parse origin/$(git branch --show-current) 2>/dev/null)

if [ "$LOCAL" = "$REMOTE" ]; then
    echo "✓ 本地已是最新，无需同步"
    git status --short
    exit 0
fi

# 显示差异
echo ""
echo "发现远程有新提交："
git log --oneline HEAD..origin/main | head -10
echo ""

# 询问用户如何处理
echo "选择同步方式："
echo "  1) 强制覆盖本地为远程版本 (git reset --hard origin/main) - 丢弃本地所有修改"
echo "  2) 拉取并合并 (git pull origin main) - 保留本地修改，生成合并提交"
echo "  3) 拉取并变基 (git pull --rebase origin main) - 保留本地修改，线性历史"
echo "  4) 仅查看差异，不操作"
echo "  5) 取消"
echo ""
read -p "请输入选择 [1-5]: " choice

case $choice in
    1)
        echo "正在强制同步到远程版本..."
        git reset --hard origin/main
        echo "✓ 同步完成"
        ;;
    2)
        echo "正在拉取并合并..."
        git pull origin main
        echo "✓ 合并完成"
        ;;
    3)
        echo "正在拉取并变基..."
        git pull --rebase origin main
        echo "✓ 变基完成"
        ;;
    4)
        echo "差异预览："
        git diff HEAD..origin/main --stat
        ;;
    5)
        echo "已取消"
        exit 0
        ;;
    *)
        echo "无效选择"
        exit 1
        ;;
esac

echo ""
echo "================================"
echo "       当前状态"
echo "================================"
git status --short
git log --oneline -3
