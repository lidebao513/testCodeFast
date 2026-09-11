"""阶段2 A1 / A2 / C1 自测。

A1 功能点业务语义：每个功能点都有 fp_id / module / action / semantic / impl / title。
A2 双向追溯：TP→FP（fp_id 命中 fp_index）、FP→TP（test_points 列表）、孤儿 TP = 0。
C1 统一契约 + 去重扫描：契约版本一致、字段齐全、同文件只读一次（text_requests > files_read）。

用法：
    python selftest_a1_a2_c1.py
退出码：0=全部通过，1=存在失败断言。
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from backend.modules.code_analyzer import (
    FP_CONTRACT_VERSION,
    compute_diff_changed_files,
    compute_diff_hunks,
    fp_id_of,
    generate_comprehensive_test_points,
)


REAL_REPO = Path(r"C:/Users/EDY/WorkBuddy/testCodeFast/work/targets/research-agent")

FAILS = []
PASSES = []


def check(name, cond, detail=""):
    if cond:
        PASSES.append(name)
        print(f"  [PASS] {name}" + (f" — {detail}" if detail else ""))
    else:
        FAILS.append(name)
        print(f"  [FAIL] {name}" + (f" — {detail}" if detail else ""))


def git(repo, *args, env=None):
    return subprocess.run(
        ["git", "-C", str(repo)] + list(args), capture_output=True, text=True, env=env, timeout=60
    )


# ---------------------------------------------------------------- fixture
APP_V1 = '''"""主服务：对外 HTTP 接口。"""
from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health():
    """健康检查：返回服务存活状态。"""
    return {"ok": True}


@app.post("/login")
def login():
    """用户登录：校验账号密码并下发访问令牌。"""
    return {"token": "x"}


@app.get("/chat-stream")
async def chat_stream():
    """对话流式输出：逐 token 推送模型回复。"""
    return {"ok": True}


@app.get("/items/{item_id}")
def get_item(item_id: str):
    """查询条目详情：按 item_id 返回单条记录。"""
    return {}
'''

APP_V2 = APP_V1.replace(
    '    return {"token": "x"}',
    '    # 新增：登录失败计数（本次变更只改这一个函数）\n    return {"token": "x"}',
)

BRIEFING = '''"""晨会简报生成。"""


def build_brief():
    """组装晨会简报正文。"""
    return ""


def send_brief():
    """推送晨会简报给订阅人。"""
    return True
'''

# 动态发现用例：不在 _CORE_MODULES 里、也无路由，只能靠 discover_business_modules 发现
LEAVE_SERVICE = '''"""请假服务：年假余额与申请流转。"""


def calc_balance():
    """计算年假余额（按入职日期折算）。"""
    return 0


def apply_leave():
    """提交请假申请并扣减余额。"""
    return True


def cancel_leave():
    """取消请假申请并回滚余额。"""
    return True
'''

ROUTER_JS = """export default new Router({
  routes: [
    { path: '/home', component: Home },
    { path: '/login', component: Login },
  ],
})
"""

COMP_VUE = """<template>
  <div><button @click="submit">提交</button></div>
