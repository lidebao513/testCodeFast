# testhub 合并迁移文档（测试加速平台 → testhub）

> 适用范围：将 `work/test-accel`（FastAPI / SQLite / 原生 HTML SPA）合并进 **testhub（Django 4.2 + DRF + Vue3 + Celery + Channels/Daphne + MySQL）**。
> 本目录 `work/testhub/` 即为迁移目标工程脚手架，本文所有命令均可依据该结构直接执行。
> 设计依据：设计文档 §11（合并注意事项）、§12（现状盘点与工作量）。

---

## 1. 环境要求

| 类别 | 要求 | 说明 |
|------|------|------|
| Python | 3.11+（管理用 3.13.12 亦可） | 虚拟环境隔离：`python -m venv venv` |
| Django | 4.2.x | 既定，勿升 5.x（Channels 兼容） |
| 数据库 | MySQL 8.0（默认）或 SQLite3（开发平迁） | `DB_ENGINE=sqlite3` 切换 |
| Redis | 7.x | Celery broker / result / cache |
| Node | 18+ | 前端 Vue3 + Vite |
| Playwright | 1.57（testhub 已装） | 真浏览器执行后续接 `ui_automation.playwright_engine` |
| 包镜像 | `https://mirrors.aliyun.com/pypi/simple` | 规避清华源 403（见 §12.3） |
| Git | 支持 SSH（GitHub 仅 SSH 可达） | 内网 codeup 直连快、代理慢，fetch 加 `protocol.version=0` |

**首次准备（在本目录执行）**
```bash
cd work/testhub
python -m venv venv
source venv/Scripts/activate          # Windows；Linux/macOS 用 venv/bin/activate
pip install -i https://mirrors.aliyun.com/pypi/simple -r requirements.txt
cp .env.example .env                  # 按需改 DB / REDIS / SECRET
cd frontend && npm install && npm run build && cd ..
```

---

## 2. 目标项目结构（本脚手架）

```
work/testhub/
├── manage.py
├── testhub/                 # Django 项目包
│   ├── settings.py          # INSTALLED_APPS / DB 切换 / Celery / 端口池
│   ├── urls.py              # 各 app API 挂载（含 code-analysis/accel-skills/deploy）
│   ├── asgi.py  wsgi.py
├── apps/
│   ├── code_analysis/       # 【新建①】AST 功能点 + change_log（models 已就位）
│   ├── accel_skills/        # 【新建②】Skill 资产库（models 已就位）
│   ├── deployment_target/   # 【新建③】只读克隆+端口池+托管+探活（models 已就位）
│   ├── projects/ testcases/ reports/ reviews/ requirement_analysis/
│   ├── ui_automation/ executions/ core/ users/ monitor/   # 复用 testhub 既有
├── frontend/                # Vue3（src/views|api|store|router|locales）
├── requirements.txt  .env.example  start_dev.sh
├── MIGRATION.md  TASK_PLAN.md  README.md
```

---

## 3. 分步执行（顺序遵循 §12.6，每步可独立验收）

### 阶段 0 · 脚手架与依赖
```bash
cd work/testhub
python manage.py check            # 配置自检
python manage.py migrate          # 既有 app 建表
```
> 本脚手架三新建 app 的 `models.py` 已写入，下一步即可 makemigrations。

### 阶段 1 · 纯逻辑模块平移（≈421 行，近乎零改动，难度极低）
将 `work/test-accel/backend/modules/` 下**零框架依赖**的模块原样迁入 `apps/code_analysis/logic/` 或独立 `libs/`：
- `code_analyzer.py`（182 行）— AST 功能点抽取，纯逻辑，直接复用
- `smoke.py`（152 行）— 探活，**改为复用 testhub `monitor`**（§12.5，勿重建）
- `config.py`（48 行）— 配置项，对齐 testhub settings
- `llm_client.py`（39 行）— **不自带**，改复用 `requirement_analysis.AIModelService`（§11.4）

```bash
# 例：把 code_analyzer 作为 code_analysis 的逻辑层
mkdir -p apps/code_analysis/logic
cp ../test-accel/backend/modules/code_analyzer.py apps/code_analysis/logic/
```
> 严禁在 FastAPI(test-accel) 端先补 skill_generator/scheduler/review_gate/前端——按 §12.5 会写两遍，应在 testhub 栈直接实现。

### 阶段 2 · 数据模型迁移（db.py 7 表 → Django models）
映射关系（§11.7）：

| 原 SQLite 表 | testhub 落点 | 文件 |
|--------------|--------------|------|
| `projects` | 扩展 `projects.Project` 或 `deployment_target` | apps/projects、apps/deployment_target/models.py |
| `functional_points` | **新建** `code_analysis.FunctionalPoint` | apps/code_analysis/models.py（已就位） |
| `cases` | **复用** `testcases`（勿新建双套） | apps/testcases |
| `skills` | **新建** `accel_skills.Skill` | apps/accel_skills/models.py（已就位） |
| `runs` | **复用** `executions.TestRun/TestRunCase` | apps/executions |
| `reports` | **复用** `reports.TestReport` | apps/reports |
| `change_log` | **新建** `code_analysis.ChangeLog` | apps/code_analysis/models.py（已就位） |

```bash
python manage.py makemigrations code_analysis accel_skills deployment_target
python manage.py migrate
```

