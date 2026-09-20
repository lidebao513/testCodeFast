# work/testhub 代码库分析报告

> **分析日期**：2026-09-08
> **分析对象**：`C:\Users\EDY\WorkBuddy\testCodeFast\work\testhub`
> **分析方法**：逐文件核验（非仅凭 README 推断）
> **一句话结论**：这是一个**基于已作废「合并进 testhub」方案**搭的**脚手架**，目前**只有 3 个 app 的数据模型、无任何可运行接口/前端**，**项目当下无法启动**（`monitor` 被引用却缺失、所有 app 均无 `urls.py`/`views.py`/`migrations`）。其自带文档描述的是理想态，与真实代码严重不符。

---

## ⚠️ 0. 最关键的前提：方案已作废，本目录属于"历史路径"

`work/testhub/README.md` / `MIGRATION.md` / `TASK_PLAN.md` 全程引用设计文档 **§11 / §12「将测试加速平台合并进 testhub」**，并自称"合并目标工程脚手架"。

但**同一会话内用户已明确变更方向**：
> "目前 testhub 不会再同步本项目的内容。我计划后续将 testcodefast 改造为一个独立服务……"

因此：**本目录编码的是一条已被用户取消的技术路线**。它目前的价值仅限于"架构参考"，不应作为独立服务化方向的落地工程。当前正确的规划文档是：
- `work/测试加速平台_服务化改造分析.md`（独立服务化）
- `work/测试执行服务_自愈与WorkBuddy集成方案.md`（含浏览器调度 + 自愈）

下文按"它本想成为什么 / 实际有什么 / 缺什么"三层展开。

---

## 1. 整体功能定位与用途（设计意图）

按文档意图，`work/testhub` 是 **Web 测试自动化平台 testhub** 的一个分支，目标是把"测试加速平台（源自 `work/test-accel`，FastAPI/SQLite/原生 HTML）"的能力并入 testhub 既有的 Django 体系。

理想态用途（完整测试平台）：
1. 输入**被测目标**（git 地址 / URL + 账号密码）→ 平台分析站点生成功能测试点；
2. 驱动**本机浏览器（Playwright）**做功能测试；
3. 产出测试结果 / 缺陷列表 / bug 截图 / 操作过程；
4. 多轮重选验证 → 生成测试报告（可带知识库，知识库可反推需求文档与操作手册）。

技术栈（既定，写在 README/settings）：
- 后端：Django 4.2 + DRF；ASGI 走 **Daphne(:8000) + Channels**（实时进度）；
- 任务：Celery（worker + beat）；缓存/broker：**Redis**；
- 存储：MySQL 8.0 默认，支持 `DB_ENGINE=sqlite3` 平迁；
- 前端：Vue3 + Vite + Element Plus + vue-i18n（zh/en/ja/ko），:3000。

---

## 2. 主要模块及目录结构划分

```
work/testhub/
├── manage.py                  # Django 入口
├── testhub/                   # 项目包
│   ├── settings.py            # INSTALLED_APPS / DB 切换 / Celery / 端口池
│   ├── urls.py                # 各 app API 挂载（含 code-analysis/accel-skills/deploy）
│   ├── asgi.py  wsgi.py       # ASGI（但 asgi.py 仅为裸 get_asgi_application，无 Channels routing）
├── apps/                      # 12 个 app 目录（见下表）
├── frontend/                  # Vue3 骨架：src/{api,locales,router,store,views} —— 0 个文件（空）
├── requirements.txt           # Django/DRF/Channels/Celery/Redis/mysqlclient
│                            #   + 复用依赖 openai/playwright/requests/httpx/python-dotenv
├── .env.example  start_dev.sh
├── README.md  MIGRATION.md  TASK_PLAN.md
```

### apps/ 现状（实测，12 个目录）

| app | 实际文件 | 状态 |
|---|---|---|
| `code_analysis` | `apps.py` + `models.py` | **模型已写，无 views/urls/serializers/migrations** |
| `accel_skills` | `apps.py` + `models.py` | 同上 |
| `deployment_target` | `apps.py` + `models.py` | 同上 |
| `core` | 仅 `__init__.py` | 空壳 |
| `executions` | 仅 `__init__.py` | 空壳 |
| `projects` | 仅 `__init__.py` | 空壳 |
| `reports` | 仅 `__init__.py` | 空壳 |
| `requirement_analysis` | 仅 `__init__.py` | 空壳 |
| `reviews` | 仅 `__init__.py` | 空壳 |
| `testcases` | 仅 `__init__.py` | 空壳 |
| `ui_automation` | 仅 `__init__.py` | 空壳 |
| `users` | 仅 `__init__.py` | 空壳 |
| `monitor`（被引用） | **目录不存在** | settings/urls 引用 `apps.monitor` → 启动即报错 |

