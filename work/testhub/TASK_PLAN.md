# 后续任务计划（testhub 合并落地）

> 列出"测试加速平台 → testhub"当前**未完成**的任务，明确各自目标、范围与在 testhub 中的执行顺序，便于在 `work/testhub/` 项目中逐项落实。
> 依据：设计文档 §11 / §12、roadmap（§7）、实现现状盘点（§12.2）。执行顺序遵循 §12.6「先搬确定小头 → 再改路由与 SQL → 最后新建大头」。

---

## 总原则
1. **先复用再补差**：case/执行/报告复用 testhub 既有 `testcases`/`executions`/`reports`，禁止第二套引擎（§11.2/§12.5）。
2. **只在 testhub 栈新建**：`skill_generator`/`scheduler`/`review_gate`/前端**不要在 test-accel 里先补**，直接按 Django/Vue3 实现，避免写两遍（§12.5）。
3. **每阶段可独立验收**：对应 MIGRATION.md §5 验证清单。

---

## 执行顺序总览（在 testhub 中的落地顺序）

| 序 | 任务编号 | 任务 | 性质 | 难度 |
|----|----------|------|------|------|
| 1 | T1 | 纯逻辑模块平移 | 平移 | 极低 |
| 2 | T2 | 数据模型迁移（7 表 → models） | 改写 | 低 |
| 3 | T3 | 路由改写（8 路由 → DRF ViewSet） | 改写 | 低-中 |
| 4 | T4 | 裸 SQL → ORM（18 处） | 改写 | 低 |
| 5 | T5 | 复用 AIModelService（LLM 配置入库） | 适配 | 低 |
| 6 | T6 | 复用 playwright_engine + executions 状态机 | 复用 | 低 |
| 7 | T7 | 复用 testcases/reports/reviews（防双套） | 复用 | 低 |
| 8 | T8 | 复用 monitor 探活 | 复用 | 低 |
| 9 | T9 | 新建 code_analysis app | 新建 | 中 |
| 10 | T10 | 新建 accel_skills app | 新建 | 中 |
| 11 | T11 | 新建 deployment_target app | 新建 | 中 |
| 12 | T12 | 增量回归调度（scheduler → Celery beat） | 新建 | 中 |
| 13 | T13 | 人工审查门 review_gate（复用 reviews） | 新建 | 中 |
| 14 | T14 | skill_generator 资产闭环 | 新建 | 中 |
| 15 | T15 | 前端 Vue3 7 页面 + i18n | 全新 | 中-高 |
| 16 | T16 | 部署脚本 + Daphne + 端口池 | 部署 | 低 |
| 17 | T17 | 多端追踪（H5/Android/iOS） | 记录 | 低 |
| 18 | T18 | LLM 开关与"纯 AST 退化"路径 | 适配 | 低 |

---

## 任务明细

### T1 · 纯逻辑模块平移
- **目标**：将 test-accel 零框架依赖模块移入 testhub，使核心逻辑可复用。
- **范围**：`code_analyzer.py`(182) / `smoke.py`(152，仅参考，实际复用 monitor) / `config.py`(48) / `llm_client.py`(39，改复用 AIModelService)。约 421 行。
- **顺序**：第 1 步。
- **依赖**：无。
- **验收**：在 Django 环境下 `from apps.code_analysis.logic.code_analyzer import code_analyzer` 可用，功能点产出与原 FastAPI 一致。

### T2 · 数据模型迁移
- **目标**：7 张 SQLite 表 → Django models + migration。
- **范围**：`functional_points`/`change_log`→`code_analysis`；`skills`→`accel_skills`；`projects`→扩展 `Project` 或 `deployment_target`；`cases`→`testcases`（复用）；`runs`→`executions`（复用）；`reports`→`reports`（复用）。
- **顺序**：第 2 步（T9/T10/T11 的 models 已在本脚手架就位）。
- **依赖**：T1。
- **验收**：`python manage.py makemigrations && migrate` 成功；模型字段对齐 §11.7。

