"""pull_code 单元测试：覆盖脱敏、目录三态判定、变更集计算、工作树模式与失败状态。

同时守护 scripts/pull_code.py 与 backend/core/enums.py 的 PullStatus 一致性（枚举单源）。
"""

import os
import sys

import pytest


_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
SCRIPTS = os.path.join(_ROOT, "scripts")
sys.path.insert(0, _ROOT)
sys.path.insert(0, SCRIPTS)

import pull_code as pc

from backend.core.enums import PullStatus as PlatformPullStatus


@pytest.fixture
def no_fs(monkeypatch):
    """禁用一切落盘 / 权限副作用，避免测试触碰真实文件系统。"""
    monkeypatch.setattr(pc, "_dump", lambda *a, **k: None)
    monkeypatch.setattr(pc, "_set_readonly", lambda *a, **k: None)


# ============================ URL 脱敏 ============================
def test_mask_url_empty():
    assert pc._mask_url("") == ""


def test_mask_url_basic():
    u = pc._mask_url("https://user:pass@codeup.aliyun.com/x/y.git")
    assert "user" not in u and "pass" not in u and "codeup.aliyun.com" in u


def test_mask_url_no_colon_token():
    u = pc._mask_url("https://ghp_abc123@github.com/owner/repo.git")
    assert "ghp_abc123" not in u and "github.com" in u


def test_mask_url_query_token():
    u = pc._mask_url("https://oauth2:tk@host/path?token=SECRET")
    assert "tk" not in u and "SECRET" not in u and "?..." in u


def test_mask_url_query_without_userinfo():
    """无 userinfo 但带查询串 → 同样必须剥离（防 ?token= 泄露）。"""
    u = pc._mask_url("https://host/path?token=SECRET&x=1")
    assert "SECRET" not in u and "?..." in u and "host" in u


def test_mask_url_fragment_stripped():
    u = pc._mask_url("https://host/path#access_token=SECRET")
    assert "SECRET" not in u and "#..." in u


def test_mask_url_no_cred_passthrough():
    assert pc._mask_url("https://github.com/owner/repo.git") == "https://github.com/owner/repo.git"


def test_mask_url_local_path_passthrough():
    """本地路径 / scp 形式（无 ://）不做 URL 解析，原样返回。"""
    assert pc._mask_url("C:/work/targets/repo") == "C:/work/targets/repo"
    assert pc._mask_url("git@github.com:owner/repo.git") == "git@github.com:owner/repo.git"


# ============================ 凭据不经 argv ============================
def test_credential_env_windows_passthrough(monkeypatch):
    """非 POSIX（Windows）：不做剥离，原样返回、无 env（保持克隆行为不变）。"""
    monkeypatch.setattr(pc.os, "name", "nt")
    with pc._credential_env("https://u:p@host/r.git") as (u, env):
        assert u == "https://u:p@host/r.git"
        assert env is None


def test_credential_env_posix_strips_and_cleans_up(monkeypatch):
    """POSIX：凭据从 URL 剥离，改经 GIT_ASKPASS 注入；临时脚本退出后清理。"""
    monkeypatch.setattr(pc.os, "name", "posix")
    with pc._credential_env("https://u:p@host:8443/r.git?x=1") as (u, env):
        assert "u:p@" not in u
        assert u.startswith("https://host:8443/r.git")
        assert env is not None
        assert env["GIT_ASKPASS_PASS"] == "p"
        assert env["GIT_ASKPASS_USER"] == "u"
        askpass = env["GIT_ASKPASS"]
        assert os.path.isfile(askpass)
    assert not os.path.exists(askpass)


# ============================ 目录三态判定 ============================
def test_classify_target_missing(monkeypatch):
    monkeypatch.setattr(os.path, "isdir", lambda p: False)
    assert pc.classify_target("/nope") == "missing"


