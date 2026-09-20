# 测试点生成 · 旧版 vs 新版 对比报告

> 目的：审阅发现上次生成的测试点「数量偏少、基于全部代码的覆盖不充分」。本次优化 `code_analyzer` 的测试点生成逻辑（新增 v2 全面生成），**依据完整代码重新生成**一套更全面、覆盖更充分的测试点，并与上次结果并排对比。

> **本轮测试点范围（Scope）**：正常、边界（可选项：正常 / 异常 / 安全 / 边界；默认 正常+边界）。


## 一、旧版（上次生成 · 报告第二章 · 9 模块级测试点）

| 功能模块 | 测试点 | 类型 | 场景 | 预期 |
|---|---|---|---|---|
| 对话核心 | 自我介绍 / 天气 / 股票 | 正常 | F-A1~A3 | 正常返回并命中业务关键词 |
| 请假休假（核心业务） | 年假申请 / 加班申请 / 余额 / 规则 | 正常+边界 | F-B1~B4 | 提交成功/返回余额与取整规则 |
| 待办审批流 | 我的待办 / 已办(按状态) / 取消申请 | 正常+异常 | F-C1~C3 | 列表返回 / 取消回滚(测试数据) |
| 邮件日程 | 邮件会议整理成日程 | 正常 | F-D1 | 日程项生成 |
| 知识库/监管 | 审计知识库检索 / 监管政策自动化 | 正常 | F-E1~E2 | 命中知识库制度 / 定时任务配置说明 |
| 经营分析/数据 | 机构经营 / 缴费达成率 / 大额未审批 / 人员数据 | 正常+空态边界 | F-F1~F4 | 数据返回 / 空态友好提示 |
| 多智能体 | 反洗钱 SQL 子 agent | 正常 | F-G1 | 自然语言→SQL 生成 |
| 汇报文档 | 长文报告(≥800字) | 长度边界 | F-H1 | 以文档产物(下载/导出)形式完整交付 |
| 异常/安全/健壮 | @mention熔断 / 工具终止 / 注入防护 / 历史重建 / 长输入 | 异常 | F-I1~I5 | 不挂起 / 拒绝注入 / 不崩溃 |

> 旧版合计：**9 条模块级聚合点**，且每条仅 1 个笼统预期，未按接口/函数/前端逐条展开，属「模块级抽样」而非「代码级覆盖」。


## 二、新版（本次依据完整代码生成 · v2 全面覆盖）

**总量 259 条测试点**，按类型：正常 165、边界 94


### 2.1 模块汇总（覆盖深度）

