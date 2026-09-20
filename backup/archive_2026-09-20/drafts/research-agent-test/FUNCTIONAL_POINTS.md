# 功能点清单（统一契约 v1.0 · A1 业务语义 + A2 双向追溯）

> 由 `code_analyzer` 单次扫描（C1 去重）产出：功能点与测试点**同源同一次 AST**，测试点通过 `fp_id` 指回功能点，功能点反查其派生测试点。

> 功能点总数 **165**；本轮范围内有派生测试点的功能点 **165**（覆盖率 100.0%）；派生测试点最多的功能点含 **2** 条测试点；孤儿测试点（无来源功能点）**0** 条。

> 说明：fp_without_tp>0 通常为 Scope 过滤导致（如本轮只要正常+异常，安全/边界维度的派生测试点被过滤），非追溯断链；tp_without_fp 应恒为 0，非 0 即契约缺陷。


## 功能点 → 测试点（双向追溯矩阵）

| # | fp_id | 类型 | 业务语义 | 功能点 | 文件 | 派生测试点 | 测试点 ID |
|---|---|---|---|---|---|---|---|
| 1 | `FP-3e755d06` | api | 账户/用户/鉴权 · 删除 | 账户/用户/鉴权 · 删除（DELETE /accounts/{account_id}） | `backend/research-agent-source/tools/wechat_channel/admin_api.py` | **2** | TP-173、TP-174 |
| 2 | `FP-ac92ea8d` | api | 账户/用户/鉴权 · 删除 | 账户/用户/鉴权 · 删除（DELETE /accounts/{account_id}/whitelist/{user_id}） | `backend/research-agent-source/tools/wechat_channel/admin_api.py` | **2** | TP-185、TP-186 |
| 3 | `FP-5bc8f455` | api | 账户/用户/鉴权 · 登录鉴权 | 账户/用户/鉴权 · 登录鉴权（DELETE /login/{session_key}） | `backend/research-agent-source/tools/wechat_channel/admin_api.py` | **2** | TP-169、TP-170 |
| 4 | `FP-2eaeabc3` | api | 账户/用户/鉴权 · 删除 | 账户/用户/鉴权 · 删除（DELETE /roles/{role_id}） | `backend/research-agent-source/tools/auth/rbac.py` | **2** | TP-119、TP-120 |
| 5 | `FP-49b47738` | api | 账户/用户/鉴权 · 删除 | 账户/用户/鉴权 · 删除（DELETE /users/{user_id}） | `backend/research-agent-source/tools/auth/admin_routes.py` | **2** | TP-107、TP-108 |
| 6 | `FP-5e173d23` | api | 线程 · 调度同步 | 线程 · 调度同步（DELETE /{schedule_id}） | `backend/research-agent-source/tools/scheduler/api.py` | **2** | TP-159、TP-160 |
| 7 | `FP-e7472679` | api | 账户/用户/鉴权 · 查询 | 账户/用户/鉴权 · 查询（GET /accounts） | `backend/research-agent-source/tools/wechat_channel/admin_api.py` | **2** | TP-171、TP-172 |
| 8 | `FP-d8ab6080` | api | 账户/用户/鉴权 · 查询 | 账户/用户/鉴权 · 查询（GET /accounts/{account_id}/whitelist） | `backend/research-agent-source/tools/wechat_channel/admin_api.py` | **2** | TP-181、TP-182 |
| 9 | `FP-156a8149` | api | 审计/审核看板 · 审批审核 | 审计/审核看板 · 审批审核（GET /api/audit/selfcheck） | `backend/research-agent-source/audit_pipeline.py` | **2** | TP-037、TP-038 |
| 10 | `FP-c79dd3d3` | api | 智能体 · 智能体编排 | 智能体 · 智能体编排（GET /api/v1/agents） | `frontend/mock-server/server.py` | **2** | TP-011、TP-012 |
| 11 | `FP-d0186c09` | api | 产物/文档 · 产物文档 | 产物/文档 · 产物文档（GET /api/v1/artifact/office-onlyoffice-config） | `backend/research-agent-source/tools/onlyoffice_bridge/routes.py` | **2** | TP-153、TP-154 |
| 12 | `FP-0cab29dd` | api | 账户/用户/鉴权 · 登录鉴权 | 账户/用户/鉴权 · 登录鉴权（GET /api/v1/auth/me） | `frontend/mock-server/server.py` | **2** | TP-007、TP-008 |
| 13 | `FP-85b27ee2` | api | 健康/其它 · 健康检查 | 健康/其它 · 健康检查（GET /api/v1/health） | `frontend/mock-server/server.py` | **2** | TP-031、TP-032 |
| 14 | `FP-179adbe5` | api | 产物/文档 · 健康检查 | 产物/文档 · 健康检查（GET /api/v1/onlyoffice-status） | `backend/research-agent-source/tools/onlyoffice_bridge/routes.py` | **2** | TP-151、TP-152 |
| 15 | `FP-b7cd0f90` | api | 线程 · 会话线程 | 线程 · 会话线程（GET /api/v1/threads） | `frontend/mock-server/server.py` | **2** | TP-009、TP-010 |
| 16 | `FP-d08046c2` | api | 线程 · 会话线程 | 线程 · 会话线程（GET /api/v1/threads/{tid}） | `frontend/mock-server/server.py` | **2** | TP-013、TP-014 |
| 17 | `FP-b65000bd` | api | 线程 · 审批审核 | 线程 · 审批审核（GET /api/v1/threads/{tid}/artifact/preview） | `frontend/mock-server/server.py` | **2** | TP-019、TP-020 |
| 18 | `FP-4f4c303d` | api | 线程 · 会话线程 | 线程 · 会话线程（GET /api/v1/threads/{tid}/result/{name}） | `frontend/mock-server/server.py` | **2** | TP-017、TP-018 |
| 19 | `FP-aa176e17` | api | 产物/文档 · 产物文档 | 产物/文档 · 产物文档（GET /api/v1/wps/config） | `backend/research-agent-source/wps_office_api.py` | **2** | TP-057、TP-058 |
| 20 | `FP-1babeffe` | api | 产物/文档 · 导出下载 | 产物/文档 · 导出下载（GET /api/v1/wps/dl/{token}） | `backend/research-agent-source/wps_office_api.py` | **2** | TP-065、TP-066 |
| 21 | `FP-b82f3b65` | api | 产物/文档 · 产物文档 | 产物/文档 · 产物文档（GET /api/v1/wps/v3/3rd/files/{file_id}） | `backend/research-agent-source/wps_office_api.py` | **2** | TP-061、TP-062 |
| 22 | `FP-0becabda` | api | 产物/文档 · 导出下载 | 产物/文档 · 导出下载（GET /api/v1/wps/v3/3rd/files/{file_id}/download） | `backend/research-agent-source/wps_office_api.py` | **2** | TP-063、TP-064 |
| 23 | `FP-e829009f` | api | 产物/文档 · 产物文档 | 产物/文档 · 产物文档（GET /api/v1/wps/v3/3rd/files/{file_id}/permission） | `backend/research-agent-source/wps_office_api.py` | **2** | TP-067、TP-068 |
| 24 | `FP-01ad8d5f` | api | 产物/文档 · 上传导入 | 产物/文档 · 上传导入（GET /api/v1/wps/v3/3rd/files/{file_id}/upload/prepare） | `backend/research-agent-source/wps_office_api.py` | **2** | TP-071、TP-072 |
| 25 | `FP-0ebac371` | api | 产物/文档 · 产物文档 | 产物/文档 · 产物文档（GET /api/v1/wps/v3/3rd/users） | `backend/research-agent-source/wps_office_api.py` | **2** | TP-069、TP-070 |
| 26 | `FP-bd8f759f` | api | 对话/会话 · 对话交互 | 对话/会话 · 对话交互（GET /ask-quota） | `backend/research-agent-source/tools/email_list/routes.py` | **2** | TP-147、TP-148 |
| 27 | `FP-3d7331e6` | api | 审计/审核看板 · 查询 | 审计/审核看板 · 查询（GET /catalog） | `backend/research-agent-source/tools/auth/rbac.py` | **2** | TP-111、TP-112 |
| 28 | `FP-d9dc1169` | api | 对话/会话 · 查询 | 对话/会话 · 查询（GET /diag-log） | `frontend/mock-server/server.py` | **2** | TP-029、TP-030 |
| 29 | `FP-942506ae` | api | 产物/文档 · 导出下载 | 产物/文档 · 导出下载（GET /dl/{short_id}） | `backend/research-agent-source/tools/wechat_channel/admin_api.py` | **2** | TP-187、TP-188 |
| 30 | `FP-c0ed59cb` | api | 产物/文档 · 产物文档 | 产物/文档 · 产物文档（GET /document） | `backend/research-agent-source/tools/audit_kb/api.py` | **2** | TP-079、TP-080 |
| 31 | `FP-720a39fc` | api | 产物/文档 · 产物文档 | 产物/文档 · 产物文档（GET /document_info） | `backend/research-agent-source/tools/audit_kb/api.py` | **2** | TP-081、TP-082 |
| 32 | `FP-695b8ad8` | api | 产物/文档 · 产物文档 | 产物/文档 · 产物文档（GET /documents） | `backend/research-agent-source/tools/audit_kb_admin/admin_api.py` | **2** | TP-093、TP-094 |
| 33 | `FP-e245cd13` | api | 产物/文档 · 产物文档 | 产物/文档 · 产物文档（GET /documents/{src_id}/content） | `backend/research-agent-source/tools/audit_kb_admin/admin_api.py` | **2** | TP-095、TP-096 |
| 34 | `FP-326f35f8` | api | 产物/文档 · 产物文档 | 产物/文档 · 产物文档（GET /documents/{src_id}/diff） | `backend/research-agent-source/tools/audit_kb_admin/admin_api.py` | **2** | TP-097、TP-098 |
| 35 | `FP-cccee0b8` | api | 审计/审核看板 · 查询 | 审计/审核看板 · 查询（GET /items） | `backend/research-agent-source/pipeline_api.py` | **2** | TP-039、TP-040 |
| 36 | `FP-b1df251b` | api | 审计/审核看板 · 查询 | 审计/审核看板 · 查询（GET /items/{item_id}） | `backend/research-agent-source/pipeline_api.py` | **2** | TP-041、TP-042 |
| 37 | `FP-e14195fe` | api | 账户/用户/鉴权 · 登录鉴权 | 账户/用户/鉴权 · 登录鉴权（GET /login/{session_key}） | `backend/research-agent-source/tools/wechat_channel/admin_api.py` | **2** | TP-167、TP-168 |
| 38 | `FP-ad480b34` | api | 审计/审核看板 · 查询 | 审计/审核看板 · 查询（GET /logs） | `backend/research-agent-source/tools/audit_kb_admin/admin_api.py` | **2** | TP-099、TP-100 |
| 39 | `FP-56627f76` | api | 账户/用户/鉴权 · 查询 | 账户/用户/鉴权 · 查询（GET /me） | `backend/research-agent-source/tools/auth/rbac.py` | **2** | TP-109、TP-110 |
| 40 | `FP-af977b94` | api | 账户/用户/鉴权 · 查询 | 账户/用户/鉴权 · 查询（GET /me） | `backend/research-agent-source/tools/auth/routes.py` | **2** | TP-131、TP-132 |
| 41 | `FP-2874864c` | api | 审计/审核看板 · 查询 | 审计/审核看板 · 查询（GET /mock/state） | `frontend/mock-server/server.py` | **2** | TP-025、TP-026 |
| 42 | `FP-df3b362f` | api | 审计/审核看板 · 审批审核 | 审计/审核看板 · 审批审核（GET /pending） | `backend/research-agent-source/tools/audit_kb_admin/admin_api.py` | **2** | TP-087、TP-088 |
| 43 | `FP-99cc9204` | api | 审计/审核看板 · 审批审核 | 审计/审核看板 · 审批审核（GET /pending/count） | `backend/research-agent-source/tools/audit_kb_admin/admin_api.py` | **2** | TP-085、TP-086 |
| 44 | `FP-6b26c560` | api | 审计/审核看板 · 检索查询 | 审计/审核看板 · 检索查询（GET /regulations/search） | `backend/research-agent-source/tools/audit_kb/api.py` | **2** | TP-083、TP-084 |
| 45 | `FP-d4811a98` | api | 账户/用户/鉴权 · 查询 | 账户/用户/鉴权 · 查询（GET /roles） | `backend/research-agent-source/tools/auth/rbac.py` | **2** | TP-113、TP-114 |
| 46 | `FP-e79dfaa6` | api | 审计/审核看板 · 健康检查 | 审计/审核看板 · 健康检查（GET /status） | `backend/research-agent-source/tools/wechat_channel/admin_api.py` | **2** | TP-179、TP-180 |
| 47 | `FP-ab3827f0` | api | 简报 · 查询 | 简报 · 查询（GET /today） | `backend/research-agent-source/tools/email_list/routes.py` | **2** | TP-143、TP-144 |
| 48 | `FP-0ac402e0` | api | 账户/用户/鉴权 · 查询 | 账户/用户/鉴权 · 查询（GET /users） | `backend/research-agent-source/tools/auth/admin_routes.py` | **2** | TP-103、TP-104 |
| 49 | `FP-0ae4b797` | api | 账户/用户/鉴权 · 查询 | 账户/用户/鉴权 · 查询（GET /users） | `backend/research-agent-source/tools/auth/rbac.py` | **2** | TP-121、TP-122 |
| 50 | `FP-78327682` | api | 账户/用户/鉴权 · 部分更新 | 账户/用户/鉴权 · 部分更新（PATCH /users/{user_id}） | `backend/research-agent-source/tools/auth/admin_routes.py` | **2** | TP-105、TP-106 |
| 51 | `FP-df4e1244` | api | 账户/用户/鉴权 · 提交/创建 | 账户/用户/鉴权 · 提交/创建（POST /accounts/{account_id}/start） | `backend/research-agent-source/tools/wechat_channel/admin_api.py` | **2** | TP-175、TP-176 |
| 52 | `FP-6b3b1099` | api | 账户/用户/鉴权 · 取消中止 | 账户/用户/鉴权 · 取消中止（POST /accounts/{account_id}/stop） | `backend/research-agent-source/tools/wechat_channel/admin_api.py` | **2** | TP-177、TP-178 |
| 53 | `FP-3ce048fe` | api | 账户/用户/鉴权 · 提交/创建 | 账户/用户/鉴权 · 提交/创建（POST /accounts/{account_id}/whitelist） | `backend/research-agent-source/tools/wechat_channel/admin_api.py` | **2** | TP-183、TP-184 |
| 54 | `FP-aa2d2477` | api | SQL/查询 · 检索查询 | SQL/查询 · 检索查询（POST /api/sql/translate） | `backend/research-agent-source/audit_pipeline.py` | **2** | TP-033、TP-034 |
| 55 | `FP-2b43392b` | api | SQL/查询 · 检索查询 | SQL/查询 · 检索查询（POST /api/sql_explanation/retry） | `backend/research-agent-source/audit_pipeline.py` | **2** | TP-035、TP-036 |
| 56 | `FP-ea62955c` | api | 产物/文档 · 产物文档 | 产物/文档 · 产物文档（POST /api/v1/artifact/office-onlyoffice-callback） | `backend/research-agent-source/tools/onlyoffice_bridge/routes.py` | **2** | TP-155、TP-156 |
| 57 | `FP-91b068ac` | api | 账户/用户/鉴权 · 登录鉴权 | 账户/用户/鉴权 · 登录鉴权（POST /api/v1/auth/login） | `frontend/mock-server/server.py` | **2** | TP-001、TP-002 |
| 58 | `FP-fcc8d684` | api | 账户/用户/鉴权 · 登录鉴权 | 账户/用户/鉴权 · 登录鉴权（POST /api/v1/auth/logout） | `frontend/mock-server/server.py` | **2** | TP-005、TP-006 |
| 59 | `FP-57704045` | api | 账户/用户/鉴权 · 登录鉴权 | 账户/用户/鉴权 · 登录鉴权（POST /api/v1/auth/refresh） | `frontend/mock-server/server.py` | **2** | TP-003、TP-004 |
| 60 | `FP-56d862c1` | api | 对话/会话 · 对话交互 | 对话/会话 · 对话交互（POST /api/v1/chat） | `frontend/mock-server/server.py` | **2** | TP-021、TP-022 |
| 61 | `FP-f6cd93f4` | api | 线程 · 取消中止 | 线程 · 取消中止（POST /api/v1/threads/{tid}/abort） | `frontend/mock-server/server.py` | **2** | TP-015、TP-016 |
| 62 | `FP-f9891eb6` | api | 产物/文档 · 产物文档 | 产物/文档 · 产物文档（POST /api/v1/wps/register） | `backend/research-agent-source/wps_office_api.py` | **2** | TP-059、TP-060 |
| 63 | `FP-df341d15` | api | 产物/文档 · 上传导入 | 产物/文档 · 上传导入（POST /api/v1/wps/v3/3rd/files/{file_id}/upload/address） | `backend/research-agent-source/wps_office_api.py` | **2** | TP-073、TP-074 |
| 64 | `FP-74397962` | api | 产物/文档 · 上传导入 | 产物/文档 · 上传导入（POST /api/v1/wps/v3/3rd/files/{file_id}/upload/complete） | `backend/research-agent-source/wps_office_api.py` | **2** | TP-077、TP-078 |
| 65 | `FP-f3750201` | api | 对话/会话 · 对话交互 | 对话/会话 · 对话交互（POST /ask-context） | `backend/research-agent-source/tools/email_list/routes.py` | **2** | TP-149、TP-150 |
| 66 | `FP-d1cb1963` | api | 账户/用户/鉴权 · 登录鉴权 | 账户/用户/鉴权 · 登录鉴权（POST /authorize） | `backend/research-agent-source/tools/email_auth/routes.py` | **2** | TP-139、TP-140 |
| 67 | `FP-23b49b51` | api | 对话/会话 · 取消中止 | 对话/会话 · 取消中止（POST /cancel） | `backend/research-agent-source/tools/email_auth/routes.py` | **2** | TP-141、TP-142 |
| 68 | `FP-1e11d8a6` | api | 账户/用户/鉴权 · 登录鉴权 | 账户/用户/鉴权 · 登录鉴权（POST /change-password） | `backend/research-agent-source/tools/auth/routes.py` | **2** | TP-133、TP-134 |
| 69 | `FP-f74dac84` | api | 对话/会话 · 提交/创建 | 对话/会话 · 提交/创建（POST /diag-log） | `frontend/mock-server/server.py` | **2** | TP-027、TP-028 |
| 70 | `FP-8a27aa92` | api | 账户/用户/鉴权 · 登录鉴权 | 账户/用户/鉴权 · 登录鉴权（POST /gateway-renew） | `backend/research-agent-source/unified_auth.py` | **2** | TP-055、TP-056 |
| 71 | `FP-b0656585` | api | 账户/用户/鉴权 · 提交/创建 | 账户/用户/鉴权 · 提交/创建（POST /gateway-user） | `backend/research-agent-source/unified_auth.py` | **2** | TP-053、TP-054 |
| 72 | `FP-105993e2` | api | 工具/集成 · 提交/创建 | 工具/集成 · 提交/创建（POST /hook/deploy） | `backend/research-agent-source/pipeline_api.py` | **2** | TP-049、TP-050 |
| 73 | `FP-84bfda66` | api | 工具/集成 · 提交/创建 | 工具/集成 · 提交/创建（POST /hook/push） | `backend/research-agent-source/pipeline_api.py` | **2** | TP-047、TP-048 |
| 74 | `FP-4eccde88` | api | 审计/审核看板 · 提交/创建 | 审计/审核看板 · 提交/创建（POST /items） | `backend/research-agent-source/pipeline_api.py` | **2** | TP-043、TP-044 |
| 75 | `FP-b28a44f4` | api | 审计/审核看板 · 提交/创建 | 审计/审核看板 · 提交/创建（POST /items/{item_id}/events） | `backend/research-agent-source/pipeline_api.py` | **2** | TP-045、TP-046 |
| 76 | `FP-81ad1b1d` | api | 账户/用户/鉴权 · 登录鉴权 | 账户/用户/鉴权 · 登录鉴权（POST /login） | `backend/research-agent-source/tools/auth/routes.py` | **2** | TP-125、TP-126 |
| 77 | `FP-ecb687b5` | api | 账户/用户/鉴权 · 登录鉴权 | 账户/用户/鉴权 · 登录鉴权（POST /login/start） | `backend/research-agent-source/tools/wechat_channel/admin_api.py` | **2** | TP-165、TP-166 |
| 78 | `FP-d6e94f1e` | api | 账户/用户/鉴权 · 登录鉴权 | 账户/用户/鉴权 · 登录鉴权（POST /logout） | `backend/research-agent-source/tools/auth/routes.py` | **2** | TP-129、TP-130 |
| 79 | `FP-0e12e38e` | api | 审计/审核看板 · 提交/创建 | 审计/审核看板 · 提交/创建（POST /mock/config） | `frontend/mock-server/server.py` | **2** | TP-023、TP-024 |
| 80 | `FP-13621e82` | api | 审计/审核看板 · 审批审核 | 审计/审核看板 · 审批审核（POST /pending/{task_id}/confirm） | `backend/research-agent-source/tools/audit_kb_admin/admin_api.py` | **2** | TP-089、TP-090 |
| 81 | `FP-a63a8123` | api | 审计/审核看板 · 审批审核 | 审计/审核看板 · 审批审核（POST /pending/{task_id}/dismiss） | `backend/research-agent-source/tools/audit_kb_admin/admin_api.py` | **2** | TP-091、TP-092 |
| 82 | `FP-f937ddbc` | api | 未归类 · 提交/创建 | 未归类 · 提交/创建（POST /proxy） | `backend/research-agent-source/tools/cockpit/api.py` | **2** | TP-135、TP-136 |
| 83 | `FP-e6187b9d` | api | 账户/用户/鉴权 · 提交/创建 | 账户/用户/鉴权 · 提交/创建（POST /refresh） | `backend/research-agent-source/tools/auth/routes.py` | **2** | TP-127、TP-128 |
| 84 | `FP-1cdb3157` | api | 账户/用户/鉴权 · 提交/创建 | 账户/用户/鉴权 · 提交/创建（POST /roles） | `backend/research-agent-source/tools/auth/rbac.py` | **2** | TP-115、TP-116 |
| 85 | `FP-50731db7` | api | 审计/审核看板 · 健康检查 | 审计/审核看板 · 健康检查（POST /status） | `backend/research-agent-source/tools/email_auth/routes.py` | **2** | TP-137、TP-138 |
| 86 | `FP-ccc7212b` | api | 对话/会话 · 总结简报 | 对话/会话 · 总结简报（POST /summarize） | `backend/research-agent-source/tools/email_list/routes.py` | **2** | TP-145、TP-146 |
| 87 | `FP-e75c7259` | api | 账户/用户/鉴权 · 登录鉴权 | 账户/用户/鉴权 · 登录鉴权（POST /unified-login） | `backend/research-agent-source/unified_auth.py` | **2** | TP-051、TP-052 |
| 88 | `FP-560839ff` | api | 账户/用户/鉴权 · 提交/创建 | 账户/用户/鉴权 · 提交/创建（POST /users） | `backend/research-agent-source/tools/auth/admin_routes.py` | **2** | TP-101、TP-102 |
| 89 | `FP-59d19239` | api | 线程 · 调度同步 | 线程 · 调度同步（POST /{schedule_id}/run） | `backend/research-agent-source/tools/scheduler/api.py` | **2** | TP-161、TP-162 |
| 90 | `FP-2405813e` | api | 线程 · 调度同步 | 线程 · 调度同步（POST /{schedule_id}/toggle） | `backend/research-agent-source/tools/scheduler/api.py` | **2** | TP-163、TP-164 |
| 91 | `FP-39969e96` | api | 产物/文档 · 登录鉴权 | 产物/文档 · 登录鉴权（PUT /api/v1/wps/put/{token}） | `backend/research-agent-source/wps_office_api.py` | **2** | TP-075、TP-076 |
| 92 | `FP-194b0998` | api | 账户/用户/鉴权 · 更新 | 账户/用户/鉴权 · 更新（PUT /roles/{role_id}） | `backend/research-agent-source/tools/auth/rbac.py` | **2** | TP-117、TP-118 |
| 93 | `FP-d38ecd31` | api | 账户/用户/鉴权 · 更新 | 账户/用户/鉴权 · 更新（PUT /users/{user_id}/role） | `backend/research-agent-source/tools/auth/rbac.py` | **2** | TP-123、TP-124 |
| 94 | `FP-6ba2cb9b` | api | 线程 · 调度同步 | 线程 · 调度同步（PUT /{schedule_id}） | `backend/research-agent-source/tools/scheduler/api.py` | **2** | TP-157、TP-158 |
| 95 | `FP-275038d0` | business | 晨会简报 · get_briefing_script | 晨会简报 · get_briefing_script（返回今日口播稿（LLM 凝练口语版晨报），按 (user_id, 日期) 缓存。） | `backend/research-agent-source/briefing.py` | **1** | TP-227 |
| 96 | `FP-fcce7548` | business | 晨会简报 · get_briefing_speech_path | 晨会简报 · get_briefing_speech_path（返回今日晨报语音 mp3 的本地路径；命中缓存直接给，否则 edge-tts 现合成。） | `backend/research-agent-source/briefing.py` | **1** | TP-228 |
| 97 | `FP-5d95d8dc` | business | 晨会简报 · get_morning_briefing | 晨会简报 · get_morning_briefing（返回今日晨报 {date, content, mail_count, event_count}；无素材或 LLM 失败时 content 为兜底文案。） | `backend/research-agent-source/briefing.py` | **1** | TP-226 |
| 98 | `FP-7b5835db` | business | 邮件实时处理 · email_auth_status | 邮件实时处理 · email_auth_status（查询当前监控邮箱（EMAIL_ACCOUNT）的授权状态；失败返回 None。） | `backend/research-agent-source/email_live.py` | **1** | TP-222 |
| 99 | `FP-7056cab4` | business | 邮件实时处理 · fetch_live_messages | 邮件实时处理 · fetch_live_messages（查询邮件网关，返回 (实时消息卡片列表, 是否实时成功)。） | `backend/research-agent-source/email_live.py` | **1** | TP-221 |
| 100 | `FP-a91b1807` | business | 邮件实时处理 · query_recent_emails | 邮件实时处理 · query_recent_emails（同步查询最近收件（供 agent 工具调用）。） | `backend/research-agent-source/email_live.py` | **1** | TP-223 |
| 101 | `FP-54153a9d` | business | 邮件实时处理 · reset_request_bmp_email | 邮件实时处理 · reset_request_bmp_email | `backend/research-agent-source/email_live.py` | **1** | TP-220 |
| 102 | `FP-7ccf200a` | business | 邮件实时处理 · reset_request_bmp_token | 邮件实时处理 · reset_request_bmp_token | `backend/research-agent-source/email_live.py` | **1** | TP-218 |
| 103 | `FP-30af09ba` | business | 邮件实时处理 · send_email | 邮件实时处理 · send_email（调网关 /sendemail 发邮件（测试环境收发同邮箱）。返回解密后的 {code,msg,data}。） | `backend/research-agent-source/email_live.py` | **1** | TP-225 |
| 104 | `FP-d6c97513` | business | 邮件实时处理 · send_email_sync | 邮件实时处理 · send_email_sync（同步发信（2026-08-16 回复闭环：供 agent 工具 email_send 在线程池调用）。） | `backend/research-agent-source/email_live.py` | **1** | TP-224 |
| 105 | `FP-e24bb671` | business | 邮件实时处理 · set_request_bmp_email | 邮件实时处理 · set_request_bmp_email | `backend/research-agent-source/email_live.py` | **1** | TP-219 |
| 106 | `FP-3a6caacb` | business | 邮件实时处理 · set_request_bmp_token | 邮件实时处理 · set_request_bmp_token（由 HTTP 中间件按请求注入，供 Agent 等非路由调用安全复用。） | `backend/research-agent-source/email_live.py` | **1** | TP-217 |
| 107 | `FP-41eb06e5` | business | 执行大厅指标 · get_summary | 执行大厅指标 · get_summary（读缓存；不存在则同步生成一次（首次访问兜底），生成失败返回 empty 态不 500。） | `backend/research-agent-source/exec_hall_metrics.py` | **1** | TP-245 |
| 108 | `FP-cb42e7b5` | business | 执行大厅指标 · load_cached_summary | 执行大厅指标 · load_cached_summary（同步读缓存（供 briefing 晨播报业绩段使用）；无缓存/损坏返回 None，绝不触发 LLM。） | `backend/research-agent-source/exec_hall_metrics.py` | **1** | TP-243 |
| 109 | `FP-17099bca` | business | 执行大厅指标 · refresh_summary | 执行大厅指标 · refresh_summary（跑批入口：提取最近 6 张问数表 → LLM 总结 → 写缓存。） | `backend/research-agent-source/exec_hall_metrics.py` | **1** | TP-244 |
| 110 | `FP-d7bc79f1` | business | 执行大厅性能 · get_perf_cards | 执行大厅性能 · get_perf_cards | `backend/research-agent-source/exec_hall_perf.py` | **1** | TP-246 |
| 111 | `FP-fbca58e2` | business | 网关加解密 · GatewayKeys | 网关加解密 · GatewayKeys | `backend/research-agent-source/gateway_crypto.py` | **1** | TP-201 |
| 112 | `FP-feb19f38` | business | 网关加解密 · decrypt_envelope | 网关加解密 · decrypt_envelope | `backend/research-agent-source/gateway_crypto.py` | **1** | TP-204 |
| 113 | `FP-b0582dfc` | business | 网关加解密 · decrypt_request | 网关加解密 · decrypt_request | `backend/research-agent-source/gateway_crypto.py` | **1** | TP-206 |
| 114 | `FP-a90bfa32` | business | 网关加解密 · decrypt_response | 网关加解密 · decrypt_response | `backend/research-agent-source/gateway_crypto.py` | **1** | TP-208 |
| 115 | `FP-29375b78` | business | 网关加解密 · encrypt_envelope | 网关加解密 · encrypt_envelope | `backend/research-agent-source/gateway_crypto.py` | **1** | TP-203 |
| 116 | `FP-20efd2f7` | business | 网关加解密 · encrypt_request | 网关加解密 · encrypt_request | `backend/research-agent-source/gateway_crypto.py` | **1** | TP-205 |
| 117 | `FP-19b676e2` | business | 网关加解密 · encrypt_response | 网关加解密 · encrypt_response | `backend/research-agent-source/gateway_crypto.py` | **1** | TP-207 |
| 118 | `FP-1253053c` | business | 网关加解密 · load_keys | 网关加解密 · load_keys（Load environment-appropriate keys from direct values or an ignored document.） | `backend/research-agent-source/gateway_crypto.py` | **1** | TP-202 |
| 119 | `FP-23d6f2ec` | business | 网关中间件 · encrypted_json_transport | 网关中间件 · encrypted_json_transport（Decrypt marked JSON requests and encrypt their JSON responses.） | `backend/research-agent-source/gateway_middleware.py` | **1** | TP-257 |
| 120 | `FP-de88860b` | business | 晨报生成 · load_cached_brief | 晨报生成 · load_cached_brief | `backend/research-agent-source/morning_brief.py` | **1** | TP-229 |
| 121 | `FP-24321c84` | business | 晨报生成 · refresh_brief | 晨报生成 · refresh_brief（跑批入口：四板块拼装 → 落缓存 → 推通知中心。失败抛异常由 runner 记录，） | `backend/research-agent-source/morning_brief.py` | **1** | TP-230 |
| 122 | `FP-bfa3e724` | business | 通知推送 · list_notifications | 通知推送 · list_notifications | `backend/research-agent-source/notifications.py` | **1** | TP-237 |
| 123 | `FP-c99c6fa7` | business | 通知推送 · mark_read | 通知推送 · mark_read | `backend/research-agent-source/notifications.py` | **1** | TP-238 |
| 124 | `FP-73ae207d` | business | 通知推送 · push | 通知推送 · push（写一条通知并广播给在线 SSE 订阅者。kind 非法/空标题直接丢弃。） | `backend/research-agent-source/notifications.py` | **1** | TP-236 |
| 125 | `FP-cb8cfd04` | business | 通知推送 · seed_mock_approvals | 通知推送 · seed_mock_approvals | `backend/research-agent-source/notifications.py` | **1** | TP-239 |
| 126 | `FP-58d0010f` | business | 通知推送 · sse_stream | 通知推送 · sse_stream（SSE 事件流：先发一条 hello（含当前未读数），之后推新通知；25s 心跳。） | `backend/research-agent-source/notifications.py` | **1** | TP-242 |
| 127 | `FP-875f823a` | business | 通知推送 · subscribe | 通知推送 · subscribe | `backend/research-agent-source/notifications.py` | **1** | TP-240 |
| 128 | `FP-4ec2a506` | business | 通知推送 · unsubscribe | 通知推送 · unsubscribe | `backend/research-agent-source/notifications.py` | **1** | TP-241 |
| 129 | `FP-4e15f183` | business | 流水线接口 · DeployIn | 流水线接口 · DeployIn | `backend/research-agent-source/pipeline_api.py` | **1** | TP-255 |
| 130 | `FP-7f61d088` | business | 流水线接口 · EventIn | 流水线接口 · EventIn | `backend/research-agent-source/pipeline_api.py` | **1** | TP-251 |
| 131 | `FP-64261c69` | business | 流水线接口 · ItemIn | 流水线接口 · ItemIn | `backend/research-agent-source/pipeline_api.py` | **1** | TP-249 |
| 132 | `FP-3950d0f7` | business | 流水线接口 · PushIn | 流水线接口 · PushIn | `backend/research-agent-source/pipeline_api.py` | **1** | TP-253 |
| 133 | `FP-3897f240` | business | 流水线接口 · add_event | 流水线接口 · add_event | `backend/research-agent-source/pipeline_api.py` | **1** | TP-252 |
| 134 | `FP-d715c4cd` | business | 流水线接口 · create_item | 流水线接口 · create_item | `backend/research-agent-source/pipeline_api.py` | **1** | TP-250 |
| 135 | `FP-46d9f674` | business | 流水线接口 · get_item | 流水线接口 · get_item | `backend/research-agent-source/pipeline_api.py` | **1** | TP-248 |
| 136 | `FP-6e3c69f3` | business | 流水线接口 · hook_deploy | 流水线接口 · hook_deploy（部署完成回调：点亮⑦合并发布（若未绿）。线上验证(⑧)由冒烟脚本另行回写。） | `backend/research-agent-source/pipeline_api.py` | **1** | TP-256 |
| 137 | `FP-b3a039fc` | business | 流水线接口 · hook_push | 流水线接口 · hook_push（Gitee push 事件（webhook 服务转发）：提交信息含 fx-N 的事项自动打点。） | `backend/research-agent-source/pipeline_api.py` | **1** | TP-254 |
| 138 | `FP-7be8b6ff` | business | 流水线接口 · list_items | 流水线接口 · list_items | `backend/research-agent-source/pipeline_api.py` | **1** | TP-247 |
| 139 | `FP-9b90f748` | business | 主服务编排 · AskUserAnswer | 主服务编排 · AskUserAnswer（前端提交 ask_user 问题的回答。） | `backend/research-agent-source/server.py` | **1** | TP-192 |
| 140 | `FP-ff3be445` | business | 主服务编排 · ChatRequest | 主服务编排 · ChatRequest | `backend/research-agent-source/server.py` | **1** | TP-191 |
| 141 | `FP-59abdc46` | business | 主服务编排 · ContributionSubmitRequest | 主服务编排 · ContributionSubmitRequest | `backend/research-agent-source/server.py` | **1** | TP-194 |
| 142 | `FP-e2c254cf` | business | 主服务编排 · ThreadTitleUpdate | 主服务编排 · ThreadTitleUpdate（前端提交会话重命名请求：title 为空字符串视为取消（保留原值）。） | `backend/research-agent-source/server.py` | **1** | TP-193 |
| 143 | `FP-dd92b00d` | business | 主服务编排 · chat | 主服务编排 · chat（启动 chat 流(P3 解耦后)。） | `backend/research-agent-source/server.py` | **1** | TP-196 |
| 144 | `FP-3297b4ae` | business | 主服务编排 · chat_resume | 主服务编排 · chat_resume（接收 ask_user 问题的用户回答，用 `Command(resume=...)` 恢复 agent。） | `backend/research-agent-source/server.py` | **1** | TP-197 |
| 145 | `FP-90a2c8fb` | business | 主服务编排 · custom_openapi | 主服务编排 · custom_openapi | `backend/research-agent-source/server.py` | **1** | TP-190 |
| 146 | `FP-8082ec57` | business | 主服务编排 · diag_log | 主服务编排 · diag_log（前端真机诊断遥测落盘（2026-09-04 卢总 iPhone standalone 视口问题定位用）。） | `backend/research-agent-source/server.py` | **1** | TP-199 |
| 147 | `FP-de585591` | business | 主服务编排 · issue_raw_ticket | 主服务编排 · issue_raw_ticket（签发一次性 raw 访问 ticket(给 <iframe> / <img> / <a> 等浏览器被动请求使用)。） | `backend/research-agent-source/server.py` | **1** | TP-195 |
| 148 | `FP-4c048ef0` | business | 主服务编排 · lifespan | 主服务编排 · lifespan | `backend/research-agent-source/server.py` | **1** | TP-189 |
| 149 | `FP-666a8e13` | business | 主服务编排 · ops_active_runs | 主服务编排 · ops_active_runs（CI 部署探活：仅允许本机调用，返回活跃 run 数（免鉴权，部署脚本在停后端前轮询）。） | `backend/research-agent-source/server.py` | **1** | TP-200 |
| 150 | `FP-6c086a57` | business | 主服务编排 · stream_chat_events | 主服务编排 · stream_chat_events（SSE 端点：订阅某 thread 正在运行的 chat 事件流(P3 解耦后的 consumer)。） | `backend/research-agent-source/server.py` | **1** | TP-198 |
| 151 | `FP-f81005a1` | business | 内容总结 · configured | 内容总结 · configured | `backend/research-agent-source/summarizer.py` | **1** | TP-231 |
| 152 | `FP-681e2bcc` | business | 内容总结 · extract_json | 内容总结 · extract_json（从模型输出里抠出 JSON 对象（容错：代码围栏 / 前后杂质）。） | `backend/research-agent-source/summarizer.py` | **1** | TP-233 |
| 153 | `FP-921ab091` | business | 内容总结 · llm_complete | 内容总结 · llm_complete（统一 LLM 调用：reasoning_split + 空 content 重试 + token 记录。） | `backend/research-agent-source/summarizer.py` | **1** | TP-232 |
| 154 | `FP-f9a8dc6c` | business | 内容总结 · llm_json | 内容总结 · llm_json（LLM 调用并要求输出 JSON；解析失败/空结果重试，彻底失败返回 None。） | `backend/research-agent-source/summarizer.py` | **1** | TP-234 |
| 155 | `FP-c1692b1a` | business | 内容总结 · prescreen_mails | 内容总结 · prescreen_mails（元数据初筛：返回选中邮件的下标。失败/未配置时退化为前 keep 封（时间序）。） | `backend/research-agent-source/summarizer.py` | **1** | TP-235 |
| 156 | `FP-8648eecc` | business | 统一身份鉴权 · UnifiedLoginRequest | 统一身份鉴权 · UnifiedLoginRequest | `backend/research-agent-source/unified_auth.py` | **1** | TP-212 |
| 157 | `FP-62b103cb` | business | 统一身份鉴权 · UnifiedLoginResponse | 统一身份鉴权 · UnifiedLoginResponse | `backend/research-agent-source/unified_auth.py` | **1** | TP-213 |
| 158 | `FP-8d82c1df` | business | 统一身份鉴权 · bmp_circuit_open | 统一身份鉴权 · bmp_circuit_open（熔断是否处于打开状态（拦截器据此降级放行）。） | `backend/research-agent-source/unified_auth.py` | **1** | TP-209 |
| 159 | `FP-4ffa87ca` | business | 统一身份鉴权 · encrypt_password | 统一身份鉴权 · encrypt_password（AES-128-ECB/PKCS5 加密并 Base64，与统一登录侧 EncryptUtils.encryptByAes 一致。） | `backend/research-agent-source/unified_auth.py` | **1** | TP-211 |
| 160 | `FP-6c3f37dc` | business | 统一身份鉴权 · gateway_renew | 统一身份鉴权 · gateway_renew（调用文档第三个接口：在 token 有效时续期。） | `backend/research-agent-source/unified_auth.py` | **1** | TP-216 |
| 161 | `FP-add46bf0` | business | 统一身份鉴权 · gateway_user | 统一身份鉴权 · gateway_user（调用文档第二个接口：校验 BMP token，并返回 token 对应邮箱。） | `backend/research-agent-source/unified_auth.py` | **1** | TP-215 |
| 162 | `FP-29d4de44` | business | 统一身份鉴权 · maybe_schedule_renew | 统一身份鉴权 · maybe_schedule_renew（每个 token 每 _GW_RENEW_INTERVAL 秒最多后台续期一次，不阻塞业务请求。） | `backend/research-agent-source/unified_auth.py` | **1** | TP-210 |
| 163 | `FP-a09e2fb2` | business | 统一身份鉴权 · unified_login | 统一身份鉴权 · unified_login（统一身份登录：校验太平统一登录 → upsert 本地用户 → 签发平台 JWT。） | `backend/research-agent-source/unified_auth.py` | **1** | TP-214 |
| 164 | `FP-f4e4bde3` | component | 前端组件 · 交互触发 | 前端组件 · 交互触发（交互组件 KbPage.vue） | `backend/research-agent-source/audit_ui/src/components/KbPage.vue` | **1** | TP-258 |
| 165 | `FP-76a78799` | component | 前端组件 · 交互触发 | 前端组件 · 交互触发（交互组件 TasksTab.vue） | `backend/research-agent-source/audit_ui/src/components/TasksTab.vue` | **1** | TP-259 |