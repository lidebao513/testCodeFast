# testgen-service 迁移至 testhub 可行性评估与迁移报告

> 评估对象：
> - 源：`testCodeFast/work/testgen-service`（FastAPI 微服务，代码→测试资产生成引擎 + 安全专项）
> - 目标：`testhub_platform`（Django 4.2 + DRF + Vue3 测试中心平台，21 个 app）
>
> 结论先行：**可行**，推荐「同仓独立 FastAPI 微服务（sidecar）」形态——把 testgen 代码迁进 testhub 仓库，仍作为独立进程运行，由 testhub 经 HTTP 调用。**不建议**改写为 Django app（那等于重写，丧失 testgen 的独立演进能力）。
> 迁移后**可被直接调用**：是（testgen 已是成熟 REST 服务，自带 `/api/v1/*` 完整接口）。

---

## 一、可行性结论

| 维度 | 结论 | 依据 |
|------|------|------|
| 能否直接调用 | ✅ 能（HTTP REST） | testgen 已是 FastAPI 服务，含 `/api/v1/generate`、`/api/v1/execute`、`/api/v1/analyze`、`/api/v1/pull`、`/health`、`/ready` 等完整接口；异步任务 + 幂等 + 轮询 + `X-Auth-Token` 鉴权 + CORS `*` 齐备 |
| 接口兼容性 | ✅ 高 | REST/JSON，与 testhub 现有对外调用模式（Dify/LLM/MCP，均用 httpx/requests）一致；无需改 testgen 接口契约 |
| 依赖项 | ✅ 极利好 | testhub `requirements.txt` **已包含 testgen 几乎全部运行时依赖**，仅缺 `fastapi` 本体（starlette/uvicorn/pydantic 已在） |
| 环境配置 | ✅ 低侵入 | testgen 100% 环境变量驱动，自带 `.env.example`；可保有自己的 `.env`，与 testhub 的 decouple 配置互不干扰 |
| 冲突/风险 | ⚠️ 可控 | 仅 starlette 版本协同、DB 选型、质量门禁归属、密钥管理、Git 历史等需处理（见第五节） |

---

## 二、接口兼容性

**testgen 现状（已核实 `service/app.py`）**
- 框架：FastAPI，`service.app:app`，经 `python -m cli.main serve [--host --port]` 启动（uvicorn）。
- 版本化前缀 `/api/v1`，统一错误体 `{code,message,detail?}`，每请求 `X-Request-ID`。
- 业务端点：`/api/v1/pipeline`（同步一站式）、`/api/v1/generate`（异步生成-only，202+轮询）、`/api/v1/execute`、`/api/v1/analyze`（仅扫描+功能点提取）、`/api/v1/pull`（取码）、`/api/v1/compare`、`/api/v1/parse-input`、`/api/v1/dialogue/*`、`/api/v1/verify/webhook`（发布流水线触发）、`/api/v1/metrics`、`/api/v1/projects/{pid}/*`（资产/报告/覆盖率/执行批次）。
- 鉴权：`require_auth` 依赖 `X-Auth-Token` 头，**`settings.auth_token` 为空时不校验**（内网/开发默认放行）——这对服务间调用极友好。
- 探针：`/health`（存活）、`/ready`（DB 就绪）。

**与 testhub 调用方兼容**
- testhub 已用 `httpx`/`requests` 调外部服务（Dify assistant、LLM、MCP server，`apps/*` 均有先例），新增「调 testgen」的客户端是同类工作，无新范式。
- 契约差异：testgen 用统一契约 v1.0（`fp_id/tp_id/case` = 内容 md5），testhub 资产模型为自增主键的 `TestCase/TestSuite`。**需做一层字段映射**（testgen 输出 → testhub 资产模型），但不影响「调用」，只影响「资产回流」。

---

## 三、依赖项（核心利好，已逐项核对 `requirements.txt`）