**实测结论**：全仓 grep 无任何 `APIView/ViewSet/@api_view/path(`；无任何 `urls.py`/`views.py`/`serializers.py`/`migrations/`。即——**没有任何可运行接口，前端 0 文件**。

---

## 3. 核心业务流程（设计意图，基于数据模型反推）

现有 5 个模型（`FunctionalPoint`/`ChangeLog`/`Skill`/`DeploymentTarget`/`PortAllocation`）透露出意图流程：

```
① 注册项目 projects.Project
        │
② 部署被测目标 deployment_target.DeploymentTarget
        ├─ 只读 git 克隆（git_url / git_token_ref / branch）
        ├─ PortAllocation 从端口池(8100–8199)分配 port
        ├─ run_command 起目标服务进程
        └─ health_url 探活 → status: stopped/running/error
        │
③ 代码分析 code_analysis
        ├─ AST 抽取 FunctionalPoint（api/page/component/flow），关联 commit_ref
        └─ diff_analyze（base..head）→ ChangeLog（new/updated/removed 功能点 id）
        │
④ 生成用例 → 落入【复用】testcases（不新建第二套 case 表）
        │
⑤ 执行 executions（复用 testhub playwright_engine）
        └─ TestRun/TestRunCase 状态机：pass/fail/error/flaky
        │
⑥ 报告 reports（复用）
        │
⑦ 审查门 reviews：FunctionalPoint/Cases 的 review_status（pending/approved/rejected）
        │
⑧ 资产闭环 accel_skills.Skill（yaml/playbook 版本化 + usage_count 复用计数 + 回流）
        │
⑨ 增量回归（Celery beat）：定时 diff_analyze → 触发变更功能点回归
        │
前端（Vue3 + i18n）经 /api/* 消费全流程
```

> 注意：上述 ④⑤⑥⑦⑧⑨ 涉及的 app（testcases/executions/reports/reviews/ui_automation/accel_skills 逻辑/前端）**当前全部为空壳或未实现**。流程目前只"存在于模型与文档"，不存在可执行代码。

---

## 4. 关键实现逻辑（已落地的部分）

### 4.1 真正写出来的只有 3 个 app 的 models
- **code_analysis**（平台区别于 testhub 的独有价值：静态 AST 功能点 + 增量溯源）
  - `FunctionalPoint`：`project`(FK) + `commit_ref` + `file_path` + `name` + `ftype`(api/page/component/flow) + `review_status`(pending/approved/rejected，复用 reviews 工作流) + `created_by`(FK users.User)；唯一约束 `(project, file_path, name, ftype)`。
  - `ChangeLog`：`project` + `commit_from/to` + `new_fp_ids`/`updated_fp_ids`/`removed_fp_ids`(JSONField) —— 增量回归溯源。
- **accel_skills**（testhub 全仓原本无 skill 概念，原生引入）
  - `Skill`：`project` + `name` + `spec_path`(skill.yaml) + `playbook_path`(playbook.md) + `version` + `scope`(project/global) + `usage_count` + `created_by`；唯一约束 `(project, name, version)`。
- **deployment_target**（补全 testhub 不托管被测服务的缺口）
  - `DeploymentTarget`：`project` + `git_url` + `git_token_ref`(仅存引用，明文走密钥注入) + `branch` + `local_path` + `run_command` + `health_url`/`base_url` + `port` + `status`(stopped/running/error)。
  - `PortAllocation`：`port`(unique) + `occupied_by`(FK DeploymentTarget) —— 端口池。

### 4.2 settings.py 编码的关键约定
- `apps/` 通过 `sys.path.insert(0, .../apps)` 统一加载；
- **DB**：`DB_ENGINE` 环境变量切换 mysql / sqlite3；
- **Redis 三库**：cache=6379/1，Celery broker=6379/2，result=6379/3；
- **Celery**：`CELERY_BROKER_URL`/`CELERY_RESULT_BACKEND` + `CELERY_TIMEZONE=Asia/Shanghai`（增量回归 beat）；
- **DRF 鉴权**：`SessionAuthentication` + `TokenAuthentication`，默认 `IsAuthenticated`；`CORS_ALLOW_ALL_ORIGINS=True`；
- **端口池**：`DEPLOY_PORT_POOL = range(8100, 8200)`；
- **LLM 凭据入库**（`requirement_analysis.AIModelConfig`），`.env` 仅留基础设施密钥。

### 4.3 未实现但文档承诺的逻辑（缺口，详见 §5）
纯逻辑平移（code_analyzer/smoke/config/llm_client）、路由改写、裸 SQL→ORM、复用 AIModelService / playwright_engine / monitor、7 个前端页面 + i18n——**均未落地**。

---

## 5. 组件/服务依赖关系与交互方式