### 阶段 3 · 路由改写 + 裸 SQL → ORM
- `main.py` 8 个路由 → `apps/*/views.py` + DRF ViewSet/Serializer（改写 228 行，低-中难度）
- 原 18 处裸 SQL → Django ORM（集中在 project_manager/case_generator/executor/reporter）
- **关键防双套**：`cases` 落到 `testcases`、`runs` 落到 `executions`、`reports` 落到 `reports`，不要新建 parallel 表。

```bash
# 为每个新建 app 补 urls.py + views.py + serializers.py 后：
python manage.py makemigrations && python manage.py migrate
```

### 阶段 4 · 复用 testhub 既有能力（先复用再补差）
| 平台模块 | 复用对象 | 动作 |
|----------|----------|------|
| LLM | `requirement_analysis.AIModelService` | 新增 writer/reviewer 配置（qwen，dashscope）；**API Key 入库非 .env**（§11.4） |
| 执行引擎 | `ui_automation.playwright_engine` | 新增"代码派生 case"执行入口，不重写引擎 |
| 报告 | `reports` + Allure | 基线对比用扩展字段 |
| 审查门 | `reviews` 工作流 | 承载 functional_points/cases 的 review_status |
| 探活 | `monitor` | 复用，勿重建 |
| 调度 | `core` management commands + Celery beat | 增量回归作为 beat 任务 |

### 阶段 5 · 新建三个 app（§11.3，直接在 testhub 栈实现）
1. `code_analysis`：补 `views.py`（功能点 CRUD + `diff_analyze` 端点：`git diff --name-status base..head` → 三向分类 new/updated/removed，逻辑平移自 `diff_analyzer.py`）+ `urls.py`。
2. `accel_skills`：补 `views.py`（skill.yaml/playbook.md/helpers 版本化、复用计数、回流闭环）。
3. `deployment_target`：补 `services.py`（只读 git 克隆 → 端口池分配 → `run_command` 起进程 → `health_url` 探活 → 日志落盘）。

```bash
python manage.py makemigrations accel_skills deployment_target
python manage.py migrate
```

### 阶段 6 · 前端 Vue3（7 页面 + i18n，全新，工期大头）
在 `frontend/src/` 下新增模块，接入既有 router/store/api，**必须 vue-i18n（zh/en/ja/ko）**，不达标不通过合并验收（§11.9）：
`views/`：仪表盘 / 项目 / 功能点 / 执行 / 报告 / Skill 库 / 设置。

```bash
cd frontend && npm run dev -- --port 3000   # 开发；生产 npm run build
```

### 阶段 7 · 部署与密钥（§11.8）
```bash
bash start_dev.sh
# 后端 Daphne :8000 | Celery worker+beat | 前端 :3000
# 被测目标服务由 deployment_target 用独立端口池（默认 8100–8199）托管
```
- `.env` 仅留 DB/Redis/SECRET/邮件；LLM 凭据入库。
- 目标服务进程托管、探活、日志由 `deployment_target` 负责。

---

## 4. 命令速查（可直接复制执行）

```bash
cd work/testhub && source venv/Scripts/activate      # 激活环境
python manage.py check                               # 配置自检
python manage.py makemigrations code_analysis accel_skills deployment_target
python manage.py migrate                             # 建/更全部表
python manage.py runserver 8000                      # 开发后端（或用 start_dev.sh 起 Daphne+Celery）
python manage.py shell                               # 校验模型、导入 test-accel 实测数据
cd frontend && npm install && npm run build          # 前端构建
bash start_dev.sh                                     # 一键开发环境
```

## 5. 验证清单（每阶段结束核对）
- [ ] 阶段1：`code_analyzer` 逻辑在 Django 环境下 `import` 可用，产出与原 FastAPI 一致
- [ ] 阶段2：`code_analysis.FunctionalPoint` / `ChangeLog`、`accel_skills.Skill`、`deployment_target.*` 迁移成功，`python manage.py migrate` 无报错
- [ ] 阶段3：`/api/code-analysis/diff` 端点返回结构与 `test-accel` 的 `POST /api/projects/{pid}/diff_analyze` 等价（文件级 diff 与 `git diff --name-status` 一致）
- [ ] 阶段4：`AIModelService` 可切换 qwen/deepseek；`playwright_engine` 可承接代码派生 case；`reviews` 承接审查门
- [ ] 阶段5：三新建 app 端点可用；`deployment_target` 能克隆+分配端口+起目标服务+探活
- [ ] 阶段6：7 个前端页面可访问且通过 i18n 校验
- [ ] 阶段7：`start_dev.sh` 一键拉起；`data/test_accel.db`（151KB 实测）可迁移进 testhub DB

## 6. 风险与回滚（§12.5）
| 级别 | 风险 | 缓解 |
|------|------|------|
| 中高 | 前端是纯增量不是移植（工期大头） | 勿被"后端仅 1091 行"误导，单独排期 |
| 中 | 先补再搬造成返工 | skill_generator/scheduler/review_gate/前端**只在 testhub 栈实现** |
| 中 | 数据模型语义重叠建双套 | `cases/runs/reports` 严格复用 `testcases/executions/reports` |
| 中 | 目标服务托管缺位 | §11.3 `deployment_target` 必须补齐（research-agent 需起前后端两进程） |
| 低 | 裸 SQL 隐式语义（DELETE 全量重建） | 迁 ORM 时做版本化/级联，保留历史 |
| 低 | `executor` 非真浏览器 | 合并后真跑 UI 接 `playwright_engine`（增量） |

> 回滚：每阶段提交独立 git 节点；若某阶段验收失败，回退该节点即可，不影响已合并的纯逻辑层。