| testgen 依赖（pyproject） | testhub 是否已有 | 版本 |
|--------------------------|----------------|------|
| `fastapi`（本体） | ❌ 缺（**唯一需新增**） | — |
| `uvicorn[standard]` | ✅ | 0.40.0 |
| `starlette` | ✅（fastapi 依赖，已随 sse-starlette/daphne 引入） | 0.50.0 |
| `pydantic` / `pydantic-settings` | ✅ | 2.12.5 / 2.12.0 |
| `python-dotenv` | ✅ | 1.2.1 |
| `openai` | ✅ | 2.14.0 |
| `httpx` | ✅ | 0.28.1 |
| `requests` | ✅ | 2.32.4 |
| `PyYAML` | ✅ | 6.0.2 |
| `playwright`（runtime 可选） | ✅（已装） | 1.57.0 |
| `openpyxl`/`reportlab`/`python-docx`（报告导出可选） | ✅（已装） | 3.1.5 / 4.2.0 / 1.2.0 |
| `pyotp`（OTP 生命周期） | ✅ | 2.9.0 |

**结论**：testgen 可运行在 **testhub 现有 Python 环境**中，只需新增 `fastapi` 一个依赖，**重依赖（playwright/pydantic/openai/openpyxl/reportlab/python-docx/pyotp）零重复安装、零版本冲突**。这是本迁移最大的可行性利好——彻底规避了「两套环境/依赖地狱」风险。

> 唯一需谨慎的依赖点：testhub 现有 `starlette==0.50.0`（被 `sse-starlette`/`daphne`/`channels` 依赖）。安装 `fastapi` 时**必须选与 starlette 0.50 兼容的版本**（如 `fastapi>=0.116`，其 starlette 约束覆盖 0.50），避免 pip 把 starlette 降级破坏 testhub 的 WebSocket/ASGI 链路。建议显式 `pip install "fastapi==0.116.*" "starlette==0.50.0"` 锁定。

---

## 四、环境配置

**testgen 配置面（已核实 `core/config.py`）**：全部来自环境变量，启动时集中校验、快速失败；自带 `.env.example`。关键变量：

| 变量 | 默认 | 说明 |
|------|------|------|
| `HOST` / `PORT` | 127.0.0.1 / **8100** | 服务监听；建议显式配置 |
| `DB_PATH` / `DATA_DIR` / `OUTPUT_DIR` / `WORKSPACE_ROOT` | `data/testgen.db` 等（相对 PROJECT_ROOT） | 已支持环境变量覆盖 |
| `AUTH_TOKEN` | 空（不校验） | 服务间调用建议**设为共享密钥** |
| `LLM_*` / `EXPERT_*` | — | LLM/专家通道（生成增强用） |
| `RUNTIME_UI_*` / `EXECUTOR_*` | 默认关 | 运行时 UI 发现/执行（按既定计划下沉 testhub，迁移期可保持关闭） |
| `FP_SEMANTIC_MERGE` | true | 功能点语义合并（testgen 独有卖点，保持开启） |

**与 testhub 配置共存策略**
- testhub 用 `python-decouple` 的 `config()` 读自身 `.env`；testgen 用 `python-dotenv` 读**自己目录下的 `.env`**（`load_dotenv(PROJECT_ROOT/.env)`）。两者读取机制不同、目录隔离，**命名冲突概率极低**。
- 为绝对安全：testgen 迁入后保留独立 `services/testgen/.env`，不混入 testhub 根 `.env`；`HOST/PORT/DB_PATH` 等仅作用于 testgen 进程，不会误触 Django 的 `SECRET_KEY`/`DATABASES`。
- **端口**：testgen 默认 8100，与 Django runserver(8000)/daphne 不冲突；仍建议显式写入 `.env` 并登记到部署文档。

---

## 五、潜在冲突与风险（逐条，均带缓解）

