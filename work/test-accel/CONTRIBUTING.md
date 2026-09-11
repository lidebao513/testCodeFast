# CONTRIBUTING.md —— 变更规则（优化/生成前的协作约束）

> 本文件与 `ARCHITECTURE.md`、`ADR/` 共同构成项目护栏。任何人在本项目提交代码
> （含 AI 自动生成）前，必须遵守以下规则。违反项会被 pre-commit / CI 拦截至提交前。

---

## 0. 提交前必须做的（自动门禁）

```bash
# 1) 安装钩子（一次性）
pip install pre-commit ruff mypy bandit pytest pytest-cov && pre-commit install

# 2) 统一门禁入口（一次性跑全 7 项，CI 与 pre-commit 都调用它）
python scripts/gate_all.py
#   → ruff lint + ruff format --check + check_enums + check_structure
#     + mypy(backend) + bandit(medium) + pytest(cov)
#   全部 OK 才退出 0；任一失败立即非零退出并定位到具体环节。

# 3) 也可单独跑某一环（调试用）：
python scripts/check_enums.py      # 枚举单源门禁，必须 0 违规
python scripts/check_structure.py  # 架构结构门禁，必须 0 error
python -m pytest tests/ -q         # 冒烟测试必须全绿

# 4) 远程 CI（.github/workflows/guard.yml）会在 push/PR 重跑 gate_all.py
```

> 质量工具推荐装在托管 Python 环境（`~/.workbuddy/binaries/python/envs/default`），
> `gate_all.py` 会自动按 `shutil.which → 托管环境 → python -m <name>` 三级解析可执行，
> 无需在每次提交机器上手动 `pip install` 全部工具。

---

## 1. 枚举变更规则（最高频坑）

- **改枚举只改一处**：所有枚举值在 `backend/core/enums.py`。新增/修改枚举值，
  在此文件改，并同步更新 `enums.py` 内的解析/推导函数。
- **禁止硬编码**：业务代码里不要写 `"正常"`/`"api"`/`"pass"` 等枚举字面量做字段赋值/比较，
  改为 `from backend.core.enums import TPType, ...`。`check_enums.py` 会拦截。
- **文档同步**：若 `qa-*/SKILL.md` 引用了枚举，更新后需与之保持一致（文档不定义行为）。

---

## 2. 目录与分层规则

- **新脚本不落根目录**：命令入口进 `backend/cli/`，一次性工具进 `scripts/`，测试进 `tests/`。
  根目录 `gen_/selftest_/run_/verify_*.py` 为历史债务，迁移见 `ARCHITECTURE.md §5`。
- **依赖方向**：`cli/service → modules → core`，禁止反向。`core/` 不依赖任何上层
  （保证引擎可被 skill 独立引用）。`check_structure.py` 强制此方向。
- **模块职责**：算法在 `modules/`，HTTP 接入在 `service/`，参数解析在 `cli/`。

---

## 3. 数据契约规则

- **测试点必含 `verify_layer`**：`code_analyzer` 生成的每条测试点必须有 `verify_layer`
  （`接口`/`UI`）。如需调整推导逻辑，改 `enums.derive_verify_layer`，不要绕过注入。
- **产物向后兼容**：`test_points_*.json` / `structured_cases.json` 的字段变更，
  必须保证既有消费方（executor、报告生成器）不报错；破坏性变更走 ADR。
- **标签语义稳定**：`tag` ∈ {全量, 更新}；`tp_type` ∈ {正常,异常,安全,边界}；
  执行层 `verify_layer` ∈ {接口, UI}。三者独立维度，不混用。

---

## 4. 文档与决策规则

- **架构变更走 ADR**：涉及分层、枚举体系、服务化定位、数据契约的变更，
  先在 `ADR/` 写决策记录（背景/选项/决定/后果），再改代码。已有 `ADR-0001`。
- **README/文档与代码一致**：文档描述的范围/默认值/枚举，以 `enums.py` 与代码为准。

---

## 5. 安全与入库规则

- **密钥不入库**：`.env` 已忽略；新增密钥只进 `.env`，模板进 `.env.example`。
- **第三方被测代码不入库**：`work/targets/` 已忽略；若曾被跟踪，执行
  `git rm --cached -r work/targets` 从索引移除（文件保留本地）。
- **不提交大产物**：`data/reports/*`、`data/screenshots/*`、`*.db` 已忽略。

---

## 6. AI 自动生成时的额外约束

当由 AI（含本助手）在「整体优化」阶段生成/重构代码时：
1. 先读 `ARCHITECTURE.md` + `ADR/` + `enums.py`，确认边界；
2. 生成后必须让 `python scripts/gate_all.py` 全绿（含 lint/format/enum/structure/type/security/test）再交付；
3. 不得为「图省事」把逻辑堆回根目录脚本或 `modules/` 上帝模块；
4. 重大结构变更必须先提 ADR，不得静默改写本文。

---

## 7. 提交信息 / 分支 / PR 规范（被 `commit-msg` 钩子强制）

> 目的：让提交历史可读、可自动生成 CHANGELOG、便于追溯「为什么改」。

### 7.1 提交信息（Conventional Commits）
格式：`type(scope): subject`，可选正文与脚注（BREAKING CHANGE / 关联 Issue）。

- **type**（必填，小写其一）：
  `feat`(新功能) / `fix`(缺陷修复) / `refactor`(重构，无行为变化) /
  `docs`(文档) / `test`(测试) / `chore`(构建/依赖/杂项) /
  `perf`(性能) / `build`(构建系统) / `ci`(CI 配置)。
- **scope**（可选）：受影响的模块，如 `analyzer` / `gate` / `enums` / `docs`。
- **subject**（必填）：祈使句、简洁、不超过 72 字符、不以句号结尾、不用中文标点混排。
- 示例：
  - `feat(analyzer): 支持 hunk 级测试点打标`
  - `fix(gate): 修复 bandit 不读 pyproject skips 的问题`
  - `docs: 补充统一门禁命令说明`
- 门禁：`scripts/check_commit_msg.py`（pre-commit `commit-msg` 钩子）拦截不符合格式的信息。
  合并提交 / revert / 符合 `(merge|revert|Merge)` 前缀的可豁免。

### 7.2 分支命名
- 功能：`feat/<简短描述>`（如 `feat/secret-scan`）
- 修复：`fix/<简短描述>`
- 重构：`refactor/<简短描述>`
- 文档：`docs/<简短描述>`
- 长期分支：`develop`；发布稳定：`main` / `master`（受分支保护，禁止直推）。

### 7.3 PR 规范
- PR 必须基于 `develop` 或特性分支 → 目标 `main`；标题用 Conventional Commits 风格。
- 描述含「变更摘要 / 影响范围 / 门禁结果（gate_all 全绿截图或本地输出）/ 测试证据」。
- PR 模板见 `.github/PULL_REQUEST_TEMPLATE.md`；合并前须通过 `guard` 状态检查 + 至少 1 人评审。

