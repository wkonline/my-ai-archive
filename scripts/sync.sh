#!/bin/bash
# 三个方向的同步统一入口
#
#   ./scripts/sync.sh pull         git  → 本地（拉取远程更新）
#   ./scripts/sync.sh push         本地 → git （提交并推送）
#   ./scripts/sync.sh nas [目标]   本地 → NAS（部署，目标见下）
#   ./scripts/sync.sh all          依次 pull → push → nas
#   ./scripts/sync.sh status       查看本地 / 远程 / NAS 状态
#
# nas 目标：old 老版系统(8000)、new 新版系统(8001)、vue 只同步前端产物、
#           all 两者都部署（默认）
#
# 环境变量（仅对 nas 生效）：
#   DRY_RUN=1   只打印将要从 NAS 删除的文件，不实际删除
#   PRUNE=0     不删除 NAS 上的多余文件
#
# 不带参数运行时进入交互菜单，供 Sync.command 双击使用。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NAS_SYNC="$ROOT/projects/cono_new/deploy/sync.sh"

die() { echo "错误：$*" >&2; exit 1; }

git_() { git -C "$ROOT" "$@"; }

current_branch() {
    local b
    b=$(git_ branch --show-current 2>/dev/null || true)
    [ -n "$b" ] || die "无法确定当前分支（HEAD 可能处于游离状态）"
    printf '%s' "$b"
}

require_repo() {
    git_ rev-parse --is-inside-work-tree >/dev/null 2>&1 || die "$ROOT 不是 Git 仓库"
    git_ remote get-url origin >/dev/null 2>&1 || die "没有配置远程仓库 origin"
}

# ── git → 本地 ────────────────────────────────────────────────
do_pull() {
    require_repo
    local branch
    branch=$(current_branch)

    echo "==> 拉取 origin/$branch ..."
    git_ fetch origin --prune

    if [ "$(git_ rev-parse HEAD)" = "$(git_ rev-parse "origin/$branch")" ]; then
        echo "    已是最新"
        return 0
    fi

    # 只接受快进：本地有未推送提交时不要自动合并，避免产生意外的合并提交
    if ! git_ merge --ff-only "origin/$branch"; then
        echo ""
        echo "!! 本地与远程已分叉，无法快进合并。"
        echo "   先推送本地提交再拉取：./scripts/sync.sh push"
        echo "   或手动处理：cd $ROOT && git rebase origin/$branch"
        return 1
    fi
    echo "    已更新到 $(git_ log --oneline -1)"
}

# ── 本地 → git ────────────────────────────────────────────────
do_push() {
    require_repo
    local branch
    branch=$(current_branch)

    if [ -n "$(git_ status --porcelain)" ]; then
        echo "==> 提交本地修改 ..."
        git_ add -A
        if git_ diff --cached --quiet; then
            echo "    暂存区无实际改动"
        else
            git_ commit -q -m "Update: $(date '+%Y-%m-%d %H:%M:%S')"
            echo "    $(git_ log --oneline -1)"
        fi
    else
        echo "==> 工作区干净，无需提交"
    fi

    echo "==> 检查远程 ..."
    git_ fetch origin --prune
    if [ "$(git_ rev-list --count "origin/$branch..HEAD")" -gt 0 ] &&
       [ "$(git_ rev-list --count "HEAD..origin/$branch")" -gt 0 ]; then
        echo "    远程有新提交，先变基"
        git_ pull --rebase origin "$branch"
    fi

    if [ "$(git_ rev-list --count "origin/$branch..HEAD")" -eq 0 ]; then
        echo "    远程已包含全部提交"
        return 0
    fi

    echo "==> 推送到 origin/$branch ..."
    git_ push origin "$branch"
    echo "    完成"
}

# ── 本地 → NAS ────────────────────────────────────────────────
do_nas() {
    local target="${1:-all}"
    case "$target" in
        old|new|vue|all) ;;
        *) die "nas 目标只能是 old / new / vue / all，收到：$target" ;;
    esac
    [ -x "$NAS_SYNC" ] || die "找不到部署脚本 $NAS_SYNC"

    if [ -n "$(git_ status --porcelain 2>/dev/null || true)" ]; then
        echo "!! 注意：工作区有未提交的修改，部署的是当前磁盘上的代码"
        echo ""
    fi
    "$NAS_SYNC" "$target"
}

# ── 状态 ─────────────────────────────────────────────────────
do_status() {
    require_repo
    local branch ahead behind dirty
    branch=$(current_branch)

    echo "分支：$branch"
    echo "远程：$(git_ remote get-url origin)"

    if git_ fetch origin --prune >/dev/null 2>&1; then
        ahead=$(git_ rev-list --count "origin/$branch..HEAD" 2>/dev/null || echo 0)
        behind=$(git_ rev-list --count "HEAD..origin/$branch" 2>/dev/null || echo 0)
        echo "未推送：$ahead 个提交    未拉取：$behind 个提交"
    else
        echo "!! 无法访问远程，跳过远程比较"
    fi

    dirty=$(git_ status --porcelain | wc -l | tr -d ' ')
    if [ "$dirty" -eq 0 ]; then
        echo "工作区：干净"
    else
        echo "工作区：$dirty 个文件有改动"
        git_ status --short | head -10
    fi

    echo ""
    echo "最近提交："
    git_ log --oneline -3
}

# ── 全套 ─────────────────────────────────────────────────────
do_all() {
    do_pull
    echo ""
    do_push
    echo ""
    do_nas "${1:-all}"
}

usage() {
    sed -n '2,17p' "$0" | sed 's/^# \{0,1\}//'
}

menu() {
    echo "=============================="
    echo "        MyAI 同步工具"
    echo "=============================="
    echo ""
    echo "  1) 从 git 拉取到本地"
    echo "  2) 本地提交并推送到 git"
    echo "  3) 本地部署到 NAS"
    echo "  4) 全套（拉取 → 推送 → 部署）"
    echo "  5) 查看状态"
    echo "  0) 退出"
    echo ""
    printf "请选择 [0-5]: "
    read -r choice
    echo ""
    case "$choice" in
        1) do_pull ;;
        2) do_push ;;
        3) do_nas all ;;
        4) do_all all ;;
        5) do_status ;;
        0) exit 0 ;;
        *) die "无效选择：$choice" ;;
    esac
    echo ""
    echo "完成。"
}

case "${1:-}" in
    pull)   do_pull ;;
    push)   do_push ;;
    nas)    shift; do_nas "${1:-all}" ;;
    all)    shift; do_all "${1:-all}" ;;
    status) do_status ;;
    help|-h|--help) usage ;;
    "")     menu ;;
    *)      usage; exit 1 ;;
esac
