# 项目技能索引（Skills Index）

> 本文件由 `work/gen_skills_index.py` 自动扫描 `~/.workbuddy/skills/` 生成。每次新增 / 改名 / 修改技能后，重跑该脚本即可同步，**请勿手改**。

技能总数：**6**（用户级 6）

## 用户级技能（~/.workbuddy/skills/ · 跨项目可用）

| 技能名 | 目录 | 路径 | 目录内容 | 说明 |
|---|---|---|---|---|
| `django-async-orm-guard` | `django-async-orm-guard` | `~/.workbuddy/skills/django-async-orm-guard` | — | 修复 Django/DRF 在 async 协程中直接调用同步 ORM（含模型 __init__ 里的查询）导致的 SynchronousOnlyOperation 异常；并覆盖 venv/playwright/browser-use 启动类故障排查。当用户报告 "SynchronousOnlyOperation: You cannot call this from an async context"、Django 异步视图/协程内数据库报错、或 browser-use/playwright 驱动 Chrome 失败时适用。 |
| `ifind-finance-data` | `ifind-finance-data` | `~/.workbuddy/skills/ifind-finance-data` | _icon.png、_skillhub_meta.json、call-node.js、call.py、mcp_config.json、references | 同花顺iFinD金融数据查询，查询股票、基金、宏观经济、行业经济、新闻公告、债券、港美股、指数板块及期货期权数据；其中A股、中国公募基金、债券交易所、国内指数共4类市场支持日内高频/实时行情的level1数据，同时支持智能选股、选基、宏观行业经济指标搜索、金融公告资讯搜索等服务 |
| `qa-code-pull` | `qa-code-pull` | `~/.workbuddy/skills/qa-code-pull` | pull_code.py | 「拉取代码」独立技能：克隆 / 更新 / 加深（解决浅克隆 git diff 失真）/ 确认 diff 基线与目标 ref / 将工作树切到目标版本 / 计算 base..target 变更文件集合。当用户给出仓库地址或分支对比基线、 要求「拉取 / 同步 / 更新代码 / 准备被测代码 / 拿到变更文件」时使用。与「测试点(qa-test-points)」技能 完全解耦：本技能只负责把代码「备好并就位」，不生成测试点；也不 import 任何测试点 / 平台模块， 环境变量命名空间隔离（REPO_URL / LOCAL_PATH / DIFF_BASE / DIFF_TARGET / DEEPEN / PULL_RESULT_JSON）， 通过文件系统契约（写 result JSON）与下游通信，互不干扰、无报错、运行稳定。 |
| `qa-reuse-validation` | `qa-reuse-validation` | `~/.workbuddy/skills/qa-reuse-validation` | — | 当用户提供仓库地址、测试环境 URL、账号密码等"待测试/待验证"信息时，在生成任何测试代码或重新搭建脚本之前， 必须先核对「已完成功能清单」与项目记忆，复用既有能力/脚本/用例，禁止把已实现的同类功能当全新功能重新生成。 触发词："在 X 地址测试"、"测试这个仓库"、"根据扫描生成的用例测试"、"重新验证"、"跑一遍"、 "验证一下"、"用环境 Y 测试"、"对 Z 分支做测试"。Also apply whenever a request bundles a repo URL + credentials with a "test/validate/verify/execute" verb, or mentions a target env that has appeared before. |
| `qa-test-points` | `qa-test-points` | `~/.workbuddy/skills/qa-test-points` | — | 测试点（Test Points）生成与对比能力。当用户要求「生成测试点 / 测试范围 / 测试知识点 / 测试覆盖 / 测试矩阵」，或给定仓库、分支、对比基线并说「生成测试点」，或需要把「旧版（模块级）」 与「新版（代码级）」测试点做对比、标注「全量 / 更新」或范围（正常 / 异常 / 安全 / 边界）时使用。 **本技能只生成测试点，不拉取代码**——被测代码须已由 qa-code-pull 技能备好（或手动就位）。 |
| `windows-browser-e2e-selftest` | `windows-browser-e2e-selftest` | `~/.workbuddy/skills/windows-browser-e2e-selftest` | scripts | Run real-browser end-to-end self-tests of a local web app inside the WorkBuddy Windows sandbox using Playwright + the system Microsoft Edge (msedge) browser. Use this skill when a task asks to verify a frontend/application by actually clicking through it in a browser (not just curl), especially on Windows where the sandbox safe-delete guard and antd/Ant Design rendering quirks cause failures. Triggers: "用浏览器走查", "真实浏览器验证", "端到端自测", "点一遍所有功能", "E2E 测试", or any request to click through a frontend and produce a self-test/acceptance report. |

## 调用顺序（QA 域）

1. **先 `qa-code-pull`**：备好被测代码（仓库就位、工作树=目标版本、产出 `.pull_result.json`）。
2. **后 `qa-test-points`**：经环境变量 `CHANGED_FILES_JSON` 指向该 JSON **解耦消费**变更集（不 import、不调 git），生成测试点。