def test_classify_target_not_repo(monkeypatch):
    monkeypatch.setattr(os.path, "isdir", lambda p: True)
    monkeypatch.setattr(pc, "_git_toplevel", lambda local: "")
    assert pc.classify_target("/plain") == "not_repo"


def test_classify_target_repo(monkeypatch):
    monkeypatch.setattr(os.path, "isdir", lambda p: True)
    monkeypatch.setattr(pc, "_git_toplevel", lambda local: os.path.realpath(local))
    assert pc.classify_target("/repo") == "repo"


def test_classify_target_escape(monkeypatch):
    monkeypatch.setattr(os.path, "isdir", lambda p: True)
    monkeypatch.setattr(pc, "_git_toplevel", lambda local: os.path.realpath("/parent"))
    assert pc.classify_target("/parent/child") == "escape"


def test_git_repo_usable_self_root(monkeypatch):
    def fake(local, args, timeout=60):
        if args == ["rev-parse", "--show-toplevel"]:
            return 0, local + "\n"
        return 1, ""

    monkeypatch.setattr(pc, "_run_git", fake)
    monkeypatch.setattr(os.path, "isdir", lambda p: True)
    assert pc._git_repo_usable("/repo") is True


def test_git_repo_usable_escape(monkeypatch):
    def fake(local, args, timeout=60):
        if args == ["rev-parse", "--show-toplevel"]:
            return 0, "/parent\n"  # 顶层逃逸到父仓库
        return 1, ""

    monkeypatch.setattr(pc, "_run_git", fake)
    monkeypatch.setattr(os.path, "isdir", lambda p: True)
    assert pc._git_repo_usable("/parent/child") is False


# ============================ 变更集 / 工作树模式 ============================
def test_changed_vs_worktree(monkeypatch):
    def fake(local, args, timeout=60):
        if args == ["diff", "--name-only", "HEAD"]:
            # 已修改（未提交）的文件来自 diff；untracked/added 来自 status
            return 0, "a.py\nb.py\nmod.py\n"
        if args == ["status", "--porcelain"]:
            return 0, "?? new.py\n"
        return 1, ""

    monkeypatch.setattr(pc, "_run_git", fake)
    cf = pc.changed_vs_worktree("/x", "HEAD")
    assert "a.py" in cf and "b.py" in cf
    assert "new.py" in cf and "mod.py" in cf


def test_changed_vs_worktree_rename_takes_new_path(monkeypatch):
    """porcelain 'R  old -> new' 必须解析出**新**路径，而非整串。"""

    def fake(local, args, timeout=60):
        if args == ["diff", "--name-only", "HEAD"]:
            return 0, ""
        if args == ["status", "--porcelain"]:
            return 0, "R  old.py -> new.py\n"
        return 1, ""

    monkeypatch.setattr(pc, "_run_git", fake)
    cf = pc.changed_vs_worktree("/x", "HEAD")
    assert "new.py" in cf
    assert "old.py -> new.py" not in cf


def test_is_worktree_mode_sentinels():
    assert pc._is_worktree_mode("WORKTREE") is True
    assert pc._is_worktree_mode("worktree") is True
    assert pc._is_worktree_mode("") is True
    # HEAD 不再被当作工作树别名（避免 target_sha 恒空的歧义）
    assert pc._is_worktree_mode("HEAD") is False
    assert pc._is_worktree_mode("main") is False


def test_default_local_resolves_to_work_targets():
    """P0 回归守护：默认路径须指向 work/targets/research-agent（不得少/多一级 parent）。"""
    parts = pc.Path(pc.DEFAULT_LOCAL).parts
    assert parts[-3:] == ("work", "targets", "research-agent")
    assert "test-accel" not in parts


