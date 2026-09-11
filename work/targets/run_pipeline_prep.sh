#!/usr/bin/env bash
# 流水线准备：备份harness -> 清理重拉 research-agent -> 变更摘要 -> 全量测试点
set +e
ROOT="C:/Users/EDY/WorkBuddy/testCodeFast"
cd "$ROOT"
PY="$ROOT/work/test-accel/venv/Scripts/python.exe"
TOKEN="pt-nJCaUBpSaU4VzRWrO12P4EJz_0e42fc49-d954-473f-b9ed-dbf88516f8ff"
GROUP="69cf2ce1f167bac7fd252020"
REPO="research-agent"
CLONE_URL="https://${TOKEN}@codeup.aliyun.com/${GROUP}/${REPO}.git"
OUT="$ROOT/work/research-agent-test"
mkdir -p "$OUT"
LOG="$OUT/pipeline_prep.log"
: > "$LOG"
echo "[$(date +%H:%M:%S)] 开始流水线准备" | tee -a "$LOG"

# 1) 备份既有测试 harness（已有代码，需复用）
echo "[$(date +%H:%M:%S)] 备份 _fx_test harness ..." | tee -a "$LOG"
rm -rf "$ROOT/work/targets/_fx_test_bak"
mkdir -p "$ROOT/work/targets/_fx_test_bak"
if [ -d "$ROOT/work/targets/research-agent/backend/research-agent-source/_fx_test" ]; then
  cp -r "$ROOT/work/targets/research-agent/backend/research-agent-source/_fx_test" "$ROOT/work/targets/_fx_test_bak/" 2>>"$LOG"
  echo "  harness 已备份到 _fx_test_bak/_fx_test" | tee -a "$LOG"
else
  echo "  未找到既有 _fx_test，跳过备份" | tee -a "$LOG"
fi

# 2) 清理现有 research-agent（含 worktree）
echo "[$(date +%H:%M:%S)] 清理现有 research-agent ..." | tee -a "$LOG"
git -C "$ROOT/work/targets/research-agent" worktree remove --force "$ROOT/work/targets/research-agent-20260907" 2>>"$LOG" || true
rm -rf "$ROOT/work/targets/research-agent-20260907"
rm -rf "$ROOT/work/targets/research-agent"
echo "  已清理" | tee -a "$LOG"

# 3) 重新克隆 test-20260907
echo "[$(date +%H:%M:%S)] 克隆 test-20260907 ..." | tee -a "$LOG"
export GIT_PROTOCOL_VERSION=0
git -c http.proxy= -c https.proxy= clone --branch test-20260907 --no-tags "$CLONE_URL" "$ROOT/work/targets/research-agent" 2>&1 | tail -8 | tee -a "$LOG"
echo "  HEAD=$(git -C "$ROOT/work/targets/research-agent" rev-parse HEAD 2>/dev/null)" | tee -a "$LOG"

# 4) fetch test-20260906 供 diff
echo "[$(date +%H:%M:%S)] fetch test-20260906 ..." | tee -a "$LOG"
git -C "$ROOT/work/targets/research-agent" -c http.proxy= -c https.proxy= fetch origin test-20260906 2>&1 | tail -5 | tee -a "$LOG"

# 5) 变更摘要
echo "[$(date +%H:%M:%S)] 生成变更摘要 ..." | tee -a "$LOG"
cd "$ROOT/work/targets/research-agent"
{
  echo "=== diff --stat (test-20260906..test-20260907) ==="
  git diff --stat origin/test-20260906..origin/test-20260907 2>&1
  echo "=== changed file count ==="
  git diff --name-only origin/test-20260906..origin/test-20260907 2>&1 | wc -l
  echo "=== additions/deletions ==="
  git diff --numstat origin/test-20260906..origin/test-20260907 2>&1 | awk '{a+=$1; d+=$2} END{print "added_lines="a" removed_lines="d}'
  echo "=== commit log ==="
  git log --oneline origin/test-20260906..origin/test-20260907 2>&1
} > "$OUT/change_summary.txt" 2>&1
echo "  变更摘要已写入 change_summary.txt" | tee -a "$LOG"

# 6) 全量测试点（复用 qa-test-points / gen_test_points）
echo "[$(date +%H:%M:%S)] 生成全量测试点 ..." | tee -a "$LOG"
cd "$ROOT/work/test-accel"
TP_REPO_PATH="$ROOT/work/targets/research-agent" \
TP_DIFF_BASE="origin/test-20260906" \
TP_DIFF_TARGET="origin/test-20260907" \
TP_SCOPE="全部" \
"$PY" gen_test_points.py > "$OUT/gen_test_points.log" 2>&1
echo "  测试点生成完成，日志见 gen_test_points.log" | tee -a "$LOG"

echo "[$(date +%H:%M:%S)] PIPELINE_PREP_DONE" | tee -a "$LOG"
