#!/usr/bin/env bash
# ============================================================================
# 启用远程门禁 + 为 main 设分支保护（一次性，需本机已装 gh 并 gh auth login）
# ----------------------------------------------------------------------------
# 背景：test-accel 的 .github/workflows/guard.yml 已就绪，但 GitHub Actions
#       默认可能未启用，且 main 分支未设保护 —— 目前远程门禁是「纸面防线」。
# 本脚本把「启用 Actions」与「main 分支保护（guard 必过 + 至少 1 人评审）」真正落地。
#
# 前置（本机执行一次）：
#   1) 安装 gh：    winget install --id GitHub.cli     # 或 https://cli.github.com
#   2) 登录：      gh auth login                      # 选 GitHub.com / HTTPS / 浏览器或 token
#   3) 先 push 当前改动（含本脚本与 guard.yml 等）到 main，否则保护规则引用的
#      guard 检查尚未产生过记录，PR 会无法合并。
#
# 运行：  bash scripts/enable_remote_guard.sh
# 注意：会修改仓库设置，需对 lidebao513/testCodeFast 有 admin 权限。
# ============================================================================
set -euo pipefail

REPO="lidebao513/testCodeFast"
BRANCH="main"
CHECK="guard"   # guard.yml 中 jobs.guard 的状态检查名

echo ">> 目标仓库: $REPO  分支: $BRANCH"

# 0) 确认登录
gh auth status || { echo "请先执行 gh auth login"; exit 1; }

# 1) 启用仓库 Actions（允许所有 action / 可重用工作流）
echo ">> 启用 GitHub Actions ..."
gh api -X PUT "/repos/$REPO/actions/permissions" \
  -f enabled=true \
  -f allowed_actions=all

# 2) 为 main 设置分支保护
#    - required_status_checks: 必须通过名为 "guard" 的 CI 检查
#    - enforce_admins: true    （保护规则也约束管理员）
#    - required_pull_request_reviews: 至少 1 个审批，过期 review 作废
echo ">> 设置 $BRANCH 分支保护（guard 必过 + 1 人审批）..."
gh api -X PUT "/repos/$REPO/branches/$BRANCH/protection" \
  -f "required_status_checks={\"strict\":false,\"checks\":[{\"context\":\"$CHECK\"}]}" \
  -f enforce_admins=true \
  -f "required_pull_request_reviews={\"required_approving_review_count\":1,\"dismiss_stale_reviews\":true,\"require_code_owner_reviews\":false}" \
  -f "restrictions=null"

echo "✅ 完成：$BRANCH 已启用 Actions 并设分支保护。"
echo "   后续流程：develop/特性分支 → PR 到 main → 自动跑 guard → 至少 1 人评审 → 合并。"
echo "   查看：https://github.com/$REPO/settings/branches"
