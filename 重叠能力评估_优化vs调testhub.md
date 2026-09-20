# 评估：testgen 重叠能力该「本地优化」还是「调 testhub 接口」

> 背景：上一轮已梳理 testgen（testCodeFast/testgen-service）与 testhub（testhub_platform）的 10 项功能重叠。本篇聚焦一个决策问题——**在重叠功能上，testgen 哪些能力弱于 testhub？弱的部分是否应直接调 testhub 接口而非在 testgen 上追赶？**
>
> 已核实事实（本轮）：
> - testhub 是 Django+DRF+Vue，**21 个 app、完整 DRF API 面**，且自带 OpenAPI schema（`/api/schema/`、Swagger `/api/docs/`、Redoc `/api/redoc/`）——接口**自描述**，testgen 可 introspect 全契约。
> - 鉴权 = **JWT（SimpleJWT 为主，Token 兼容）**，经 `/api/auth/` 取 token，后续 `Authorization: Bearer`。
> - **自动化执行可被 API 驱动**：`ui_automation` 有 `TestCaseViewSet.run` / `mcp_runner.start_case_execution`（Playwright+Selenium+AI agent）；`api_testing` 有 `ApiRequestViewSet.execute` / `TestSuiteViewSet.execute`（HTTP+WebSocket）。即 testhub 不是「只登记结果」，而是真能跑。
> - 但 testhub 仓内**无** `code_analysis`/`deployment_target`/`accel_skills`/`migrate_test_accel_data` 等接入代码——**适配器尚未建**，调接口需要 testgen 侧新写客户端。

---

## 一、逐能力强弱对比与裁决

判定口径：
- **调 testhub** = 该能力 testhub 明显更强/更成熟，testgen 应停掉自己的实现、改为调用 testhub 接口。
- **本地保留** = testgen 在此能力上更强/独有，应留在 testgen 并强化。
- **混合** = testgen 保留「大脑」（设计/判定），把「手脚」（驱动）交给 testhub。

| # | 重叠能力 | testgen 现状 | testhub 现状 | 裁决 | 关键理由 |
|---|---------|------------|------------|------|---------|
| O2 | UI 执行驱动 | 单引擎 Playwright，自校验式 harness | Playwright+Selenium+AI(browser-use)+MCP，多模型，真平台 | **调 testhub** | testhub 是多引擎产品级；testgen 是「够用版」自校验，追平=再造 testhub |
| O3 | API 执行驱动 | 仅 HTTP，强耦合生成 TP | HTTP+WebSocket、集合/环境管理、Allure、调度 | **调 testhub** | testhub 的 api_testing 是完整接口测试平台 |
| O2/O3 判定层 | 执行结果判读 | **五维安全判定**（NORMAL/ABNORMAL/AUTH/PRIV_ESC/BOUNDARY）强；通用断言弱 | locator/assertion 通用断言强；**无安全语义判读** | **混合：testgen 保留判定层** | testgen 把安全语义判读（尤其越权/边界）作为大脑；testhub 只当驱动手脚 |
| O4 | 报告导出 | md/html/json + 可选 pdf/docx/xlsx | Allure（工业标准）+ reportlab + openpyxl，平台统一 | **调 testhub** | 统一报告走 testhub；testgen 保留生成期 md/json 预览即可 |
| O5 | 缺陷管理 | 缺陷信息散落本地 `runs`/SQLite | 完整 `Defect` 生命周期（severity/priority/status/type/source） | **调 testhub** | 把 testgen 派生的缺陷推到 `/api/defects`，闭环在平台 |
| O9 | 资产持久化 | SQLite 本地、临时态 | MySQL+Django，多项目/版本/套件/执行 | **调 testhub** | 生成结果应落到 testhub（TestCase/TestSuite/executions），不再自建库 |
| O8 | 性能测试 | `PERFORMANCE` 测试点**诚实 SKIPPED** | jmeter/locust/httpx 完整引擎 + SLA/基线 | **调 testhub** | 直接用，不自研 |
| O6 | 对话/智能体入口 | 内部 `dialogue/agent` | Dify `assistant` 产品化 | **调 testhub** | 前端入口统一到 testhub，testgen 暴露生成 API 供其调用 |
| O7 | 文档→用例 | `prd_ingest` 默认关 | `requirement_analysis` 成熟（PDF/DOCX→LLM） | **调 testhub** | 文档通道以 testhub 为唯一入口 |
| O10 | 对比/复核 | expected vs actual | `reviews` + `llm_judge` 正式评判 | **调 testhub** | 正式评审/评判交给 testhub |
| O1(代码) | **代码→用例生成** | `scan/fp_extract/diff_tag/tp_expand` **独有且强** | 无（仅文档级） | **本地保留+强化** | testgen 核心卖点，testhub 不具备 |
| 安全 | **安全专项** | `auth_scan` + `tenant_retest` + 五维安全判定 **独有且强** | 无对应 app | **本地保留+强化** | testgen 差异化壁垒 |
| 编排 | 生成链编排 | `pipeline` + `fp_merge` 语义合并 **独有** | 无 | **本地保留** | 把代码变更转测试资产的编排逻辑是价值锚点 |
| O6(基建) | LLM 基础设施 | 各自封装 client | 各自封装 client | **抽公共库** | 两边共用 base_url/model/retry/代理/密钥，避免重复踩坑 |