### T3 · 路由改写
- **目标**：`main.py` 8 个端点 → DRF ViewSet/Serializer。
- **范围**：项目管理、analyze、diff_analyze、functional_points、change_logs 等。
- **顺序**：第 3 步。
- **依赖**：T2。
- **验收**：`POST /api/code-analysis/diff` 与原 `POST /api/projects/{pid}/diff_analyze` 返回结构等价。

### T4 · 裸 SQL → ORM
- **目标**：消除 18 处裸 SQL（project_manager 4 / case_generator 3 / executor 3 / reporter 1 / main 若干）。
- **范围**：改写为 Django ORM；注意 `DELETE FROM cases WHERE project_id=?` 全量重建语义 → 改为版本化/级联（§12.5）。
- **顺序**：第 4 步（与 T3 同阶段）。
- **依赖**：T2。
- **验收**：全仓无裸 SQL；既有功能等价。

### T5 · 复用 AIModelService
- **目标**：LLM 配置不再自带 `llm_client`，复用 `requirement_analysis.AIModelService`。
- **范围**：新增 writer/reviewer 配置（qwen，dashscope）；**API Key 入库非 .env**（§11.4）；保留"无 active 配置即退化为纯 AST"。
- **顺序**：第 5 步。
- **依赖**：testhub 既有 `requirement_analysis`。
- **验收**：可切换 qwen/deepseek；关闭 LLM 时功能点以 AST 结果为唯一来源。

### T6 · 复用 playwright_engine + executions
- **目标**：执行引擎复用 testhub `ui_automation.playwright_engine`，长任务走 Celery，进度接 `executions` 状态机。
- **范围**：新增"代码派生 case"执行入口；复用 `TestRun/TestRunCase` 状态机（pass/fail/error/flaky）。
- **顺序**：第 6 步。
- **依赖**：T3、T4。
- **验收**：代码派生 case 经 `playwright_engine` 实际跑通；结果写回 `executions`。

### T7 · 复用 testcases/reports/reviews（防双套）
- **目标**：严格复用，不新建 parallel 表。
- **范围**：`cases`→`testcases`、`reports`→`reports`（基线对比用扩展字段）、`reviews` 承载审查门。
- **顺序**：第 7 步（与 T3/T4 协同）。
- **依赖**：T2。
- **验收**：全仓仅一套 case/report 表，无语义冲突。

### T8 · 复用 monitor 探活
- **目标**：健康探活复用 testhub `monitor`（`MonitorTarget`/`AlertEvent`），不重建。
- **范围**：目标服务 `health_url` 探活挂 monitor。
- **顺序**：第 8 步。
- **依赖**：testhub 既有 `monitor`。
- **验收**：目标服务上下线触发 monitor 事件。

### T9 · 新建 code_analysis app
- **目标**：落地平台独有价值——AST 功能点抽取 + 增量溯源。
- **范围**：`views.py`（`diff_analyze`：`git diff --name-status base..head` → new/updated/removed 三向分类，逻辑平移 `diff_analyzer.py`）+ `urls.py`；`models.py` 已就位。
- **顺序**：第 9 步（新建大头第一步）。
- **依赖**：T2、T3。
- **验收**：`/api/code-analysis/diff` 文件级 diff 与 `git diff --name-status` 逐项一致；change_log 写入。

### T10 · 新建 accel_skills app
- **目标**：引入 testhub 全仓缺失的 Skill 资产概念。
- **范围**：`skill.yaml`+`playbook.md`+`helpers/` 版本化、复用计数、回流闭环；`models.py` 已就位。
- **顺序**：第 10 步。
- **依赖**：T2、T3。
- **验收**：Skill 可创建/版本化/被 case 复用并计数。

### T11 · 新建 deployment_target app
- **目标**：补齐 testhub 缺位的被测目标托管能力。
- **范围**：只读 git 克隆（git_url/token/branch）→ 端口池分配 → `run_command` 起进程 → `health_url` 探活 → 日志落盘；`models.py` 已就位。
- **顺序**：第 11 步。
- **依赖**：T2、T8。
- **验收**：能克隆 research-agent 并起前后端两进程、分配独立端口、探活成功（research-agent 为复合目标，复杂度高于单服务，§12.5）。