def test_pull_worktree_mode(monkeypatch, no_fs):
    def fake_local(local, args, timeout=60):
        if args == ["rev-parse", "--is-shallow-repository"]:
            return 0, "false\n"
        if args == ["diff", "--name-only", "HEAD"]:
            return 0, "changed.py\n"
        if args == ["status", "--porcelain"]:
            return 0, "?? untracked.py\n"
        if args[0] == "rev-parse" and args[1] == "--short":
            return 0, "abc123\n"
        return 1, ""

    monkeypatch.setattr(pc, "_run_git", fake_local)
    monkeypatch.setattr(pc, "classify_target", lambda local: "repo")
    monkeypatch.setattr(pc, "_net_git", lambda *a, **k: 0)

    res = pc.pull("", "/repo", "HEAD", "WORKTREE", 300, "")
    assert res["success"] is True
    assert res["status"] == "ok"
    assert "changed.py" in res["changed_files"]
    assert "untracked.py" in res["changed_files"]
    assert res["mode"] == "worktree"
    assert res["base_sha"] == "abc123"


# ============================ 失败 / 边界状态 ============================
def test_pull_escape_blocked(monkeypatch, no_fs):
    monkeypatch.setattr(pc, "classify_target", lambda local: "escape")
    res = pc.pull("", "/repo", "HEAD", "WORKTREE", 300, "")
    assert res["status"] == "repo_escape_blocked"
    assert res["success"] is False


def test_pull_clone_required_no_url(monkeypatch, no_fs):
    monkeypatch.setattr(pc, "classify_target", lambda local: "missing")
    res = pc.pull("", "/nope", "HEAD", "WORKTREE", 300, "")
    assert res["status"] == "clone_required_no_url"
    assert res["success"] is False


def test_pull_not_repo_no_url(monkeypatch, no_fs):
    """既存非 git 目录 + 无 url → 明确报"非仓库"，而非误判为逃逸。"""
    monkeypatch.setattr(pc, "classify_target", lambda local: "not_repo")
    res = pc.pull("", "/plain", "HEAD", "WORKTREE", 300, "")
    assert res["status"] == "clone_required_no_url"
    assert res["success"] is False
    assert any("不是 git 仓库" in e for e in res["errors"])


def test_pull_target_not_empty(monkeypatch, no_fs):
    """既存非空且非 git 目录 + 有 url → 明确报 target_not_empty（克隆无法写入）。"""
    monkeypatch.setattr(pc, "classify_target", lambda local: "not_repo")
    monkeypatch.setattr(pc, "_is_empty_dir", lambda p: False)
    res = pc.pull("https://host/x.git", "/plain", "HEAD", "WORKTREE", 300, "")
    assert res["status"] == "target_not_empty"
    assert res["success"] is False


def test_pull_refs_unavailable(monkeypatch, no_fs):
    """双 ref 模式下两个 ref 均不可解析且离线 → refs_unavailable。"""

    def fake_local(local, args, timeout=60):
        if args == ["rev-parse", "--is-shallow-repository"]:
            return 0, "false\n"
        if args in (["rev-parse", "--quiet", "base"], ["rev-parse", "--quiet", "target"]):
            return 1, ""  # ref 不可解析
        if args[0] == "rev-parse" and args[1] == "--short":
            return 0, "abc\n"
        return 1, ""

    monkeypatch.setattr(pc, "_run_git", fake_local)
    monkeypatch.setattr(pc, "classify_target", lambda local: "repo")
    monkeypatch.setattr(pc, "_net_git", lambda *a, **k: 1)  # 离线：fetch 失败
    res = pc.pull("", "/repo", "base", "target", 300, "")
    assert res["status"] == "refs_unavailable"
    assert res["success"] is False


# ============================ 枚举单源一致性 ============================
def test_pull_status_matches_platform():
    """scripts 本地枚举须与 backend/core/enums.py::PullStatus 逐值一致（枚举单源）。"""
    local = {s.value for s in pc.PullStatus}
    platform = {s.value for s in PlatformPullStatus}
    assert local == platform, f"本地={sorted(local)} 平台={sorted(platform)}"
