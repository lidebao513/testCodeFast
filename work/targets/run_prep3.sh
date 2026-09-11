#!/usr/bin/env bash
set -u
REPO="C:/Users/EDY/WorkBuddy/testCodeFast/work/targets/research-agent"
OUT="C:/Users/EDY/WorkBuddy/testCodeFast/work/research-agent-test"
PY="C:/Users/EDY/WorkBuddy/testCodeFast/work/test-accel/venv/Scripts/python.exe"
GEN="C:/Users/EDY/WorkBuddy/testCodeFast/work/test-accel/gen_test_points.py"
LOG="C:/Users/EDY/WorkBuddy/testCodeFast/work/targets/prep3.log"
BASE=codeup/test-20260906
TARGET=codeup/test-20260907
echo "==== [$(date +%H:%M:%S)] STEP1 clean checkout $TARGET ====" | tee -a "$LOG"
cd "$REPO" || { echo "REPO missing"; exit 1; }
git checkout -f -B test-20260907 "$TARGET" 2>&1 | tee -a "$LOG"
HEAD_NOW=$(git rev-parse HEAD)
echo "HEAD_NOW=$HEAD_NOW (expect 93aa0d8d1235313aacccec1c3565616bb17d5e6f)" | tee -a "$LOG"
git log --oneline -1 | tee -a "$LOG"

echo "==== [$(date +%H:%M:%S)] STEP2 change summary $BASE..$TARGET ====" | tee -a "$LOG"
mkdir -p "$OUT"
{
  echo "=== diff --stat ($BASE..$TARGET) ==="
  git diff --stat "$BASE..$TARGET"
  echo "=== changed file count ==="
  git diff --name-only "$BASE..$TARGET" | wc -l
  echo "=== additions/deletions (numstat sum) ==="
  git diff --numstat "$BASE..$TARGET" | awk '{a+=$1; d+=$2} END{print "added_lines="a" removed_lines="d}'
  echo "=== commit log ==="
  git log --oneline "$BASE..$TARGET"
} > "$OUT/change_summary.txt" 2>&1
echo "change_summary.txt written, size=$(wc -c < "$OUT/change_summary.txt")" | tee -a "$LOG"

echo "==== [$(date +%H:%M:%S)] STEP3 generate test points ====" | tee -a "$LOG"
cd "C:/Users/EDY/WorkBuddy/testCodeFast/work/test-accel" || { echo "test-accel missing"; exit 1; }
TP_REPO_PATH="$REPO" TP_DIFF_BASE="$BASE" TP_DIFF_TARGET="$TARGET" TP_SCOPE=全部 "$PY" "$GEN" 2>&1 | tail -40 | tee -a "$LOG"
echo "==== [$(date +%H:%M:%S)] DONE prep3 ====" | tee -a "$LOG"
