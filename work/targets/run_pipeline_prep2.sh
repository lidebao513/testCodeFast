#!/usr/bin/env bash
# 流水线准备(修正)：不删除目录，强制重置到 codeup/test-20260907 干净检出 -> 变更摘要 -> 全量测试点
set +e
ROOT="C:/Users/EDY/WorkBuddy/testCodeFast"
cd "$ROOT"
PY="$ROOT/work/test-accel/venv/Scripts/python.exe"
OUT="$ROOT/work/research-agent-test"
mkdir -p "$OUT"
LOG="$OUT/pipeline_prep2.log"
: > "$LOG"
echo "[$(date +%H:%M:%S)] prep2 开始" | tee -a "$LOG"

cd "$ROOT/work/targets/research-agent"
export GIT_PROTOCOL_VERSION=0

# 0) 移除可能的旧 worktree（不阻塞）
git worktree remove --force "$ROOT/work/targets/research-agent-20260907" 2>>"$LOG" || true

# 1) 抓取目标分支与基线
echo "[$(date +%H:%M:%S)] fetch codeup test-20260907 / test-20260906 ..." | tee -a "$LOG"
git -c http.proxy= -c https.proxy= fetch codeup test-20260907 test-20260906 2>&1 | tail -5 | tee -a "$LOG"

# 2) 强制检出干净 test-20260907
echo "[$(date +%H:%M:%S)] checkout -f codeup/test-20260907 ..." | tee -a "$LOG"
git checkout -f codeup/test-20260907 2>&1 | tail -3 | tee -a "$LOG"
git reset --hard codeup/test-20260907 2>&1 | tail -2 | tee -a "$LOG"
git clean -fdx 2>&1 | tail -3 | tee -a "$LOG"
echo "  HEAD=$(git rev-parse HEAD 2>/dev/null)  branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)" | tee -a "$LOG"

# 3) 变更摘要
echo "[$(date +%H:%M:%S)] 生成变更摘要 ..." | tee -a "$LOG"
{
  echo "=== diff --stat (codeup/test-20260906..codeup/test-20260907) ==="
  git diff --stat codeup/test-20260906..codeup/test-20260907 2>&1
  echo "=== changed file count ==="
  git diff --name-only codeup/test-20260906..codeup/test-20260907 2>&1 | wc -l
  echo "=== additions/deletions ==="
  git diff --numstat codeup/test-20260906..codeup/test-20260907 2>&1 | awk '{a+=$1; d+=$2} END{print "added_lines="a" removed_lines="d}'
  echo "=== commit log ==="
  git log --oneline codeup/test-20260906..codeup/test-20260907 2>&1
} > "$OUT/change_summary.txt" 2>&1
echo "  变更摘要已写入 change_summary.txt" | tee -a "$LOG"

# 4) 全量测试点
echo "[$(date +%H:%M:%S)] 生成全量测试点 ..." | tee -a "$LOG"
cd "$ROOT/work/test-accel"
TP_REPO_PATH="$ROOT/work/targets/research-agent" \
TP_DIFF_BASE="codeup/test-20260906" \
TP_DIFF_TARGET="codeup/test-20260907" \
TP_SCOPE="全部" \
"$PY" gen_test_points.py > "$OUT/gen_test_points.log" 2>&1
echo "  测试点生成完成" | tee -a "$LOG"

echo "[$(date +%H:%M:%S)] PIPELINE_PREP2_DONE" | tee -a "$LOG"