</template>
<script>
export default { name: 'MyForm' }
</script>
"""


def build_fixture():
    """造一个最小 git 仓库：base 提交 → 只改 login 函数 → target 提交。"""
    tmp = Path(tempfile.mkdtemp(prefix="tp_a1a2c1_"))
    env = dict(
        os.environ,
        GIT_AUTHOR_NAME="t",
        GIT_AUTHOR_EMAIL="t@t",
        GIT_COMMITTER_NAME="t",
        GIT_COMMITTER_EMAIL="t@t",
    )
    git(tmp, "init", "-q")
    (tmp / "app.py").write_text(APP_V1, encoding="utf-8")
    (tmp / "briefing.py").write_text(BRIEFING, encoding="utf-8")
    (tmp / "tools").mkdir()
    (tmp / "tools" / "leave_service.py").write_text(LEAVE_SERVICE, encoding="utf-8")
    (tmp / "frontend").mkdir()
    (tmp / "frontend" / "router.js").write_text(ROUTER_JS, encoding="utf-8")
    (tmp / "frontend" / "MyForm.vue").write_text(COMP_VUE, encoding="utf-8")
    git(tmp, "add", "-A", env=env)
    git(tmp, "commit", "-q", "-m", "base", env=env)
    git(tmp, "tag", "base", env=env)
    (tmp / "app.py").write_text(APP_V2, encoding="utf-8")
    git(tmp, "add", "-A", env=env)
    git(tmp, "commit", "-q", "-m", "target: change login", env=env)
    git(tmp, "tag", "target", env=env)
    return tmp


def run(repo, base=None, target=None, scopes=None):
    changed = compute_diff_changed_files(str(repo), base, target) if base else set()
    hunks = compute_diff_hunks(str(repo), base, target) if base else {}
    return generate_comprehensive_test_points(
        str(repo),
        project_type="pc",
        changed_files=changed,
        scopes=scopes,
        diff_hunks=hunks,
        diff_target=target,
    )


# ---------------------------------------------------------------- 用例
def test_fixture():
    print("\n=== 用例1：受控 fixture 仓库（base..target 只改 login 函数）===")
    tmp = build_fixture()
    try:
        data = run(tmp, "base", "target", scopes={"正常", "异常"})
        tps = data["test_points"]
        fps = data["functional_points"]
        tr = data["traceability"]
        ss = data["scan_stats"]

        # ---- A1：功能点业务语义 ----
        print("\n[A1] 功能点业务语义")
        miss = [
            f["fp_id"]
            for f in fps
            if not (
                f.get("semantic")
                and f.get("module")
                and f.get("action")
                and f.get("title")
                and f.get("fp_id")
            )
        ]
        check(
            "A1-1 每个功能点都有 fp_id/module/action/semantic/title",
            not miss,
            f"缺失 {len(miss)} 个；功能点总数 {len(fps)}",
        )
        api_fps = [f for f in fps if f["ftype"] == "api"]
        check(
            "A1-2 api 功能点带结构化 method/path 字段",
            all(f.get("method") and f.get("path") for f in api_fps),
            f"api 功能点 {len(api_fps)} 个",
        )
        impl_fps = [f for f in api_fps if f.get("impl")]
        check(
            "A1-3 api 功能点补出实现函数(impl)",
            len(impl_fps) == len(api_fps),
            f"{len(impl_fps)}/{len(api_fps)}；样例：{impl_fps[0]['impl'] if impl_fps else '-'}",
        )
        login_fp = [f for f in api_fps if f["path"] == "/login"]
        check(
            "A1-4 业务语义正确归类（/login → 账户/用户/鉴权 · 登录鉴权）",
            bool(login_fp) and login_fp[0]["semantic"] == "账户/用户/鉴权 · 登录鉴权",
            login_fp[0]["semantic"] if login_fp else "未找到 /login",
        )
        check(
            "A1-5 功能点带源码位置 loc（hunk 打标与跳转用）",
            any(f.get("loc") for f in api_fps),
            f"样例 loc={login_fp[0].get('loc') if login_fp else None}",
        )
        check(
            "A1-6 业务函数也升级为功能点(business)且带语义",
            all(f.get("semantic") for f in fps if f["ftype"] == "business"),
            f"business 功能点 {len([f for f in fps if f['ftype'] == 'business'])} 个",
        )

        # ---- 业务模块发现（显式清单 + 动态补足）----
        print("\n[业务模块发现] 显式清单 + 动态补足")
        biz_fps = [f for f in fps if f["ftype"] == "business"]
        check(
            "BM-1 显式清单命中（briefing.py 在 _CORE_MODULES 中）",
            any("briefing.py::" in f["name"] for f in biz_fps),
        )
        check(
            "BM-2 动态发现补足（leave_service.py 不在任何显式清单）",
            any("leave_service.py::" in f["name"] for f in biz_fps),
            f"business 功能点 {len(biz_fps)} 个",
        )
        check(
            "BM-3 路由主导文件不再重复抽取（app.py 已由 api 维度覆盖）",
            not any("app.py::" in f["name"] for f in biz_fps),
        )
        priv = [f["name"] for f in biz_fps if f["name"].split("::")[-1].startswith("_")]
        check("BM-4 业务函数只取公共符号（过滤 _ 私有实现）", not priv, f"私有符号 {len(priv)} 个")

        # ---- A2：双向追溯 ----
        print("\n[A2] 双向追溯")
        idx = data["fp_index"]
        orphan = [r["id"] for r in tps if r.get("fp_id") not in idx]
        check(
            "A2-1 TP→FP：每条测试点都能命中 fp_index（无孤儿）",
            not orphan,
            f"孤儿 {len(orphan)} 条",
        )
        back_ok = True
        for r in tps:
            if r["id"] not in idx[r["fp_id"]]["test_points"]:
                back_ok = False
        check("A2-2 FP→TP：功能点反查列表包含其全部派生测试点", back_ok)
        check(
            "A2-3 traceability 统计自洽",
            tr["tp_with_fp"] + tr["tp_without_fp(orphan)"] == tr["tp_total"]
            and tr["fp_with_tp"] + tr["fp_without_tp"] == tr["fp_total"],
            f"FP {tr['fp_total']}（有派生 {tr['fp_with_tp']}）/ "
            f"TP {tr['tp_total']}（孤儿 {tr['tp_without_fp(orphan)']}）",
        )
        sample = [f for f in fps if len(f.get("test_points", [])) > 1]
        check(
            "A2-4 一个功能点可派生多条测试点（四维展开）",
            bool(sample),
            f"样例 {sample[0]['name'] if sample else '-'} → "
            f"{len(sample[0]['test_points']) if sample else 0} 条",
        )

        # ---- C1：统一契约 + 去重扫描 ----
        print("\n[C1] 统一契约 + 去重扫描")
        check(
            "C1-1 契约版本一致",
            data.get("contract_version") == FP_CONTRACT_VERSION,
            f"v{data.get('contract_version')}",
        )
        check(
            "C1-2 fp_id 稳定（同输入两次运行 ID 不变）",
            run(tmp, "base", "target", scopes={"正常", "异常"})["fp_index"].keys() == idx.keys(),
            f"{len(idx)} 个 fp_id",
        )
        check(
            "C1-3 fp_id 由内容决定（ftype|file|name 哈希，与顺序无关）",
            fp_id_of("api", "app.py", "POST /login") == fp_id_of("api", "app.py", "POST /login")
            and fp_id_of("api", "app.py", "POST /login")
            != fp_id_of("api", "app.py", "GET /health"),
        )
        check(
            "C1-4 去重扫描：重复请求被缓存吸收（text_requests > files_read）",
            ss["text_requests"] > ss["files_read"] > 0,
            f"请求 {ss['text_requests']} 次 → 实际读 {ss['files_read']} 个"
            f"（缓存命中 {ss['text_cache_hits']}）",
        )
        check(
            "C1-5 每个 (文件,版本) 只解析一次 AST",
            ss["ast_parses"] <= ss["files_read"],
            f"ast_parses={ss['ast_parses']} files_read={ss['files_read']}",
        )

        # ---- 与 B1 的交叉验证：hunk 精度未被破坏 ----
        print("\n[B1 回归] hunk 级打标精度")
        upd = [r for r in tps if r["tag"] == "更新"]
        check(
            "B1-1 仅变更函数(login)的测试点被标『更新』",
            bool(upd) and all(r["area"] == "/login" for r in upd),
            f"更新 {len(upd)} 条，area={sorted({r['area'] for r in upd})}",
        )
        check(
            "B1-2 未变更路由仍为『全量』",
            all(
                r["tag"] == "全量"
                for r in tps
                if r["area"] in ("/health", "/chat-stream", "/items/{item_id}")
            ),
            f"全量 {len([r for r in tps if r['tag'] == '全量'])} 条",
        )

        print(
            "\n  fixture 概览："
            f"FP={tr['fp_total']} TP={tr['tp_total']} "
            f"更新={len(upd)} 覆盖={tr['coverage']}"
        )
        return data
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_real_repo():
    print("\n=== 用例2：真实仓库 research-agent 回归（无有效 diff 基线）===")
    if not REAL_REPO.exists():
        print("  [SKIP] 被测仓库不存在")
        return None
    data = run(REAL_REPO, None, None, scopes={"正常", "异常"})
    tps = data["test_points"]
    fps = data["functional_points"]
    tr = data["traceability"]
    ss = data["scan_stats"]
    print(
        f"  TP={len(tps)} FP={tr['fp_total']} 覆盖={tr['coverage']} "
        f"孤儿={tr['tp_without_fp(orphan)']}"
    )

    check("R-1 真实仓库不报错且产出测试点", len(tps) > 0, f"{len(tps)} 条")
    check(
        "R-2 测试点全部带 fp_id 且可追溯",
        all(r.get("fp_id") in data["fp_index"] for r in tps),
        f"孤儿 {tr['tp_without_fp(orphan)']} 条",
    )
    check(
        "R-3 功能点业务语义覆盖率 100%",
        all(f.get("semantic") for f in fps),
        f"{sum(1 for f in fps if f.get('semantic'))}/{len(fps)}",
    )
    check(
        "R-4 测试点业务语义覆盖率 100%（B2 未回退）",
        all(r.get("semantic") for r in tps),
        f"{sum(1 for r in tps if r.get('semantic'))}/{len(tps)}",
    )
    check(
        "R-5 去重扫描生效（真实仓库重复请求被缓存吸收）",
        ss["text_requests"] > ss["files_read"] > 0,
        f"请求 {ss['text_requests']} 次 → 读 {ss['files_read']} 个，"
        f"缓存命中 {ss['text_cache_hits']}",
    )
    check(
        "R-6 无有效 diff 基线时全部标『全量』（不误标）",
        all(r["tag"] == "全量" for r in tps),
        f"by_tag={data['by_tag']}",
    )
    by_ftype = {}
    for f in fps:
        by_ftype[f["ftype"]] = by_ftype.get(f["ftype"], 0) + 1
    biz_fps2 = [f for f in fps if f["ftype"] == "business"]
    check(
        "R-7 业务函数维度已从 0 恢复（动态发现生效）",
        len(biz_fps2) > 0,
        f"business 功能点 {len(biz_fps2)} 个，业务域：{sorted({f['module'] for f in biz_fps2})}",
    )
    check(
        "R-8 业务功能点均带实现说明(impl)或函数名",
        all(f.get("impl") for f in biz_fps2),
        f"{sum(1 for f in biz_fps2 if f.get('impl'))}/{len(biz_fps2)}",
    )
    print(f"  功能点类型分布：{by_ftype}")
    return data


def main():
    print("=" * 78)
    print(f"阶段2 A1/A2/C1 自测（契约 v{FP_CONTRACT_VERSION}）")
    print("=" * 78)
    d1 = test_fixture()
    d2 = test_real_repo()

    # 产物留档（便于人工核对追溯矩阵）
    out = Path(r"C:/Users/EDY/WorkBuddy/testCodeFast/work/research-agent-test")
    out.mkdir(parents=True, exist_ok=True)
    if d2:
        (out / "_selftest_a1a2c1_real.json").write_text(
            json.dumps(
                {
                    "traceability": d2["traceability"],
                    "scan_stats": d2["scan_stats"],
                    "functional_points": d2["functional_points"][:40],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    print("\n" + "=" * 78)
    print(f"结果：PASS {len(PASSES)} / FAIL {len(FAILS)}")
    if FAILS:
        for f in FAILS:
            print(f"  ✗ {f}")
    print("=" * 78)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