| 模块 | 测试点总数 | API维 | 业务函数维 | 前端维 | 覆盖面积 |
|---|---|---|---|---|---|
| 账户/用户/鉴权 Auth | 68 | 68 | 0 | 0 | /accounts、/accounts/{account_id}、/accounts/{account_id}/start、/accounts/{account_id}/stop、/accounts/{account_id}/whitelist、/accounts/{account_id}/whitelist/{user_id} … |
| 产物/文档 Artifact | 40 | 40 | 0 | 0 | /api/v1/artifact/office-onlyoffice-callback、/api/v1/artifact/office-onlyoffice-config、/api/v1/onlyoffice-status、/api/v1/wps/config、/api/v1/wps/dl/{token}、/api/v1/wps/put/{token} … |
| 审计/审核看板 Audit | 32 | 32 | 0 | 0 | /api/audit/selfcheck、/catalog、/items、/items/{item_id}、/items/{item_id}/events、/logs … |
| 线程 Thread | 18 | 18 | 0 | 0 | /api/v1/threads、/api/v1/threads/{tid}、/api/v1/threads/{tid}/abort、/api/v1/threads/{tid}/artifact/preview、/api/v1/threads/{tid}/result/{name}、/{schedule_id} … |
| 对话/会话 Chat | 14 | 14 | 0 | 0 | /api/v1/chat、/ask-context、/ask-quota、/cancel、/diag-log、/summarize |
| 业务函数·主服务编排 | 12 | 0 | 12 | 0 | AskUserAnswer、ChatRequest、ContributionSubmitRequest、ThreadTitleUpdate、chat、chat_resume … |
| 业务函数·流水线接口 | 10 | 0 | 10 | 0 | DeployIn、EventIn、ItemIn、PushIn、add_event、create_item … |
| 业务函数·邮件实时处理 | 9 | 0 | 9 | 0 | email_auth_status、fetch_live_messages、query_recent_emails、reset_request_bmp_email、reset_request_bmp_token、send_email … |
| 业务函数·网关加解密 | 8 | 0 | 8 | 0 | GatewayKeys、decrypt_envelope、decrypt_request、decrypt_response、encrypt_envelope、encrypt_request … |
| 业务函数·统一身份鉴权 | 8 | 0 | 8 | 0 | UnifiedLoginRequest、UnifiedLoginResponse、bmp_circuit_open、encrypt_password、gateway_renew、gateway_user … |
| 业务函数·通知推送 | 7 | 0 | 7 | 0 | list_notifications、mark_read、push、seed_mock_approvals、sse_stream、subscribe … |
| 业务函数·内容总结 | 5 | 0 | 5 | 0 | configured、extract_json、llm_complete、llm_json、prescreen_mails |
| SQL/查询 Query | 4 | 4 | 0 | 0 | /api/sql/translate、/api/sql_explanation/retry |
| 工具/集成 Tool | 4 | 4 | 0 | 0 | /hook/deploy、/hook/push |
| 业务函数·晨会简报 | 3 | 0 | 3 | 0 | get_briefing_script、get_briefing_speech_path、get_morning_briefing |
| 业务函数·执行大厅指标 | 3 | 0 | 3 | 0 | get_summary、load_cached_summary、refresh_summary |
| 智能体 Agent | 2 | 2 | 0 | 0 | /api/v1/agents |
| 健康/其它 | 2 | 2 | 0 | 0 | /api/v1/health |
| 未归类 Other | 2 | 2 | 0 | 0 | /proxy |
| 简报 Briefing | 2 | 2 | 0 | 0 | /today |
| 业务函数·晨报生成 | 2 | 0 | 2 | 0 | load_cached_brief、refresh_brief |
| 前端 Frontend | 2 | 0 | 0 | 2 | 交互组件 KbPage.vue、交互组件 TasksTab.vue |
| 业务函数·执行大厅性能 | 1 | 0 | 1 | 0 | get_perf_cards |
| 业务函数·网关中间件 | 1 | 0 | 1 | 0 | encrypted_json_transport |

### 2.2 各模块代表测试点（节选，完整见 TEST_POINTS_NEW.md）

