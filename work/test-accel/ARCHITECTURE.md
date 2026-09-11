# ARCHITECTURE.md —— test-accel 架构约束（单一事实来源）

> 本文件是**项目整体改动前的硬性约束**：任何重构、优化、AI 自动生成，都必须遵守
> 本文规定的目录结构、分层依赖方向与模块职责。违反即视为「跑偏」，由
> `scripts/check_structure.py` 在 pre-commit / CI（`scripts/gate_all.py` 统一入口）中自动拦截。
> 变更本文需走 ADR（见 `ADR/` 目录），不得私自改写。

---

## 1. 分层模型（核心约束）

```
┌─────────────────────────────────────────────────────────────┐
│  接入层 (cli / service)                                        │
│   backend/cli/     命令入口（gen / validate / run 等）          │
│   backend/service/ FastAPI 服务壳（被 testhub 远程调用 / 流水线）│
└───────────────┬─────────────────────────────┬───────────────┘
                │ 依赖（向下）                  │ 依赖（向下）
                ▼                               ▼
┌───────────────────────────┐     ┌──────────────────────────────┐
│  modules/ 业务引擎（纯逻辑）│     │  core/ 基础设施（单源）          │
│  code_analyzer /            │     │  enums.py  ← 枚举唯一真值源      │
│  case_generator / executor  │     │  config / 常量 / 工具           │
└───────────────┬────────────┘     └──────────────────────────────┘
                │ 依赖                            ▲ 不依赖任何上层
                └────────────────────────────────┘
```

**依赖方向铁律（被 `check_structure.py` 强制）**：
- `cli/` 与 `service/` **可以**依赖 `modules/` 与 `core/`
- `modules/` **可以**依赖 `core/`，**禁止**依赖 `cli/`/`service/`
- `core/` **禁止**依赖 `modules/`/`cli/`/`service/`（保证可被 skill 独立引用）
- 任何层 **禁止** `import` 兄弟层的私有实现细节（只依赖公开 API）

---

## 2. 目录结构约定

| 目录 | 职责 | 允许放什么 | 禁止放什么 |
|---|---|---|---|
| `backend/core/` | 基础设施单源 | `enums.py`、`config.py`、纯工具 | 业务逻辑、网络 IO |
| `backend/modules/` | 业务引擎（纯逻辑、可单测） | 代码分析/用例生成/执行器 | FastAPI 依赖、CLI 参数解析 |
| `backend/service/` | 服务壳 | FastAPI app、路由、webhook | 业务算法 |
| `backend/cli/` | 命令入口 | 子命令、参数解析 | 业务算法 |
| `scripts/` | 一次性/维护性工具 | `check_enums.py`、`check_structure.py`、迁移脚本 | 常驻业务逻辑 |
| `tests/` | 测试层 | `test_*.py` pytest 套件 | 业务实现 |
| `data/` | 运行态（git 忽略内容） | db / logs / reports / screenshots | 源码 |
| `report_templates/` | 报告模板 | 静态模板 | 逻辑 |
| `gen_*.py` / `selftest_*.py` / `run_*.py` / `verify_*.py`（根目录） | **历史债务** | —— | 新代码**禁止**再放根目录，应迁入 `cli/`/`scripts/`/`tests/` |

> 根目录散落脚本是优化前的技术债，迁移清单见 §5。`check_structure.py` 会打印现存清单并提示目标位置，但不阻断（避免历史债务瞬间爆红）。

---

## 3. 模块职责边界

- **code_analyzer**：读代码结构 → 提取功能点(FP) → 展开测试点(TP)。纯标准库 + `ast`/`subprocess`，**不碰 DB / 不碰 HTTP 服务**。
- **case_generator**：FP/TP → 测试用例。确定性、不依赖 LLM。
- **executor**：用例 → 执行结果。含执行层派发（`VerifyLayer`）+ UI→接口回退。
- **enums（core）**：所有枚举/常量的**唯一真值源**（见 §4 铁律）。
- **db / main**：持久化与 HTTP 接入，仅 service 层相关。

---

## 4. 不可动摇的铁律（被门禁强制）

> 上述铁律由 `scripts/gate_all.py` 统一编排的 pre-commit / CI 门禁强制执行：
> `ruff lint` + `ruff format --check` + `check_enums` + `check_structure` + `mypy(backend)`
> + `bandit(medium)` + `pytest(cov)`。新增/修改代码前先跑一遍 `python scripts/gate_all.py`，全绿再提交。

1. **枚举单源**：所有枚举值（`tp_type`/`tag`/`ftype`/`verify_layer`/`dimension`/`status` 等）
   必须来自 `backend/core/enums.py`。任何 `.py` 在枚举字段赋值/比较里**硬编码字面量**，
   会被 `scripts/check_enums.py` 拦截。**改枚举只改 `enums.py` 一处。**
2. **SKILL.md 与 enums 同步**：`~/.workbuddy/skills/qa-*/SKILL.md` 中出现枚举取值时，
   必须与 `enums.py` 一致；文档不承载可执行定义，仅说明。
3. **引擎可被 skill 引用、禁止双源**：`code_analyzer` 等引擎抽离后，
   项目**引用**技能包而非内嵌副本；禁止"复制一份"，防止双源分叉。
4. **测试点数据契约稳定**：产物 JSON 中每条测试点**必须含** `verify_layer`
   （由 `code_analyzer` 注入）；新增字段不得破坏既有消费方（executor / 报告生成器）。
5. **第三方被测代码不入库**：`work/targets/` 由 `.gitignore` 排除（见 `.gitignore`）。
6. **密钥不入库**：`.env` 排除；`.env.example` 仅含占位。

---

## 5. 历史债务迁移清单（优化阶段目标，非即时阻断）

以下根目录脚本应在「整体优化」阶段迁入对应目录（门禁仅 warning）：

| 现有文件 | 目标位置 | 说明 |
|---|---|---|
| `gen_test_points.py` / `gen_structured_cases.py` / `gen_*.py` | `backend/cli/` | 命令入口 |
| `validate_full_pipeline.py` / `gen_validation_reports.py` | `scripts/` 或 `backend/cli/` | 验证/报告工具 |
| `selftest_*.py` / `verify_*.py` | `tests/` | pytest 化 |
| `run_flow123.py` / `run_full_flow.py` | `backend/cli/` | 编排入口 |
| `make_*_report.py` | `scripts/` | 报告生成 |

> 在迁移完成前，新提交**不得新增**根目录 `gen_/selftest_/run_/verify_*.py`。

---

## 6. 与服务化定位的关系

平台定位为**独立服务**：①被 testhub 远程调用；②接入发布流水线做部署后验证。
因此 `service/` 层是「薄壳」，引擎逻辑留在 `modules/`，便于被 skill 与 CI 双重复用。
详见 `ADR/`。