| # | 风险 | 严重度 | 缓解措施 |
|---|------|--------|---------|
| R1 | **starlette 版本协同**：testhub 0.50.0 被 WebSocket 链路依赖，fastapi 安装可能降级它 | 中 | 锁定 `fastapi==0.116.*` + `starlette==0.50.0`；迁移后用 testhub 现有 WebSocket/ASGI 冒烟测试验证 |
| R2 | **Python 版本**：testgen 要求 `>=3.11`，testhub 运行时版本未显式核实 | 低 | 迁移前确认 testhub 部署 Python `>=3.11`（requirements 含大量现代库，几乎确定满足）；不满足则升 testhub 运行时 |
| R3 | **框架共存**：FastAPI(Starlette) + Django 同仓 | 低（若分进程） | **必须分进程部署**，绝不在同一 ASGI app 内挂载两个框架；testgen 独立 uvicorn 进程，testhub 独立 gunicorn/daphne |
| R4 | **DB 选型**：testgen SQLite vs testhub MySQL | 无冲突 | 迁移期 testgen 保留自有 SQLite（文件独立）；「资产共享到 testhub MySQL」是 R2 级重写，属后续规划，不在本次迁移范围 |
| R5 | **质量门禁归属**：testgen 八门禁（ruff/mypy/bandit/pytest/secret）vs testhub 自身 CI | 中 | testgen 迁入后保留其 `pyproject.toml` 门禁定义，CI 新增一个「testgen 包」独立 job；不强行并入 testhub 的 Django pytest |
| R6 | **密钥/凭证管理**：`.env` 含 AUTH_TOKEN/LLM key/运行时候选凭据 | 中 | 确保 `services/testgen/.env` 被 testhub `.gitignore` 覆盖；AUTH_TOKEN 用 testhub↔testgen 共享的服务密钥，不入库；testgen 对登录密码/OTP 已做掩码（不回显/不落库） |
| R7 | **Git 历史丢失**：跨仓库搬代码默认丢历史 | 低 | 用 `git subtree add` / `git filter-repo` 将 testgen 作为子树迁入，**保留提交历史**；勿直接 copy 目录 |
| R8 | **Playwright 浏览器二进制**：runtime_ui 需浏览器内核 | 低（迁移期可关） | 迁移期 `RUNTIME_UI_ENABLED=off`；若启用，复用系统 Edge（`PLAYWRIGHT_CHANNEL=msedge`，testgen 已支持），免下载 chromium |
| R9 | **异步任务后端**：testgen 为进程内 `BackgroundExecutor`+`TaskStore` | 低 | 迁移期够用；后续可换 testhub 已有的 redis+celery 作为 broker（testhub 已装 redis/celery），提升横向扩展 |
| R10 | **范围控制**：testgen `/api/v1/execute` 自带执行 | 低 | 按既定规划（前两份报告），执行最终下沉 testhub；迁移期保留 execute 可用，但明确「生成→testhub 执行」为演进方向，避免双份执行引擎长期并存 |

> 综合：无「不可解」的硬冲突，全部为可计划缓解的中低风险。

---

## 六、完整迁移步骤

**Phase 0 — 准备**
1. 确认 testhub 部署 Python `>=3.11`（R2）。
2. 用 `git subtree add` 将 `testgen-service` 作为子树迁入 testhub 仓库（R7，保历史）。
3. 在 testhub venv 安装 `fastapi==0.116.*`（锁定 starlette 0.50.0，R1）。

**Phase 1 — 落位**
4. 将代码置于 `services/testgen/`（见第七节结构），保留 `pyproject.toml`/`.env.example`。
5. 新建 `services/testgen/.env`：设 `PORT=8100`、`HOST=0.0.0.0`（或内网 IP）、`AUTH_TOKEN=<共享密钥>`、`RUNTIME_UI_ENABLED=off`、`FP_SEMANTIC_MERGE=true`；确认 `.env` 被 gitignore。
6. 确认 `DATA_DIR/OUTPUT_DIR/WORKSPACE_ROOT/DB_PATH` 指向 testhub 数据卷（避免写进代码目录，R4）。