### T12 · 增量回归调度
- **目标**：git diff 增量回归作为周期性任务。
- **范围**：`scheduler`（当前未实现）→ testhub `core` management command + Celery beat 任务。
- **顺序**：第 12 步。
- **依赖**：T9、T11、T6。
- **验收**：beat 定时跑 `diff_analyze` 并写入 change_log，触发需回归的功能点。

### T13 · 人工审查门 review_gate
- **目标**：功能点/case 审查门接入既有评审工作流。
- **范围**：复用 `reviews` 承载 `review_status`（pending/approved/rejected）；原 `config.REVIEW_GATE` 开关语义保留。
- **顺序**：第 13 步。
- **依赖**：T7、T5。
- **验收**：审查门开启时功能点/case 处于 pending 需审批；关闭则自动终态。

### T14 · skill_generator 资产闭环
- **目标**：从执行结果自动产出/回流 Skill 资产。
- **范围**：`skill_generator`（当前未实现）→ 在 `accel_skills` 上实现 skill.yaml/playbook 生成 + 每次任务同步、新旧对比补充。
- **顺序**：第 14 步（与 T10 协同）。
- **依赖**：T10、T6。
- **验收**：一轮测试后可自动沉淀 Skill 并被后续复用。

### T15 · 前端 Vue3 7 页面 + i18n
- **目标**：补齐平台前端（当前 0 行，纯增量）。
- **范围**：仪表盘 / 项目 / 功能点 / 执行 / 报告 / Skill 库 / 设置；接入 router/store/api；**强制 vue-i18n（zh/en/ja/ko）**（§11.9）。
- **顺序**：第 15 步（工期大头，最后做）。
- **依赖**：T3–T14 后端就绪。
- **验收**：7 页面可访问；i18n 校验通过；不达标不通过合并验收。

### T16 · 部署脚本 + Daphne + 端口池
- **目标**：统一启动与端口治理。
- **范围**：`start_dev.sh`（Daphne :8000 + Celery worker/beat + 前端 :3000）；`deployment_target` 端口池（默认 8100–8199）。
- **顺序**：第 16 步（可在 T9/T11 后即可局部验证，整体收尾）。
- **依赖**：T9、T11。
- **验收**：`bash start_dev.sh` 一键拉起；目标服务端口不冲突。

### T17 · 多端追踪（H5/Android/iOS）
- **目标**：记录待完成端，不实现执行。
- **范围**：数据模型 `type` 字段 + "待完成"状态；H5/Android(Appium)/iOS(XCUITest) 仅登记。
- **顺序**：第 17 步（低优，合并后追踪）。
- **依赖**：T2。
- **验收**：三端在 UI/数据层可追踪，状态明确为"待完成"。

### T18 · LLM 开关与"纯 AST 退化"路径
- **目标**：保证可关闭 LLM、纯 AST 仍成立。
- **范围**：`REVIEW_GATE`/LLM 开关在 testhub 配置层对齐；无 active writer/reviewer 时功能点以 AST 为准的语义不变。
- **顺序**：第 18 步（贯穿，建议在 T5 一并落实）。
- **依赖**：T5。
- **验收**：关闭 LLM 后功能点提取结果与设计语义一致，前端标记"待补"。

---

## 工作量配比参考（§12.4）
**后端移植 2 : 前端新建 5 : 三新模块+部署 3**。综合难度 ★★☆☆☆（代码量小、耦合低），但最大工作量在"从零新建"而非"搬运"。

## 建议节奏
- 第 1–4 步（T1–T4）为"搬运确定项"，可快速完成并验收；
- 第 5–8 步（T5–T8）为"复用对齐"，依赖 testhub 既有 app；
- 第 9–14 步（T9–T14）为"新建大头"，直接在 testhub 栈实现；
- 第 15 步（T15）前端单独排期；第 16–18 步收尾与追踪。