---

## 二、结论先行（直接回答你的问题）

**绝大多数重叠能力应该「调 testhub 接口」，而不是在 testgen 上优化追赶。** 只有三块必须留在 testgen 并强化：代码级生成、安全专项、生成链编排（含五维安全判定层）。

理由：
1. testhub 在「执行驱动、报告、缺陷、资产持久化、性能、对话入口、文档→用例、评审」上**明显更强且是产品级**；testgen 在这些上是为「自校验生成质量」补的够用版。在 testgen 里把这些追平，等于再造一个 testhub——这正是我们要消除的重叠。
2. testgen 真正强且 testhub **完全没有**的只有：代码级生成、安全专项（越权/边界/鉴权判读）、生成链编排。这三块是 testgen 并入 testhub 的**价值锚点**，必须保留。
3. 一个关键细节：**即使把执行驱动交给 testhub，testgen 也要保留「五维安全判定层」**。testhub 的执行引擎按 locator/assertion 判通过失败，不懂「无凭证访问应被拒」「越权访问应被拒」这类安全语义。所以最优姿势是——testhub 当「手脚」（驱动浏览器/HTTP），testgen 当「安全大脑」（设计安全测试点 + 判读结果）。

---

## 三、推荐落地姿势（混合架构，不是二选一全调）

```
代码/PRD ──► testgen(生成微服务)
              │  代码级生成 + 安全测试点设计 + 五维判定层
              ▼
         推送到 testhub：/api/projects · /api/testcases · /api/testsuites
              │
              ▼  需要跑执行时
         testgen 调 testhub：/api/ui-automation/.../run  ·  /api/api_testing/.../execute
              │  拿回原始结果
              ▼
         testgen 用自己的五维判定（尤其安全）判读 ──► 缺陷推 /api/defects
              ▼
         报告统一走 testhub（Allure）或复用其导出
```

即：testgen **退守为「代码→测试资产生成微服务 + 安全测试大脑」**，执行/报告/缺陷/资产/性能/对话入口全部下沉或复用 testhub。

---

## 四、调 testhub 的前提与风险（动手前必读）

1. **适配器未建**：testhub 仓内无接入代码，`migrate_test_accel_data` 在 testCodeFast 侧而非 testhub 侧。需要 testgen 新写：
   - JWT 客户端（取 token → Bearer，处理刷新）；
   - schema 映射（testgen 的 `fp_id/tp_id/case`(md5) ↔ testhub `TestCase`/`TestSuite`/`executions`/`defects`）；
   - 把 `/api/v1/execute` 改造为「调 testhub 执行引擎」的薄层，**保留五维判定**作为判读外包结果的智能。
2. **硬依赖**：testgen 调 testhub 前提是 **testhub 已部署且网络可达**。对该用户场景（部署后自动验证、平台内远程调用）可接受；但 testgen 本地离线开发时会多一层依赖，需保留「本地 dry-run 最小执行」兜底。
3. **首个待确认项**：testhub 当前是否有运行实例？base URL 是什么？是否有给 testgen 用的服务账号/凭证？——这是落地第一步，需你确认。
4. **安全判定归属**：若执行走 testhub 通用引擎，务必保证 testgen 的五维安全判定层不被丢弃，否则安全测试能力会从「强」退化成「只会点页面」。

---

## 五、一句话决策表（给你快速拍板）

- ✅ **调 testhub**：UI 执行、API 执行、报告导出、缺陷、资产持久化、性能测试、对话入口、文档→用例、评审复核。
- 🔒 **留在 testgen 并强化**：代码级生成、安全专项（auth_scan/tenant_retest + 五维判定）、生成链编排。
- 🤝 **混合（testgen 大脑 + testhub 手脚）**：执行驱动交给 testhub，安全判定层留在 testgen。
- 🛠️ **两边都做**：抽公共 LLM client 库。