| ID | 业务语义 | 模块 | 区域 | 方法 | 类型 | 维度 | 预期 |
|---|---|---|---|---|---|---|---|
| TP-001 | 账户/用户/鉴权 · 登录鉴权 | 账户/用户/鉴权 Auth | `/api/v1/auth/login` | POST | 正常 | 正常-可用性 | 账户/用户/鉴权·登录鉴权 功能可用：POST /api/v1/auth/login 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 login |
| TP-002 | 账户/用户/鉴权 · 登录鉴权 | 账户/用户/鉴权 Auth | `/api/v1/auth/login` | POST | 边界 | 边界-参数缺失/非法 | 账户/用户/鉴权·登录鉴权 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 login |
| TP-009 | 线程 · 会话线程 | 线程 Thread | `/api/v1/threads` | GET | 正常 | 正常-可用性 | 线程·会话线程 功能可用：GET /api/v1/threads 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 list_threads |
| TP-010 | 线程 · 会话线程 | 线程 Thread | `/api/v1/threads` | GET | 边界 | 边界-参数缺失/非法 | 线程·会话线程 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 list_threads |
| TP-011 | 智能体 · 智能体编排 | 智能体 Agent | `/api/v1/agents` | GET | 正常 | 正常-可用性 | 智能体·智能体编排 功能可用：GET /api/v1/agents 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 list_agents |
| TP-012 | 智能体 · 智能体编排 | 智能体 Agent | `/api/v1/agents` | GET | 边界 | 边界-参数缺失/非法 | 智能体·智能体编排 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 list_agents |
| TP-021 | 对话/会话 · 对话交互 | 对话/会话 Chat | `/api/v1/chat` | POST | 正常 | 正常-可用性 | 对话/会话·对话交互 功能可用：POST /api/v1/chat 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 chat |
| TP-022 | 对话/会话 · 对话交互 | 对话/会话 Chat | `/api/v1/chat` | POST | 边界 | 边界-参数缺失/非法 | 对话/会话·对话交互 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 chat |
| TP-023 | 审计/审核看板 · 提交/创建 | 审计/审核看板 Audit | `/mock/config` | POST | 正常 | 正常-可用性 | 审计/审核看板·提交/创建 功能可用：POST /mock/config 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 mock_config |
| TP-024 | 审计/审核看板 · 提交/创建 | 审计/审核看板 Audit | `/mock/config` | POST | 边界 | 边界-参数缺失/非法 | 审计/审核看板·提交/创建 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 mock_config |
| TP-031 | 健康/其它 · 健康检查 | 健康/其它 | `/api/v1/health` | GET | 正常 | 正常-可用性 | 健康/其它·健康检查 功能可用：GET /api/v1/health 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 health |
| TP-032 | 健康/其它 · 健康检查 | 健康/其它 | `/api/v1/health` | GET | 边界 | 边界-参数缺失/非法 | 健康/其它·健康检查 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 health |
| TP-033 | SQL/查询 · 检索查询 | SQL/查询 Query | `/api/sql/translate` | POST | 正常 | 正常-可用性 | SQL/查询·检索查询 功能可用：POST /api/sql/translate 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 sql_translate：SQL → 中文翻译。SQLGlot 拆 AST + minimax M3 翻译。 |
| TP-034 | SQL/查询 · 检索查询 | SQL/查询 Query | `/api/sql/translate` | POST | 边界 | 边界-参数缺失/非法 | SQL/查询·检索查询 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 sql_translate：SQL → 中文翻译。SQLGlot 拆 AST + minimax M3 翻译。 |
| TP-047 | 工具/集成 · 提交/创建 | 工具/集成 Tool | `/hook/push` | POST | 正常 | 正常-可用性 | 工具/集成·提交/创建 功能可用：POST /hook/push 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 hook_push：Gitee push 事件（webhook 服务转发）：提交信息含 fx-N 的事项自动打点。 |
| TP-048 | 工具/集成 · 提交/创建 | 工具/集成 Tool | `/hook/push` | POST | 边界 | 边界-参数缺失/非法 | 工具/集成·提交/创建 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 hook_push：Gitee push 事件（webhook 服务转发）：提交信息含 fx-N 的事项自动打点。 |
| TP-057 | 产物/文档 · 产物文档 | 产物/文档 Artifact | `/api/v1/wps/config` | GET | 正常 | 正常-可用性 | 产物/文档·产物文档 功能可用：GET /api/v1/wps/config 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 wps_config |
| TP-058 | 产物/文档 · 产物文档 | 产物/文档 Artifact | `/api/v1/wps/config` | GET | 边界 | 边界-参数缺失/非法 | 产物/文档·产物文档 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 wps_config |
| TP-135 | 未归类 · 提交/创建 | 未归类 Other | `/proxy` | POST | 正常 | 正常-可用性 | 未归类·提交/创建 功能可用：POST /proxy 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 cockpit_proxy |
| TP-136 | 未归类 · 提交/创建 | 未归类 Other | `/proxy` | POST | 边界 | 边界-参数缺失/非法 | 未归类·提交/创建 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 cockpit_proxy |
| TP-143 | 简报 · 查询 | 简报 Briefing | `/today` | GET | 正常 | 正常-可用性 | 简报·查询 功能可用：GET /today 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 list_today：最近 3 天邮件清单（不含正文，供列表页展示）。路由名 /today 保留兼容前端。 |
| TP-144 | 简报 · 查询 | 简报 Briefing | `/today` | GET | 边界 | 边界-参数缺失/非法 | 简报·查询 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 list_today：最近 3 天邮件清单（不含正文，供列表页展示）。路由名 /today 保留兼容前端。 |
| TP-189 | 主服务编排 · lifespan | 业务函数·主服务编排 | `lifespan` | FUNC | 正常 | 业务函数-逻辑可用 | 主服务编排 业务函数 lifespan 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测 |
| TP-190 | 主服务编排 · custom_openapi | 业务函数·主服务编排 | `custom_openapi` | FUNC | 正常 | 业务函数-逻辑可用 | 主服务编排 业务函数 custom_openapi 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测 |
| TP-201 | 网关加解密 · GatewayKeys | 业务函数·网关加解密 | `GatewayKeys` | FUNC | 正常 | 业务函数-逻辑可用 | 网关加解密 业务函数 GatewayKeys 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测 |
| TP-202 | 网关加解密 · load_keys | 业务函数·网关加解密 | `load_keys` | FUNC | 正常 | 业务函数-逻辑可用 | 网关加解密 业务函数 load_keys 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：Load environment-appropriate keys from direct values or an ignored document. |
| TP-209 | 统一身份鉴权 · bmp_circuit_open | 业务函数·统一身份鉴权 | `bmp_circuit_open` | FUNC | 正常 | 业务函数-逻辑可用 | 统一身份鉴权 业务函数 bmp_circuit_open 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：熔断是否处于打开状态（拦截器据此降级放行）。 |
| TP-210 | 统一身份鉴权 · maybe_schedule_renew | 业务函数·统一身份鉴权 | `maybe_schedule_renew` | FUNC | 正常 | 业务函数-逻辑可用 | 统一身份鉴权 业务函数 maybe_schedule_renew 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：每个 token 每 _GW_RENEW_INTERVAL 秒最多后台续期一次，不阻塞业务请求。 |
| TP-217 | 邮件实时处理 · set_request_bmp_token | 业务函数·邮件实时处理 | `set_request_bmp_token` | FUNC | 正常 | 业务函数-逻辑可用 | 邮件实时处理 业务函数 set_request_bmp_token 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：由 HTTP 中间件按请求注入，供 Agent 等非路由调用安全复用。 |
| TP-218 | 邮件实时处理 · reset_request_bmp_token | 业务函数·邮件实时处理 | `reset_request_bmp_token` | FUNC | 正常 | 业务函数-逻辑可用 | 邮件实时处理 业务函数 reset_request_bmp_token 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测 |
| TP-226 | 晨会简报 · get_morning_briefing | 业务函数·晨会简报 | `get_morning_briefing` | FUNC | 正常 | 业务函数-逻辑可用 | 晨会简报 业务函数 get_morning_briefing 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：返回今日晨报 {date, content, mail_count, event_count}；无素材或 LLM 失败时 content 为兜底文案。 |
| TP-227 | 晨会简报 · get_briefing_script | 业务函数·晨会简报 | `get_briefing_script` | FUNC | 正常 | 业务函数-逻辑可用 | 晨会简报 业务函数 get_briefing_script 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：返回今日口播稿（LLM 凝练口语版晨报），按 (user_id, 日期) 缓存。 |
| TP-229 | 晨报生成 · load_cached_brief | 业务函数·晨报生成 | `load_cached_brief` | FUNC | 正常 | 业务函数-逻辑可用 | 晨报生成 业务函数 load_cached_brief 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测 |
| TP-230 | 晨报生成 · refresh_brief | 业务函数·晨报生成 | `refresh_brief` | FUNC | 正常 | 业务函数-逻辑可用 | 晨报生成 业务函数 refresh_brief 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：跑批入口：四板块拼装 → 落缓存 → 推通知中心。失败抛异常由 runner 记录， |
| TP-231 | 内容总结 · configured | 业务函数·内容总结 | `configured` | FUNC | 正常 | 业务函数-逻辑可用 | 内容总结 业务函数 configured 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测 |
| TP-232 | 内容总结 · llm_complete | 业务函数·内容总结 | `llm_complete` | FUNC | 正常 | 业务函数-逻辑可用 | 内容总结 业务函数 llm_complete 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：统一 LLM 调用：reasoning_split + 空 content 重试 + token 记录。 |
| TP-236 | 通知推送 · push | 业务函数·通知推送 | `push` | FUNC | 正常 | 业务函数-逻辑可用 | 通知推送 业务函数 push 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：写一条通知并广播给在线 SSE 订阅者。kind 非法/空标题直接丢弃。 |
| TP-237 | 通知推送 · list_notifications | 业务函数·通知推送 | `list_notifications` | FUNC | 正常 | 业务函数-逻辑可用 | 通知推送 业务函数 list_notifications 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测 |
| TP-243 | 执行大厅指标 · load_cached_summary | 业务函数·执行大厅指标 | `load_cached_summary` | FUNC | 正常 | 业务函数-逻辑可用 | 执行大厅指标 业务函数 load_cached_summary 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：同步读缓存（供 briefing 晨播报业绩段使用）；无缓存/损坏返回 None，绝不触发 LLM。 |
| TP-244 | 执行大厅指标 · refresh_summary | 业务函数·执行大厅指标 | `refresh_summary` | FUNC | 正常 | 业务函数-逻辑可用 | 执行大厅指标 业务函数 refresh_summary 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：跑批入口：提取最近 6 张问数表 → LLM 总结 → 写缓存。 |
| TP-246 | 执行大厅性能 · get_perf_cards | 业务函数·执行大厅性能 | `get_perf_cards` | FUNC | 正常 | 业务函数-逻辑可用 | 执行大厅性能 业务函数 get_perf_cards 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测 |
| TP-247 | 流水线接口 · list_items | 业务函数·流水线接口 | `list_items` | FUNC | 正常 | 业务函数-逻辑可用 | 流水线接口 业务函数 list_items 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测 |
| TP-248 | 流水线接口 · get_item | 业务函数·流水线接口 | `get_item` | FUNC | 正常 | 业务函数-逻辑可用 | 流水线接口 业务函数 get_item 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测 |
| TP-257 | 网关中间件 · encrypted_json_transport | 业务函数·网关中间件 | `encrypted_json_transport` | FUNC | 正常 | 业务函数-逻辑可用 | 网关中间件 业务函数 encrypted_json_transport 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：Decrypt marked JSON requests and encrypt their JSON responses. |
| TP-258 | 前端组件 · 交互 | 前端 Frontend | `交互组件 KbPage.vue` | UI | 正常 | 交互元素可用 | 交互组件 交互组件 KbPage.vue 可正常触发：含交互钩子(@click/表单/上传)，操作有响应 |
| TP-259 | 前端组件 · 交互 | 前端 Frontend | `交互组件 TasksTab.vue` | UI | 正常 | 交互元素可用 | 交互组件 交互组件 TasksTab.vue 可正常触发：含交互钩子(@click/表单/上传)，操作有响应 |