**Phase 2 — 启动校验（testgen 独立）**
7. 在 testhub venv 启动：`python -m cli.main serve --host 0.0.0.0 --port 8100`（工作目录 `services/testgen`）。
8. 探活：`GET /health` → `status=ok`；`GET /ready` → `status=ready`。

**Phase 3 — testhub 接入（新增客户端）**
9. 在 testhub 新增客户端模块（建议 `apps/testgen_integration/client.py` 或 `backend/testgen_client.py`），封装：base_url 读取、注入 `X-Auth-Token`、提交 `/api/v1/generate`、轮询 `/api/v1/tasks/{id}`、取 `project_id`。
10. `backend/settings.py` 增加 `TESTGEN_BASE_URL`、`TESTGEN_AUTH_TOKEN`（用 `config()` 从根 `.env` 读，与 testgen 自身 `.env` 分离）。
11. 可选：建 `apps/testgen_integration` Django app，暴露 `/api/testgen/generate` 薄代理 + 资产回流逻辑。

**Phase 4 — 资产回流（可选，R4 后续）**
12. 写映射层：testgen `fp/tp/case`(md5) → testhub `TestCase`/`TestSuite`/`Defects`（幂等：以 md5 为外部 ID，避免重复）。
13. 安全专项产出（AUTH/PRIV_ESC 维度用例）经映射进入 testhub 用例库 + 缺陷库。

**Phase 5 — 流水线接入**
14. 发布流水线调用 testgen `POST /api/v1/verify/webhook`（带 `repo_url`/`commit`/`base_url`/`scopes`/`execute`），触发「生成（+可选执行）」。

**Phase 6 — 门禁与部署**
15. CI 新增 testgen 包门禁 job（跑其 `pyproject.toml` 八门禁 + pytest，R5）。
16. 部署：将 testgen 作为独立进程/compose service 纳入 testhub 运维（进程管理用 systemd/supervisor 或 compose `depends_on`）；与 Django/gunicorn 分进程（R3）。

---

## 七、目标目录结构（建议）

```
testhub_platform/
├── services/
│   └── testgen/                      # 迁入的 testgen-service（独立 FastAPI 服务）
│       ├── core/  engine/  service/  cli/  output/  workspace/
│       ├── data/   outputs/          # 运行时数据（由 DATA_DIR/OUTPUT_DIR 指定，gitignore）
│       ├── pyproject.toml            # 保留八门禁定义
│       ├── .env.example
│       └── .env                      # 新建，gitignore
├── backend/
│   ├── settings.py                   # 增加 TESTGEN_BASE_URL / TESTGEN_AUTH_TOKEN
│   └── testgen_client.py             # testhub 侧 HTTP 客户端（封装 token + 轮询）
├── apps/
│   └── testgen_integration/          # 可选 Django 薄壳 app（代理 + 资产回流）
│       ├── client.py                 # 复用 backend/testgen_client.py
│       ├── mapping.py                # md5(fp/tp/case) → TestCase/TestSuite/Defects
│       └── views.py                  # /api/testgen/generate 等
└── ...（原有 backend/ apps/ frontend/ 不动）
```

> 关键：**不动 testhub 现有 21 个 app 与 Django 配置**；testgen 作为 `services/` 下的独立服务存在，与 `backend`/`apps`/`frontend` 平级。

---

## 八、需修改的代码点

**testgen 侧（最小改动）**
- `core/config.py`：端口/主机默认已可从 env 覆盖，**无需改逻辑**，只需在 `.env` 配 `PORT/HOST`；`AUTH_TOKEN` 已支持。
- `service/app.py`：生产建议将 CORS `allow_origins=["*"]` **收窄**为 testhub 前端域名（当前仅演示用）；其余接口/契约**不改**。
- 可选：`service/tasks.py` 异步后端由进程内改为 celery+redis（R9，非必须）。
- 可选：日志接入 testhub 统一日志（当前为 json 格式，基本兼容）。
- **业务逻辑、生成链路、安全专项、统一契约一律不改**——保持 testgen 独立演进，这是它作为「生成微服务」的价值锚点。

