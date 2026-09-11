#!/bin/sh
# ============================================================================
# 安装 testCodeFast 的 git 钩子（纯 shell 实现，不依赖 pre-commit 框架）
#
# 背景：本机沙箱中 pre-commit 框架（原生 exe）无法解析 git，导致提交被误拦。
#       故改用「等价语义」的纯 shell 钩子，直接调用 scripts/gate_all.py 与
#       scripts/check_commit_msg.py，门禁内容与 CI(.github/workflows/guard.yml)
#       完全一致。.pre-commit-config.yaml 保留，供其他机器/CI 使用。
#
# 注意：所有传给原生 python 的路径都用 Windows 形式（pwd -W / 手工拼接），
#       否则原生 python 会把 MSYS 的 /c/... 误读成 C:\c\...。
#
# 用法：sh scripts/install_hooks.sh
# 卸载：rm .git/hooks/pre-commit .git/hooks/commit-msg
# ============================================================================
set -e

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
PROJ_DIR=$(cd "$SCRIPT_DIR/.." && pwd)
REPO_ROOT=$(cd "$PROJ_DIR/../.." && pwd)
HOOKS_DIR="$REPO_ROOT/.git/hooks"

if [ ! -d "$HOOKS_DIR" ]; then
  echo "[install_hooks] 未找到 $HOOKS_DIR，请确认仓库根为 $REPO_ROOT" >&2
  exit 1
fi

cat > "$HOOKS_DIR/pre-commit" <<'HOOK'
#!/bin/sh
# testCodeFast 质量门禁（由 work/test-accel/scripts/install_hooks.sh 生成）
REPO_ROOT=$(cd "$(dirname "$0")/../.." && pwd -W)
PROJ="$REPO_ROOT/work/test-accel"
if [ ! -d "$PROJ" ]; then
  echo "[quality-gate] 跳过：未找到 $PROJ"
  exit 0
fi
cd "$PROJ" || exit 1
for PY in python python3 py; do
  if command -v "$PY" >/dev/null 2>&1; then
    exec "$PY" scripts/gate_all.py
  fi
done
echo "[quality-gate] 未找到可用的 python，请把 python 加入 PATH 后重试" >&2
exit 1
HOOK

cat > "$HOOKS_DIR/commit-msg" <<'HOOK'
#!/bin/sh
# 提交信息规范校验（由 work/test-accel/scripts/install_hooks.sh 生成）
REPO_ROOT=$(cd "$(dirname "$0")/../.." && pwd -W)
MSG_FILE="$1"
[ -n "$MSG_FILE" ] || exit 0
case "$MSG_FILE" in
  /*|[A-Za-z]:*) ;;
  *) MSG_FILE="$REPO_ROOT/$MSG_FILE" ;;
esac
for PY in python python3 py; do
  if command -v "$PY" >/dev/null 2>&1; then
    exec "$PY" "$REPO_ROOT/work/test-accel/scripts/check_commit_msg.py" "$MSG_FILE"
  fi
done
exit 0
HOOK

chmod +x "$HOOKS_DIR/pre-commit" "$HOOKS_DIR/commit-msg"
echo "[install_hooks] 已安装："
echo "  $HOOKS_DIR/pre-commit"
echo "  $HOOKS_DIR/commit-msg"