### 5.1 外部依赖
| 依赖 | 用途 | 配置 |
|---|---|---|
| MySQL 8.0 / SQLite | 主存储 | `DB_ENGINE` 切换 |
| Redis 7 | cache + Celery broker + result | `REDIS_URL`（3 个 db） |
| Celery worker+beat | 长任务执行 + 增量回归调度 | `CELERY_BROKER_URL` |
| Daphne + Channels | ASGI + 实时进度（WebSocket） | `ASGI_APPLICATION`（`asgi.py` 目前裸，无 routing/consumer） |
| Playwright（浏览器） | 真浏览器执行 | 经 `ui_automation.playwright_engine`（未实现） |
| 被测目标服务 | 被验证对象 | 由 `deployment_target` 克隆/起进程/探活 |

### 5.2 应用间依赖（来自模型外键）
```
projects.Project  ◄── code_analysis.FunctionalPoint / ChangeLog
                 ◄── accel_skills.Skill
                 ◄── deployment_target.DeploymentTarget / PortAllocation
users.User       ◄── FunctionalPoint.created_by / Skill.created_by
```
即：`projects` 与 `users` 是**被依赖的基座**（但二者目前仅为空壳 app）；三个"新建 app"的数据模型已挂上这两个基座的外键。

### 5.3 调用/交互方式（设计意图）
- **前端 ↔ 后端**：Vue3 经 DRF `/api/*`（projects / testcases / reports / reviews / ai / executions / code-analysis / accel-skills / deploy）JSON 交互；
- **长任务**：同步提交 → 返回 task_id → Celery 异步执行 → 进度经（规划中的）Channels WebSocket 推送；
- **增量回归**：Celery beat 定时触发 `diff_analyze` → 写入 `ChangeLog` → 触发变更功能点回归；
- **被测目标生命周期**：`deployment_target` 负责 git 只读克隆 → 端口池分配 → 起进程 → `health_url` 探活，与 tests 解耦。

### 5.4 文档声称 vs 真实代码（矛盾清单）
| 文档声称 | 真实情况 |
|---|---|
| 21 个 apps | 实际 12 个 app 目录 + 引用 1 个不存在的 `monitor` |
| 三新建 app "models 已就位" | 仅 models 在，无 views/urls/serializers/migrations |
| `monitor` 探活复用 | `monitor` 目录不存在，settings/urls 引用会直接报错 |
| 7 个前端页面 + i18n | `frontend/src` 下 0 个文件 |
| 可 `manage.py migrate` 起服务 | 任何 app 都无 `migrations/`；urls 引用大量不存在模块 → check/migrate 必失败 |
| 纯逻辑 421 行已平移 | `apps/*/logic/` 不存在，code_analyzer 等未迁入 |

---

## 6. 结论与建议

1. **它当前不能运行**：缺 `monitor`、所有 app 无 `urls.py`/`migrations`、前端为空。`start_dev.sh` 里的 `manage.py migrate` 与 Daphne 起服务都会因导入失败而中断。它是一份**架构骨架 + 3 张数据模型表**，不是工程。

2. **它代表已取消的路线**：自带文档全部基于"合并进 testhub"（§11/§12），而用户已决定"testCodeFast 改独立服务"。**不要把本目录当作后续落地工程**；若作参考，仅取其"数据模型设计"（FunctionalPoint/ChangeLog/Skill/DeploymentTarget/PortAllocation 的字段划分）与"复用而非双套"的思路有价值。

3. **若仍要复活合并路线（非当前方向）**，最小修复顺序：
   - 删除 `settings.py`/`urls.py` 中对 `apps.monitor` 的引用（或补建 monitor）；
   - 为 3 个新 app 生成 `migrations/`（先 `makemigrations`）；
   - 为所有被 `urls.py` include 的 app 补 `urls.py` + `views.py` + `serializers.py`；
   - 实现 `TASK_PLAN.md` 中 T1–T18（纯逻辑平移→模型迁移→路由/ORM→复用→三新 app→前端）。

4. **推荐动作**：以 `测试加速平台_服务化改造分析.md` + `测试执行服务_自愈与WorkBuddy集成方案.md` 为后续准绳；`work/testhub` 可作为"历史脚手架"保留或归档，但**不再作为开发主线**。如确认不再需要，可移出工作区以避免混淆。

---

## 附：可运行性快速核验命令（供你自行验证）
```bash
cd C:\Users\EDY\WorkBuddy\testCodeFast\work\testhub
python manage.py check         # 预期：报错（找不到 apps.monitor / 各 app urls）
python manage.py migrate       # 预期：失败（同上 + 无 migrations）
find apps -name "urls.py"     # 预期：无输出（0 个）
find frontend -type f          # 预期：0 个文件
```