**testhub 侧（新增为主，少改）**
- 新增 `backend/testgen_client.py`：HTTP 客户端（base_url + `X-Auth-Token` + 提交/轮询）。
- `backend/settings.py`：新增 `TESTGEN_BASE_URL`、`TESTGEN_AUTH_TOKEN`（decouple `config()`）。
- 可选 `apps/testgen_integration/`：代理视图 + 资产映射（md5 → 自增主键幂等）。
- `requirements.txt`：新增 `fastapi==0.116.*`（R1）；其余依赖已具备。
- `.gitignore`：确保 `services/testgen/.env` 与 `data/`、`outputs/` 被忽略（R6）。
- **不改**：testhub 现有 app、MySQL、Django 配置、前端。

---

## 九、迁移后调用验证方式

**1. testgen 自身门禁（迁入即跑）**
- `pytest`（testgen 自带，覆盖 core/engine/service）；八门禁（ruff/mypy/bandit/secret）由 CI job 跑。

**2. 服务探活**
- `GET /health` → `{"status":"ok","service":"testgen-service","contract_version":1}`。
- `GET /ready` → `{"status":"ready","config":{...}}`（DB 可用才 ready）。

**3. 端到端调用验证（testhub 视角，建议写成集成测试）**
```
POST /api/v1/generate
  Header: X-Auth-Token: <共享密钥>
  Body: { "local_path": "<被测代码目录>", "mode": "full", "scopes": ["正常","安全","边界"] }
→ 202 + task_id + poll_url
GET  /api/v1/tasks/{task_id}        # 轮询至 state=success
→ result.project_id
GET  /api/v1/projects/{pid}/cases   # 校验用例数 > 0
```
- 同步对照：`POST /api/v1/pipeline`（一次性脚本/本地调试）直接返回 result。

**4. 契约校验**
- `GET /health` 返回的 `contract_version` 应与 testgen 统一契约 v1.0 一致；若启用 OpenAPI，可拉 `/openapi.json` 与 testhub 侧 schema 比对。

**5. 安全专项验证（testgen 独有卖点）**
- `scopes` 含 `安全` → 检查产出用例 `dimension/severity` 含 `AUTH`/`PRIV_ESC`；`/api/v1/analyze` 应返回功能点（含安全类 `ftype`）。

**6. 失败/边界用例（红线与健壮性）**
- 错误 token：`X-Auth-Token` 错 → 401 `unauthorized`。
- 生成红线：`/api/v1/generate` 带 `execute:true`/`exec_url` → 422（生成-only 红线不被破坏）。
- 幂等：同一 `(路径/mode/scopes/...)` 重复提交 → 返回既有 `task_id`（不重跑）。
- 取码失败：`/api/v1/pull` 远端不可达 → `success=false` + `status`（不抛 5xx）。

---

## 十、TL;DR

- **可行**，且依赖层面极其友好：testhub 已装 testgen 几乎全部运行时依赖，**只缺 `fastapi` 一个包**，加包即可同环境运行，无依赖地狱。
- 推荐形态：**同仓独立 FastAPI 微服务（sidecar）**，不改写为 Django app；迁移后**可被 testhub 直接 HTTP 调用**（接口已就绪）。
- 主要技术风险仅 **starlette 版本协同**（锁定 `fastapi==0.116.*`+`starlette==0.50.0`）与 **Python>=3.11 确认**，均为中低且可计划缓解；DB（SQLite vs MySQL）、框架共存（分进程）、密钥（独立 `.env`+gitignore）均无硬冲突。
- 迁移=「代码落位 + 新增 testhub 客户端 + 配置 token/端口」，**testgen 业务逻辑零改动**，延续其作为「代码→测试资产生成微服务 + 安全大脑」的定位（与前两份报告规划一致）。
- 落地第一步待确认：testhub 部署实例的 **Python 版本**、**是否复用 testhub venv**（建议是）、以及给 testgen↔testhub 的**共享服务 token**。
