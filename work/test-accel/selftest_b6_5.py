"""阶段6 批次4 增补自测：用例:测试点 映射策略（CASE_PER_TP）。

验证 three 模式（one/split/merge）下：
  1. 默认 one 模式向后兼容（测试点数 == 用例数，键两元组）。
  2. split 模式 1:N（测试点数 < 用例数），键唯一、title 带维度前缀、tc_no 带 ::维度。
  3. merge 模式 N:1（测试点数 > 用例数），按 fp_contract_id 去重。
  4. 模式间切换后 C-②8 对账不误判（键稳定）。
纯构造验证 + 落库统计，不跑执行器。
"""

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

PASS = 0
FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        print(f"  FAIL  {name}  {detail}")


from backend.db import get_conn
from backend.modules import case_generator as cg


gen = cg.CaseGenerator()

conn = get_conn()
PID = conn.execute("SELECT id FROM projects WHERE name='research-agent'").fetchone()[0]
n_tp = conn.execute("SELECT COUNT(*) FROM test_points WHERE project_id=2").fetchone()[0]
conn.close()

print(f"research-agent pid={PID}, 测试点总数={n_tp}\n")


# 构造 specs（三种模式，不写库）
def build_specs(mode):
    c = get_conn()
    cur = c.cursor()
    cur.execute("SELECT id, contract_id FROM functional_points WHERE project_id=2")
    fp_map = {r["contract_id"]: r["id"] for r in cur.fetchall() if r["contract_id"]}
    cur.execute("SELECT * FROM test_points WHERE project_id=2 ORDER BY id")
    tps = [dict(r) for r in cur.fetchall()]
    c.close()
    dims = ["正常", "边界", "异常", "安全"]
    specs = []
    for tp in tps:
        if mode == "split":
            for sk in dims:
                specs.append(gen._build_from_tp(tp, fp_map, split_key=sk))
        elif mode == "merge":
            specs.append(gen._build_from_tp(tp, fp_map))
        else:
            specs.append(gen._build_from_tp(tp, fp_map))
    if mode == "merge":
        merged, seen = [], set()
        for s in specs:
            fk = s.get("fp_contract_id")
            if fk and fk in seen:
                continue
            if fk:
                seen.add(fk)
            merged.append(s)
        specs = merged
    return specs


print("== 模式一：one（默认，向后兼容）==")
one = build_specs("one")
check("one 用例数 == 测试点数", len(one) == n_tp, f"{len(one)} vs {n_tp}")
keys_one = [gen._case_key(s) for s in one]
check("one 键为两元组 ('tp', tp_id)", all(len(k) == 2 and k[0] == "tp" for k in keys_one))
check("one 键无重复", len(keys_one) == len(set(keys_one)))

print("\n== 模式二：split（1:N，测试点 < 用例）==")
split = build_specs("split")
check("split 用例数 > 测试点数", len(split) > n_tp, f"{len(split)} vs {n_tp}")
check("split 比例 = 4（4 维度）", len(split) == n_tp * 4, f"{len(split)} vs {n_tp * 4}")
keys_split = [gen._case_key(s) for s in split]
check("split 键为三元组 ('tp', tp_id, dim)", all(len(k) == 3 and k[0] == "tp" for k in keys_split))
check("split 键无重复（同 TP 不同维度互不冲突）", len(keys_split) == len(set(keys_split)))
# 抽查：同一 TP 拆出 4 条，标题维度前缀不同，tc_no 带 ::维度
t0 = split[0]["tp_id"]
same_tp = [s for s in split if s["tp_id"] == t0]
check("同 TP 拆出 4 条", len(same_tp) == 4, f"{len(same_tp)}")
check("标题维度前缀唯一", len(set(s["case_type"] for s in same_tp)) == 4)
check("tc_no 带 ::维度后缀", all("::" in (s["tc_no"] or "") for s in same_tp))

print("\n== 模式三：merge（N:1，测试点 > 用例）==")
merge = build_specs("merge")
check("merge 用例数 < 测试点数", len(merge) < n_tp, f"{len(merge)} vs {n_tp}")
check(
    "merge 按 fp 去重（用例数 == 去重 fp 数）",
    len(merge) == len(set(s["fp_contract_id"] for s in merge if s["fp_contract_id"])),
)
keys_merge = [gen._case_key(s) for s in merge]
check("merge 键无重复", len(keys_merge) == len(set(keys_merge)))

print("\n== 键稳定性（模式切换后 C-②8 不误判）==")
# one 与 split 的键空间互不重叠（split 用三元组，one 用两元组），故切换不会误 match
one_set = set(keys_one)
split_set = set(keys_split)
check("one/split 键空间不重叠", one_set.isdisjoint(split_set))

print(f"\n===== {PASS} PASSED / {FAIL} FAILED =====")
sys.exit(1 if FAIL else 0)
