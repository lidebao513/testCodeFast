"""增量对比分析器：对比两个 git ref 之间的代码变更，产出"功能点差异"。

用途：回答"这次改了什么、哪些功能点是新增/被删/被动过的"，只针对变更文件做分析，
避免每次全量重扫（对应 main.py 顶部注释里的"增量回归"）。

实现要点：
1. 变更文件：`git diff --name-status <base>..<head>`，状态 A=新增 M=修改 D=删除 R=重命名
2. 历史版本内容：`git show <ref>:<path>` —— 关键：已删除(D)的文件在工作区已不存在，
   只能靠 git show 从基线取回旧内容才能分析出"被删掉了哪些功能点"
3. 三向分类（以 (ftype, file_path, name) 为 key）：
   - new     = 新分支有、基线没有  → 需要新增用例
   - removed = 基线有、新分支没有  → 对应功能已下线，用例应废弃
   - updated = 两边都有，但文件被改过(M/R) → 功能仍在但实现变了，需回归验证

只读：本模块对目标仓库只执行 git diff / show / rev-parse，绝不写仓库。
"""
import subprocess
import time
from backend.modules.code_analyzer import code_analyzer

# 只分析代码文件，过滤 md/json/yaml/png 等，显著减少 git show 调用
_CODE_EXTS = (".py", ".ts", ".tsx", ".js", ".jsx", ".vue")

_STATUS_LABEL = {
    "A": "新增",
    "M": "修改",
    "D": "删除",
    "R": "重命名",
    "T": "类型变更",
    "C": "复制",
}


class DiffAnalyzer:
    # ---------- git 只读封装 ----------

    @staticmethod
    def _git(local_path, args, timeout=60):
        try:
            out = subprocess.run(
                ["git", "-C", local_path] + args,
                capture_output=True, text=True, timeout=timeout,
                errors="ignore",
            )
            if out.returncode != 0:
                return None
            return out.stdout
        except Exception:
            return None

    def resolve(self, local_path: str, ref: str) -> str:
        """把 ref 解析成 commit sha，失败返回空串。"""
        out = self._git(local_path, ["rev-parse", ref])
        return out.strip() if out else ""

    def changed_files(self, local_path: str, base: str, head: str):
        """返回 [(status, path), ...]，status 为首字母 A/M/D/R/T/C。"""
        out = self._git(local_path, ["diff", "--name-status", f"{base}..{head}"],
                        timeout=120)
        if not out:
            return []
        items = []
        for line in out.splitlines():
            line = line.rstrip()
            if not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) >= 2:
                st = parts[0].strip()[:1]
                path = parts[-1].strip()   # 重命名 R 时取新路径
            else:
                seg = line.split(None, 1)
                if len(seg) != 2:
                    continue
                st, path = seg[0][:1], seg[1].strip()
            if st and path:
                items.append((st, path))
        return items

    def file_content(self, local_path: str, ref: str, path: str):
        """取某 ref 下某文件的内容；文件在该 ref 不存在时返回 None。"""
        return self._git(local_path, ["show", f"{ref}:{path}"], timeout=30)

    # ---------- 主流程 ----------

    def analyze_diff(self, local_path: str, base: str, head: str,
                     project_type: str = "pc", max_files: int = 3000,
                     include_files: bool = False):
        t0 = time.time()
        base_commit = self.resolve(local_path, base)
        head_commit = self.resolve(local_path, head)
        if not base_commit or not head_commit:
            return {"ok": False,
                    "error": f"ref 无法解析（base={base} head={head}），"
                             f"请确认分支/commit 存在于 {local_path}"}

        raw = self.changed_files(local_path, base, head)
        by_status = {}
        for st, _p in raw:
            by_status[st] = by_status.get(st, 0) + 1

        code_pairs = [(st, p) for st, p in raw if p.lower().endswith(_CODE_EXTS)]
        truncated = len(code_pairs) > max_files
        if truncated:
            code_pairs = code_pairs[:max_files]

        # 分别取基线侧与新版本侧的内容
        # A(新增)：基线没有该文件 → 只取新版本
        # D(删除)：新版本没有该文件 → 只取基线（否则分析不出被删的功能点）
        old_map, new_map = {}, {}
        calls = 0
        for st, p in code_pairs:
            if st != "A":
                txt = self.file_content(local_path, base, p)
                calls += 1
                if txt is not None:
                    old_map[p] = txt
            if st != "D":
                txt = self.file_content(local_path, head, p)
                calls += 1
                if txt is not None:
                    new_map[p] = txt

        old_fps = code_analyzer.analyze_content_map(old_map, project_type)
        new_fps = code_analyzer.analyze_content_map(new_map, project_type)

        def key(fp):
            return (fp["ftype"], fp["file_path"], fp["name"])

        old_k = {key(fp): fp for fp in old_fps}
        new_k = {key(fp): fp for fp in new_fps}

        def srt(fps):
            return sorted(fps, key=lambda x: (x["file_path"], x["name"]))

        new_list = srt([new_k[k] for k in (new_k.keys() - old_k.keys())])
        removed_list = srt([old_k[k] for k in (old_k.keys() - new_k.keys())])
        # 交集：两边都有 = 功能点仍在，但所属文件属于 M/R（被改过）→ 需回归
        updated_list = srt([new_k[k] for k in (new_k.keys() & old_k.keys())])

        result = {
            "ok": True,
            "base": base,
            "head": head,
            "base_commit": base_commit[:12],
            "head_commit": head_commit[:12],
            "changed_files": {
                "total": len(raw),
                "code_files": len(code_pairs),
                "by_status": {k: v for k, v in sorted(by_status.items())},
                "by_status_label": {_STATUS_LABEL.get(k, k): v
                                    for k, v in sorted(by_status.items())},
            },
            "fp_diff": {
                "new": len(new_list),
                "updated": len(updated_list),
                "removed": len(removed_list),
                "baseline_fp_total": len(old_fps),
                "current_fp_total": len(new_fps),
            },
            "new_fps": new_list,
            "updated_fps": updated_list,
            "removed_fps": removed_list,
            "stats": {
                "git_show_calls": calls,
                "truncated": truncated,
                "elapsed_s": round(time.time() - t0, 2),
            },
        }
        if include_files:
            result["changed_file_list"] = [
                {"status": st, "label": _STATUS_LABEL.get(st, st), "path": p}
                for st, p in code_pairs
            ]
        return result


diff_analyzer = DiffAnalyzer()
