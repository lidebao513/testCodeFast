#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""生成/同步仓库根 SKILLS.md 技能索引。

扫描用户级 + 项目级 skills 目录，解析每个 SKILL.md 的 name / description，
写出仓库根 SKILLS.md（git 跟踪）。每次新增 / 改名 / 改技能后重跑本脚本即可同步。

用法：
    python work/gen_skills_index.py
    python work/gen_skills_index.py --out SKILLS.md
"""
import argparse
import io
import os
import re

# 用户级技能根目录（跨项目可用）
USER_SKILLS = os.path.expanduser("~/.workbuddy/skills")
# 项目级技能根目录（随仓库共享给协作者）——本仓库当前无此目录，保留扩展位
PROJECT_SKILLS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    ".workbuddy", "skills"
)
# 仓库根（SKILLS.md 落点）
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _strip(s):
    """去掉 YAML 引号与折叠标记。"""
    s = s.strip()
    if len(s) >= 2 and s[0] in "\"'" and s[-1] == s[0]:
        s = s[1:-1]
    return s.strip()


def _parse_frontmatter(path):
    """读取 SKILL.md 的 name / description 字段（YAML 首段）。

    支持：普通标量、双/单引号、以及 `>` / `|` 折叠/字面块标量（多行）。
    """
    name = desc = ""
    try:
        with io.open(path, "r", encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return name, desc
    if not text.startswith("---"):
        return name, desc
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, re.S)
    if not m:
        return name, desc
    block = m.group(1)
    lines = block.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("name:"):
            name = _strip(line[len("name:"):])
            i += 1
        elif line.startswith("description:"):
            val = line[len("description:"):].strip()
            if val in (">", "|", ">-", "|-", ">+", "|+"):
                # 折叠块：收集后续缩进行
                parts = []
                i += 1
                while i < len(lines) and (lines[i].startswith(" ") or lines[i].startswith("\t")):
                    parts.append(lines[i].strip())
                    i += 1
                desc = " ".join(parts)
            else:
                desc = _strip(val)
                i += 1
        else:
            i += 1
    return name, desc


def _scan(root):
    """返回 [(name, dirname, abs_path, description, contents)]，排除备份目录。"""
    if not os.path.isdir(root):
        return []
    out = []
    for d in sorted(os.listdir(root)):
        full = os.path.join(root, d)
        if not os.path.isdir(full):
            continue
        if d.endswith(".bak") or re.search(r"\.bak\.\d{8}$", d):
            continue  # 跳过备份（如 skills.bak.20260908）
        skill = os.path.join(full, "SKILL.md")
        if not os.path.isfile(skill):
            continue
        name, desc = _parse_frontmatter(skill)
        contents = sorted(
            f for f in os.listdir(full)
            if f != "SKILL.md" and not f.startswith(".")
        )
        out.append((name or d, d, full, desc, contents))
    return out


def build_markdown(skills_user, skills_proj):
    L = []
    L.append("# 项目技能索引（Skills Index）\n")
    L.append("> 本文件由 `work/gen_skills_index.py` 自动扫描 `~/.workbuddy/skills/` 生成。"
             "每次新增 / 改名 / 修改技能后，重跑该脚本即可同步，**请勿手改**。\n")
    total = len(skills_user) + len(skills_proj)
    L.append(f"技能总数：**{total}**（用户级 {len(skills_user)}"
             + (f" / 项目级 {len(skills_proj)}" if skills_proj else "") + "）\n")

    def _friendly_path(full):
        home = os.path.expanduser("~").rstrip("/\\")
        if full.startswith(home):
            return "~" + full[len(home):].replace("\\", "/")
        return os.path.relpath(full, REPO_ROOT).replace("\\", "/")

    def _table(title, rows):
        L.append(f"## {title}\n")
        L.append("| 技能名 | 目录 | 路径 | 目录内容 | 说明 |")
        L.append("|---|---|---|---|---|")
        for name, d, full, desc, contents in rows:
            rel = _friendly_path(full)
            c = "、".join(contents) if contents else "—"
            L.append(f"| `{name}` | `{d}` | `{rel}` | {c} | {desc} |")
        L.append("")

    if skills_user:
        _table("用户级技能（~/.workbuddy/skills/ · 跨项目可用）", skills_user)
    if skills_proj:
        _table("项目级技能（{ws}/.workbuddy/skills/ · 随仓库共享）", skills_proj)

    L.append("## 调用顺序（QA 域）\n")
    L.append("1. **先 `qa-code-pull`**：备好被测代码（仓库就位、工作树=目标版本、产出 `.pull_result.json`）。")
    L.append("2. **后 `qa-test-points`**：经环境变量 `CHANGED_FILES_JSON` 指向该 JSON **解耦消费**变更集（不 import、不调 git），生成测试点。\n")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(REPO_ROOT, "SKILLS.md"))
    args = ap.parse_args()

    user = _scan(USER_SKILLS)
    proj = _scan(PROJECT_SKILLS)
    md = build_markdown(user, proj)

    with io.open(args.out, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"WROTE {args.out}")
    print(f"  用户级 {len(user)} 个 / 项目级 {len(proj)} 个")


if __name__ == "__main__":
    main()