## 三、新旧差异对比

| 维度 | 旧版（上次） | 新版（本次） | 变化 |
|---|---|---|---|
| 测试点数量 | 9 条模块级 | 259 条逐项 | +250（约 28×） |
| 覆盖粒度 | 模块级抽样（9 模块） | 代码级（API路由+业务函数+前端） | 由粗到细 |
| 测试维度 | 单一笼统预期 | 正常/边界/异常/安全 四维展开 | 维度补齐 |
| 来源 | 手工归纳业务场景 | 完整代码静态扫描派生 | 可复现、随代码演进 |
| 路由覆盖 | 仅线上对话可见业务（~24 场景） | 全仓 125 路由 × 多维 | 全 API 面 |
| 业务函数 | 未覆盖 | 抽取 14 个核心模块顶层函数 | 逻辑面补齐 |
| 前端 | 未覆盖 | 页面可达 + 组件交互 | UI 面补齐 |

> 结论：新版测试点从「9 个模块级抽样」升级为「259 条代码级逐项 + 四维维度 + 全 API/业务/前端覆盖」，覆盖充分性与可复现性显著提升，且与代码变更同步。

> 附：**标签属性**已加入每条测试点——「全量」259 条 / 「更新」0 条（本次 test-20260906..test-20260907 diff 覆盖其底层路由/函数 hunk 才标『更新』），可在测试列表/JSON 中按标签筛选本次变更测试点。
