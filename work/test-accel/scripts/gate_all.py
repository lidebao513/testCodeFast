#!/usr/bin/env python3
# ============================================================================
# test-accel 统一质量门禁（本地 / pre-commit / CI 单入口）
# ----------------------------------------------------------------------------
# 依次执行：secret scan -> ruff(lint + format) -> check_enums -> check_structure
# -> mypy -> bandit -> pytest(含覆盖率)。任一环节非零退出，则整体非零退出。
#
# 工具解析优先级：
#   1) PATH（shutil.which）——CI 中 pip 安装后即命中
#   2) 托管环境目录（QUALITY_ENV 或本机 managed venv Scripts）
#   3) 回退 `python -m <tool>`（ruff/mypy/bandit）
# pytest 用「当前 python -m pytest」，须在已装项目依赖的 venv 中运行。
# ============================================================================
import os
import shutil
import subprocess
import sys


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 本机托管环境（含 ruff/mypy/bandit）；可用 QUALITY_ENV 覆盖
_MANAGED = os.environ.get("QUALITY_ENV") or (
    r"C:\Users\EDY\.workbuddy\binaries\python\envs\default\Scripts"
)


def _resolve(name: str) -> list:
    """返回可执行的命令列表（长度 1 或 3）。"""
    p = shutil.which(name) or shutil.which(name + ".exe")
    if p:
        return [p]
    cand = os.path.join(_MANAGED, name + ".exe")
    if os.path.isfile(cand):
        return [cand]
    return [sys.executable, "-m", name]


def _step(label: str, cmd: list) -> int:
    print(f"\n=== {label} ===")
    print("  $ " + " ".join(cmd))
    rc = subprocess.run(cmd, cwd=ROOT).returncode
    print(f"--- {label}: {'OK' if rc == 0 else 'FAIL'} (rc={rc}) ---")
    return rc


def _pytest_cmd() -> list:
    """pytest 必须在含项目依赖的 venv 中跑；优先用项目 venv，否则回退当前 python。"""
    venv_py = os.path.join(ROOT, "venv", "Scripts", "python.exe")
    py = venv_py if os.path.isfile(venv_py) else sys.executable
    return [py, "-m", "pytest", "--cov=backend", "--cov-report=term-missing", "-q"]


def main() -> int:
    ruff = _resolve("ruff")
    mypy = _resolve("mypy")
    bandit = _resolve("bandit")
    py = sys.executable

    failures = []

    # 0) 密钥 / 凭据预提交扫描（gitleaks 类，最先跑：最高风险）
    failures.append(("secret scan", _step("secret scan", [py, "scripts/check_secrets.py"])))
    # 1) ruff lint（backend 生产 + scripts 门禁 + tests 测试层）
    failures.append(
        ("ruff lint", _step("ruff lint", [*ruff, "check", "backend", "scripts", "tests"]))
    )
    # 2) ruff format 校验（不自动改写，保持 CI 幂等）
    failures.append(
        (
            "ruff format",
            _step(
                "ruff format --check",
                [*ruff, "format", "backend", "scripts", "tests", "--check"],
            ),
        )
    )
    # 3) 枚举单源门禁（字段感知 + 反向孤儿检查）
    failures.append(("check_enums", _step("check_enums", [py, "scripts/check_enums.py"])))
    # 4) 架构结构门禁（分层反向依赖 / 数据契约）
    failures.append(
        ("check_structure", _step("check_structure", [py, "scripts/check_structure.py"]))
    )
    # 5) mypy basic 类型检查（backend + scripts）
    failures.append(("mypy", _step("mypy backend scripts", [*mypy, "backend", "scripts"])))
    # 6) bandit 安全扫描（MEDIUM 及以上；backend + scripts；误报见 pyproject [tool.bandit]）
    failures.append(
        (
            "bandit",
            _step(
                "bandit backend scripts",
                [
                    *bandit,
                    "-r",
                    "backend",
                    "scripts",
                    "-x",
                    "backend/modules/selftest*,tests",
                    "-c",
                    "pyproject.toml",
                    "--severity-level",
                    "medium",
                ],
            ),
        )
    )
    # 7) pytest + 覆盖率（fail_under 见 pyproject [tool.coverage.report]）
    failures.append(("pytest", _step("pytest", _pytest_cmd())))

    failed = [(name, rc) for name, rc in failures if rc != 0]
    print("\n" + "=" * 60)
    if not failed:
        print("✅ 全部质量门禁通过（secret/lint/format/enum/structure/type/security/test）")
        return 0
    print(f"❌ {len(failed)} 项门禁未通过：")
    for name, rc in failed:
        print(f"   - {name} (rc={rc})")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
