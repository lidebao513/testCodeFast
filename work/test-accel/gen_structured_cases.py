"""
基于 research-agent 真实源码推断功能与预期结果，生成结构化测试用例。

产出：
  - work/research-agent-test/structured_cases.json   （机读，可被 test-accel 消费）
  - work/test-accel/结构化测试用例_含预期结果.html     （可读报告，含模块功能推断 + 测试边界 + 用例表）

预期结果一律来自源码（装饰器 / raise HTTPException / return 形态 / docstring），
每条用例带 source_ref（文件:行）以便追溯。本脚本不含 LLM，确定性强、可重复生成。
"""

import datetime
import html
import json
import os


ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_JSON = os.path.join(ROOT, "..", "research-agent-test", "structured_cases.json")
OUT_HTML = os.path.join(ROOT, "结构化测试用例_含预期结果.html")

# ---------------------------------------------------------------------------
# 模块级功能推断（来源：实际阅读源码）
# ---------------------------------------------------------------------------
MODULES = [
    {
        "key": "auth",
        "name": "认证服务",
        "prefix": "/api/v1/auth",
        "source": "tools/auth/routes.py",
        "functions": [
            "账号密码登录：换取 access + refresh 双 token（POST /login）",
            "refresh 续签：用 refresh token 轮换新双 token，旧 refresh 进黑名单防重放（POST /refresh）",
            "登出：把当前 access token 加入黑名单，幂等（POST /logout）",
            "当前用户：返回登录用户基本信息（GET /me）",
            "修改密码：校验旧密码后写新哈希（POST /change-password）",
        ],
        "boundaries": [
            "登录失败锁定：5 次失败后 5 分钟内拒绝（423 account_locked）",
            "账号非 active 状态：403 user_<status>",
            "登录限流：同一 IP 频繁失败返回 429",
            "refresh 过期 / 被吊销（黑名单）/ 用户失效：401",
            "logout 缺 token：400 missing_token，且已过期 token 也视为成功（幂等）",
            "改密旧密码错误：400 old_password_incorrect",
        ],
    },
    {
        "key": "rbac",
        "name": "权限管理（RBAC）",
        "prefix": "/api/v1/rbac",
        "source": "tools/auth/rbac.py",
        "functions": [
            "当前权限：返回登录账号的角色 / 菜单 / 是否管理员（GET /me）",
            "接口目录：列出全部接口与基础接口（管理员，GET /catalog）",
            "角色 CRUD：增(201)/查/改/删（GET|POST|PUT|DELETE /roles）",
            "用户角色分配：分页查询用户并分配角色（GET /users、PUT /users/{id}/role）",
            "身份跟随真实登录人：优先用 X-BMP-Email 解析真实账号（_resolve_real_user）",
        ],
        "boundaries": [
            "仅管理员可访问 /catalog、/roles、/users、/users/{id}/role（否则 403 rbac_admin_required）",
            "系统角色 administrator / employee 不可删除（400 system_role_cannot_be_deleted）",
            "角色 key 重复：409 role_key_taken",
            "角色 / 用户不存在：404",
            "不能把自身管理员角色降权（400 cannot_remove_own_admin_role）",
        ],
    },
    {
        "key": "admin",
        "name": "用户管理",
        "prefix": "/api/v1/admin",
        "source": "tools/auth/admin_routes.py",
        "functions": [
            "创建用户：201，username 唯一（POST /users）",
            "查询用户：列表（GET /users）",
            "修改用户：patch 改状态/角色（PATCH /users/{id}）",
            "删除用户：204（DELETE /users/{id}）",
        ],
        "boundaries": [
            "username 重复：409 username_taken",
            "用户不存在：404 user_not_found",
            "不能自降管理员 / 自禁用 / 自删除：400（cannot_demote_self / cannot_disable_self / cannot_delete_self）",
        ],
    },
    {
        "key": "wechat",
        "name": "企业微信渠道",
        "prefix": "/api/v1/wechat",
        "source": "tools/wechat_channel/admin_api.py",
        "functions": [
            "扫码登录流程：发起(login/start)→轮询状态(login/{key})→确认→取消(delete)",
            "账号管理：列表 / 删除 / 启停 / 白名单增删查",
            "文件下载代理：/dl/{short_id} 经服务端取文件",
        ],
        "boundaries": [
            "渠道未启用（WECHAT_CHANNEL_ENABLED=0）：503",
            "账号不存在：404",
            "白名单 user_id 为空：400",
            "/dl 路径越界：403 outside_result_dir；shortlink 不存在：404；invalid_path：400",
        ],
    },
    {
        "key": "schedules",
        "name": "定时任务",
        "prefix": "/api/v1/schedules",
        "source": "tools/scheduler/api.py",
        "functions": [
            "任务 CRUD：增 / 查 / 改 / 删",
            "立即触发：run 触发一次（返回 status:triggered + thread_id）",
            "启停切换：toggle 改变启用状态",
        ],
        "boundaries": [
            "参数校验失败：400",
            "任务不存在：404",
        ],
    },
    {
        "key": "kb-admin",
        "name": "审计知识库管理",
        "prefix": "/api/kb-admin",
        "source": "tools/audit_kb_admin/admin_api.py",
        "functions": [
            "待办确认/忽略：pending count / confirm / dismiss（审计任务审批）",
            "文档管理：文档列表 / 内容查看 / 段落 diff",
            "操作日志：审计操作记录查询",
        ],
        "boundaries": [
            "任务不存在：404；任务已处理：400",
            "文档 / 知识库不存在或未索引：404",
        ],
    },
    {
        "key": "audit_kb",
        "name": "审计知识库（查询）",
        "prefix": "/api/audit_kb",
        "source": "tools/audit_kb/api.py",
        "functions": [
            "知识库检索 / 文档读取 / 文档元信息 / 法规检索",
        ],
        "boundaries": [
            "工具未初始化：503；知识库不存在：404；未索引：404",
            "source 路径越界：403；非法路径：400；不支持文件类型：400",
        ],
    },
    {
        "key": "cockpit",
        "name": "高管报告厅（国密代理）",
        "prefix": "/api/v1/cockpit",
        "source": "tools/cockpit/api.py",
        "functions": [
            "代理国密 API：/proxy 转发请求并返回结构化响应",
        ],
        "boundaries": [
            "国密签名失败：502；服务未启用：503；超时：504；响应解析失败：502；不支持：501",
        ],
    },
]

# ---------------------------------------------------------------------------
# 结构化用例（预期结果来自源码；source_ref = 文件:行）
# ---------------------------------------------------------------------------
CASES = [
    # ---- auth ----
    {
        "case_id": "TC-AUTH-01",
        "module": "auth",
        "title": "正确账号密码登录成功换取双 token",
        "scope": "正常",
        "kind": "api",
        "tag": "全量",
        "priority": "P0",
        "source_ref": "tools/auth/routes.py:91",
        "preconditions": "存在 active 状态账号；IP 未被限流；账号未锁定",
        "steps": ["POST /api/v1/auth/login，body={username,password}（正确凭据）", "解析响应"],
        "expected_result": '200；返回 access_token、refresh_token 非空，token_type="Bearer"，expires_in>0（秒）',
        "assertion_type": "contract",
    },
    {
        "case_id": "TC-AUTH-02",
        "module": "auth",
        "title": "错误密码登录被拒",
        "scope": "异常",
        "kind": "api",
        "tag": "全量",
        "priority": "P0",
        "source_ref": "tools/auth/routes.py:108",
        "preconditions": "账号存在",
        "steps": ["POST /api/v1/auth/login，body={username, password:错误值}"],
        "expected_result": "401，detail=invalid_credentials；不返回 token",
        "assertion_type": "contract",
    },
    {
        "case_id": "TC-AUTH-03",
        "module": "auth",
        "title": "锁定账号登录被拒",
        "scope": "异常",
        "kind": "api",
        "tag": "全量",
        "priority": "P1",
        "source_ref": "tools/auth/routes.py:116",
        "preconditions": "账号 locked_until 晚于当前时间",
        "steps": ["POST /api/v1/auth/login（正确凭据）"],
        "expected_result": "423，detail 形如 account_locked_until=<ISO 时间>",
        "assertion_type": "contract",
    },
    {
        "case_id": "TC-AUTH-04",
        "module": "auth",
        "title": "非 active 账号登录被拒",
        "scope": "异常",
        "kind": "api",
        "tag": "全量",
        "priority": "P1",
        "source_ref": "tools/auth/routes.py:122",
        "preconditions": "账号 status != 'active'（如 disabled）",
        "steps": ["POST /api/v1/auth/login（正确凭据）"],
        "expected_result": "403，detail=user_<status>",
        "assertion_type": "contract",
    },
    {
        "case_id": "TC-AUTH-05",
        "module": "auth",
        "title": "同 IP 频繁失败触发限流",
        "scope": "安全",
        "kind": "api",
        "tag": "全量",
        "priority": "P1",
        "source_ref": "tools/auth/routes.py:95",
        "preconditions": "同一 IP 短时间内多次登录失败",
        "steps": ["连续多次 POST /api/v1/auth/login 失败"],
        "expected_result": "429，detail=too_many_login_attempts",
        "assertion_type": "contract",
    },
    {
        "case_id": "TC-AUTH-06",
        "module": "auth",
        "title": "有效 refresh 续签成功并轮换",
        "scope": "正常",
        "kind": "api",
        "tag": "全量",
        "priority": "P0",
        "source_ref": "tools/auth/routes.py:152",
        "preconditions": "持有未过期、未吊销的 refresh token",
        "steps": ["POST /api/v1/auth/refresh，body={refresh_token}"],
        "expected_result": "200；返回新 access_token、refresh_token；旧 refresh 进入黑名单",
        "assertion_type": "contract",
    },
    {
        "case_id": "TC-AUTH-07",
        "module": "auth",
        "title": "过期 refresh 续签失败",
        "scope": "异常",
        "kind": "api",
        "tag": "全量",
        "priority": "P1",
        "source_ref": "tools/auth/routes.py:158",
        "preconditions": "refresh token 已过期",
        "steps": ["POST /api/v1/auth/refresh"],
        "expected_result": "401，detail=refresh_expired",
        "assertion_type": "contract",
    },
    {
        "case_id": "TC-AUTH-08",
        "module": "auth",
        "title": "已吊销 refresh 续签失败",
        "scope": "安全",
        "kind": "api",
        "tag": "全量",
        "priority": "P1",
        "source_ref": "tools/auth/routes.py:174",
        "preconditions": "该 refresh 的 jti 已在 token_blacklist",
        "steps": ["POST /api/v1/auth/refresh"],
        "expected_result": "401，detail=refresh_revoked",
        "assertion_type": "contract",
    },
    {
        "case_id": "TC-AUTH-09",
        "module": "auth",
        "title": "登出吊销 access token",
        "scope": "正常",
        "kind": "api",
        "tag": "全量",
        "priority": "P0",
        "source_ref": "tools/auth/routes.py:210",
        "preconditions": "持有有效 access token",
        "steps": ["POST /api/v1/auth/logout，带 Authorization: Bearer <access>"],
        "expected_result": "200，{revoked:true}；此后该 access 调用受保护接口应 401",
        "assertion_type": "value",
    },
    {
        "case_id": "TC-AUTH-10",
        "module": "auth",
        "title": "登出缺 token 报错且幂等",
        "scope": "异常",
        "kind": "api",
        "tag": "全量",
        "priority": "P1",
        "source_ref": "tools/auth/routes.py:218",
        "preconditions": "请求不携带 token",
        "steps": ["POST /api/v1/auth/logout"],
        "expected_result": "400，detail=missing_token",
        "assertion_type": "contract",
    },
    {
        "case_id": "TC-AUTH-11",
        "module": "auth",
        "title": "已登录获取当前用户信息",
        "scope": "正常",
        "kind": "api",
        "tag": "全量",
        "priority": "P0",
        "source_ref": "tools/auth/routes.py:246",
        "preconditions": "持有有效 access token",
        "steps": ["GET /api/v1/auth/me，带 token"],
        "expected_result": "200；返回 {id,username,is_admin,status,created_at,last_login_at}",
        "assertion_type": "contract",
    },
    {
        "case_id": "TC-AUTH-12",
        "module": "auth",
        "title": "未登录访问 /me 被拒",
        "scope": "安全",
        "kind": "api",
        "tag": "全量",
        "priority": "P0",
        "source_ref": "tools/auth/routes.py:247",
        "preconditions": "无 token",
        "steps": ["GET /api/v1/auth/me"],
        "expected_result": "401（依赖 get_current_user 鉴权）",
        "assertion_type": "contract",
    },
    {
        "case_id": "TC-AUTH-13",
        "module": "auth",
        "title": "正确旧密码改密成功",
        "scope": "正常",
        "kind": "api",
        "tag": "全量",
        "priority": "P1",
        "source_ref": "tools/auth/routes.py:259",
        "preconditions": "持有有效 token；old_password 正确",
        "steps": ["POST /api/v1/auth/change-password，body={old_password,new_password(≥8位)}"],
        "expected_result": "200，{changed:true, revoked_tokens:0}",
        "assertion_type": "value",
    },
    {
        "case_id": "TC-AUTH-14",
        "module": "auth",
        "title": "旧密码错误改密失败",
        "scope": "异常",
        "kind": "api",
        "tag": "全量",
        "priority": "P1",
        "source_ref": "tools/auth/routes.py:266",
        "preconditions": "持有有效 token；old_password 错误",
        "steps": ["POST /api/v1/auth/change-password"],
        "expected_result": "400，detail=old_password_incorrect",
        "assertion_type": "contract",
    },
    {
        "case_id": "TC-AUTH-15",
        "module": "auth",
        "title": "未登录改密被拒",
        "scope": "安全",
        "kind": "api",
        "tag": "全量",
        "priority": "P1",
        "source_ref": "tools/auth/routes.py:260",
        "preconditions": "无 token",
        "steps": ["POST /api/v1/auth/change-password"],
        "expected_result": "401",
        "assertion_type": "contract",
    },
    # ---- rbac ----
    {
        "case_id": "TC-RBAC-01",
        "module": "rbac",
        "title": "普通用户获取自身权限",
        "scope": "正常",
        "kind": "api",
        "tag": "全量",
        "priority": "P0",
        "source_ref": "tools/auth/rbac.py:192",
        "preconditions": "持有有效 token（普通员工）",
        "steps": ["GET /api/v1/rbac/me，带 token"],
        "expected_result": "200；返回 {roles, menus, is_admin:false, account}；menus 不含 rbac",
        "assertion_type": "value",
    },
    {
        "case_id": "TC-RBAC-02",
        "module": "rbac",
        "title": "非管理员访问接口目录被拒",
        "scope": "安全",
        "kind": "api",
        "tag": "全量",
        "priority": "P0",
        "source_ref": "tools/auth/rbac.py:206",
        "preconditions": "普通员工 token",
        "steps": ["GET /api/v1/rbac/catalog"],
        "expected_result": "403，detail=rbac_admin_required",
        "assertion_type": "contract",
    },
    {
        "case_id": "TC-RBAC-03",
        "module": "rbac",
        "title": "管理员查看接口目录",
        "scope": "正常",
        "kind": "api",
        "tag": "全量",
        "priority": "P0",
        "source_ref": "tools/auth/rbac.py:205",
        "preconditions": "管理员 token",
        "steps": ["GET /api/v1/rbac/catalog"],
        "expected_result": "200；返回 {menus, apis, base_apis}，apis 含全部 /api 路由，base_apis 含认证基础接口",
        "assertion_type": "contract",
    },
    {
        "case_id": "TC-RBAC-04",
        "module": "rbac",
        "title": "非管理员列角色被拒",
        "scope": "安全",
        "kind": "api",
        "tag": "全量",
        "priority": "P1",
        "source_ref": "tools/auth/rbac.py:214",
        "preconditions": "普通员工 token",
        "steps": ["GET /api/v1/rbac/roles"],
        "expected_result": "403，detail=rbac_admin_required",
        "assertion_type": "contract",
    },
    {
        "case_id": "TC-RBAC-05",
        "module": "rbac",
        "title": "创建角色：重复 key 冲突 / 成功",
        "scope": "边界",
        "kind": "api",
        "tag": "全量",
        "priority": "P1",
        "source_ref": "tools/auth/rbac.py:219",
        "preconditions": "管理员 token",
        "steps": ["POST /api/v1/rbac/roles，body={key:'新key',name,...}", "用相同 key 再次提交"],
        "expected_result": "首次 201 返回角色字典；重复 key 返回 409 role_key_taken",
        "assertion_type": "contract",
    },
    {
        "case_id": "TC-RBAC-06",
        "module": "rbac",
        "title": "修改不存在角色",
        "scope": "异常",
        "kind": "api",
        "tag": "全量",
        "priority": "P1",
        "source_ref": "tools/auth/rbac.py:226",
        "preconditions": "管理员 token；不存在的 role_id",
        "steps": ["PUT /api/v1/rbac/roles/{不存在id}"],
        "expected_result": "404，detail=role_not_found",
        "assertion_type": "contract",
    },
    {
        "case_id": "TC-RBAC-07",
        "module": "rbac",
        "title": "删除系统角色被拒",
        "scope": "安全",
        "kind": "api",
        "tag": "全量",
        "priority": "P1",
        "source_ref": "tools/auth/rbac.py:235",
        "preconditions": "管理员 token；role_id 指向 administrator 或 employee",
        "steps": ["DELETE /api/v1/rbac/roles/{系统角色id}"],
        "expected_result": "400，detail=system_role_cannot_be_deleted",
        "assertion_type": "contract",
    },
    {
        "case_id": "TC-RBAC-08",
        "module": "rbac",
        "title": "删除不存在角色",
        "scope": "异常",
        "kind": "api",
        "tag": "全量",
        "priority": "P2",
        "source_ref": "tools/auth/rbac.py:235",
        "preconditions": "管理员 token；不存在的 role_id",
        "steps": ["DELETE /api/v1/rbac/roles/{不存在id}"],
        "expected_result": "404，detail=role_not_found",
        "assertion_type": "contract",
    },
    {
        "case_id": "TC-RBAC-09",
        "module": "rbac",
        "title": "分页查询用户",
        "scope": "正常",
        "kind": "api",
        "tag": "全量",
        "priority": "P1",
        "source_ref": "tools/auth/rbac.py:251",
        "preconditions": "管理员 token",
        "steps": ["GET /api/v1/rbac/users?page=1&page_size=20"],
        "expected_result": "200；返回 {users,page,page_size,total,total_pages}，total_pages=max(1,ceil(total/page_size))",
        "assertion_type": "contract",
    },
    {
        "case_id": "TC-RBAC-10",
        "module": "rbac",
        "title": "管理员不能自降权",
        "scope": "安全",
        "kind": "api",
        "tag": "全量",
        "priority": "P1",
        "source_ref": "tools/auth/rbac.py:283",
        "preconditions": "管理员 token（操作自身）",
        "steps": ["PUT /api/v1/rbac/users/{自己id}/role，body={role_key:'employee'}"],
        "expected_result": "400，detail=cannot_remove_own_admin_role",
        "assertion_type": "contract",
    },
    {
        "case_id": "TC-RBAC-11",
        "module": "rbac",
        "title": "分配角色给不存在用户",
        "scope": "异常",
        "kind": "api",
        "tag": "全量",
        "priority": "P2",
        "source_ref": "tools/auth/rbac.py:284",
        "preconditions": "管理员 token；不存在的 user_id",
        "steps": ["PUT /api/v1/rbac/users/{不存在id}/role"],
        "expected_result": "404，detail=user_not_found",
        "assertion_type": "contract",
    },
    # ---- admin ----
    {
        "case_id": "TC-ADMIN-01",
        "module": "admin",
        "title": "创建用户成功",
        "scope": "正常",
        "kind": "api",
        "tag": "全量",
        "priority": "P1",
        "source_ref": "tools/auth/admin_routes.py:56",
        "preconditions": "管理员 token；username 未被占用",
        "steps": ["POST /api/v1/admin/users，body={username,password,...}"],
        "expected_result": "201；返回 UserResponse",
        "assertion_type": "contract",
    },
    {
        "case_id": "TC-ADMIN-02",
        "module": "admin",
        "title": "创建重复用户名用户",
        "scope": "边界",
        "kind": "api",
        "tag": "全量",
        "priority": "P1",
        "source_ref": "tools/auth/admin_routes.py:67",
        "preconditions": "username 已存在",
        "steps": ["POST /api/v1/admin/users"],
        "expected_result": "409，detail=username_taken",
        "assertion_type": "contract",
    },
    {
        "case_id": "TC-ADMIN-03",
        "module": "admin",
        "title": "修改不存在用户",
        "scope": "异常",
        "kind": "api",
        "tag": "全量",
        "priority": "P2",
        "source_ref": "tools/auth/admin_routes.py:147",
        "preconditions": "不存在的 user_id",
        "steps": ["PATCH /api/v1/admin/users/{不存在id}"],
        "expected_result": "404，detail=user_not_found",
        "assertion_type": "contract",
    },
    {
        "case_id": "TC-ADMIN-04",
        "module": "admin",
        "title": "不能删除自己",
        "scope": "安全",
        "kind": "api",
        "tag": "全量",
        "priority": "P1",
        "source_ref": "tools/auth/admin_routes.py:188",
        "preconditions": "管理员操作自身",
        "steps": ["DELETE /api/v1/admin/users/{自己id}"],
        "expected_result": "400，detail=cannot_delete_self",
        "assertion_type": "contract",
    },
    # ---- wechat ----
    {
        "case_id": "TC-WECHAT-01",
        "module": "wechat",
        "title": "发起企微扫码登录",
        "scope": "正常",
        "kind": "api",
        "tag": "全量",
        "priority": "P1",
        "source_ref": "tools/wechat_channel/admin_api.py:97",
        "preconditions": "企微渠道已启用",
        "steps": ["POST /api/v1/wechat/login/start"],
        "expected_result": "200；返回 session_key 及二维码/跳转信息",
        "assertion_type": "contract",
    },
    {
        "case_id": "TC-WECHAT-02",
        "module": "wechat",
        "title": "轮询不存在的登录会话",
        "scope": "异常",
        "kind": "api",
        "tag": "全量",
        "priority": "P2",
        "source_ref": "tools/wechat_channel/admin_api.py:122",
        "preconditions": "不存在的 session_key",
        "steps": ["GET /api/v1/wechat/login/{不存在key}"],
        "expected_result": '200；{session_key, status:"not_found"}',
        "assertion_type": "value",
    },
    {
        "case_id": "TC-WECHAT-03",
        "module": "wechat",
        "title": "渠道未启用时启停账号",
        "scope": "边界",
        "kind": "api",
        "tag": "全量",
        "priority": "P2",
        "source_ref": "tools/wechat_channel/admin_api.py:321",
        "preconditions": "WECHAT_CHANNEL_ENABLED=0 或 server 未就绪",
        "steps": ["POST /api/v1/wechat/accounts/{id}/start"],
        "expected_result": "503，detail=wechat channel 未启用（...）",
        "assertion_type": "contract",
    },
    {
        "case_id": "TC-WECHAT-04",
        "module": "wechat",
        "title": "删除不存在账号",
        "scope": "异常",
        "kind": "api",
        "tag": "全量",
        "priority": "P2",
        "source_ref": "tools/wechat_channel/admin_api.py:294",
        "preconditions": "不存在的 account_id",
        "steps": ["DELETE /api/v1/wechat/accounts/{不存在id}"],
        "expected_result": "404，detail 含'账号 不存在'",
        "assertion_type": "contract",
    },
    {
        "case_id": "TC-WECHAT-05",
        "module": "wechat",
        "title": "白名单 user_id 为空",
        "scope": "边界",
        "kind": "api",
        "tag": "全量",
        "priority": "P2",
        "source_ref": "tools/wechat_channel/admin_api.py:379",
        "preconditions": "account 存在",
        "steps": ['POST /api/v1/wechat/accounts/{id}/whitelist，body={user_id:""}'],
        "expected_result": "400，detail=user_id 不能为空",
        "assertion_type": "contract",
    },
    {
        "case_id": "TC-WECHAT-06",
        "module": "wechat",
        "title": "下载越界文件被拒",
        "scope": "安全",
        "kind": "api",
        "tag": "全量",
        "priority": "P1",
        "source_ref": "tools/wechat_channel/admin_api.py:443",
        "preconditions": "short_id 指向 result 目录外",
        "steps": ["GET /api/v1/wechat/dl/{short_id}"],
        "expected_result": "403，detail=outside_result_dir",
        "assertion_type": "contract",
    },
    # ---- schedules ----
    {
        "case_id": "TC-SCHED-01",
        "module": "schedules",
        "title": "创建定时任务成功",
        "scope": "正常",
        "kind": "api",
        "tag": "全量",
        "priority": "P1",
        "source_ref": "tools/scheduler/api.py:66",
        "preconditions": "合法任务参数",
        "steps": ["POST /api/v1/schedules，body={name,cron,...}"],
        "expected_result": "200；返回任务项（_to_api_item）",
        "assertion_type": "contract",
    },
    {
        "case_id": "TC-SCHED-02",
        "module": "schedules",
        "title": "参数非法创建失败",
        "scope": "边界",
        "kind": "api",
        "tag": "全量",
        "priority": "P1",
        "source_ref": "tools/scheduler/api.py:76",
        "preconditions": "任务参数校验失败",
        "steps": ["POST /api/v1/schedules，body 缺必填/格式错"],
        "expected_result": "400，{error:...}",
        "assertion_type": "contract",
    },
    {
        "case_id": "TC-SCHED-03",
        "module": "schedules",
        "title": "立即触发不存在任务",
        "scope": "异常",
        "kind": "api",
        "tag": "全量",
        "priority": "P2",
        "source_ref": "tools/scheduler/api.py:162",
        "preconditions": "不存在的 schedule_id",
        "steps": ["POST /api/v1/schedules/{不存在id}/run"],
        "expected_result": '404，{error:"schedule not found"}',
        "assertion_type": "contract",
    },
    {
        "case_id": "TC-SCHED-04",
        "module": "schedules",
        "title": "触发任务返回 triggered",
        "scope": "正常",
        "kind": "api",
        "tag": "全量",
        "priority": "P1",
        "source_ref": "tools/scheduler/api.py:171",
        "preconditions": "任务存在",
        "steps": ["POST /api/v1/schedules/{id}/run"],
        "expected_result": '200；{id, status:"triggered", thread_id}',
        "assertion_type": "value",
    },
    # ---- kb-admin ----
    {
        "case_id": "TC-KBA-01",
        "module": "kb-admin",
        "title": "确认待办审计任务",
        "scope": "正常",
        "kind": "api",
        "tag": "全量",
        "priority": "P1",
        "source_ref": "tools/audit_kb_admin/admin_api.py:179",
        "preconditions": "存在 pending 任务",
        "steps": ["POST /api/kb-admin/pending/{task_id}/confirm"],
        "expected_result": "200；{ok:true, task_id}",
        "assertion_type": "value",
    },
    {
        "case_id": "TC-KBA-02",
        "module": "kb-admin",
        "title": "确认不存在任务",
        "scope": "异常",
        "kind": "api",
        "tag": "全量",
        "priority": "P2",
        "source_ref": "tools/audit_kb_admin/admin_api.py:184",
        "preconditions": "不存在的 task_id",
        "steps": ["POST /api/kb-admin/pending/{不存在id}/confirm"],
        "expected_result": "404，detail=任务不存在",
        "assertion_type": "contract",
    },
    {
        "case_id": "TC-KBA-03",
        "module": "kb-admin",
        "title": "重复确认已处理任务",
        "scope": "边界",
        "kind": "api",
        "tag": "全量",
        "priority": "P2",
        "source_ref": "tools/audit_kb_admin/admin_api.py:186",
        "preconditions": "任务状态已 confirmed/dismissed",
        "steps": ["POST /api/kb-admin/pending/{已处理id}/confirm"],
        "expected_result": "400，detail=任务已处理",
        "assertion_type": "contract",
    },
    {
        "case_id": "TC-KBA-04",
        "module": "kb-admin",
        "title": "查看文档内容不存在",
        "scope": "异常",
        "kind": "api",
        "tag": "全量",
        "priority": "P2",
        "source_ref": "tools/audit_kb_admin/admin_api.py:303",
        "preconditions": "不存在的 src_id",
        "steps": ["GET /api/kb-admin/documents/{不存在src_id}/content"],
        "expected_result": "404，detail=文档不存在",
        "assertion_type": "contract",
    },
    # ---- audit_kb ----
    {
        "case_id": "TC-AKB-01",
        "module": "audit_kb",
        "title": "工具未初始化检索",
        "scope": "边界",
        "kind": "api",
        "tag": "全量",
        "priority": "P2",
        "source_ref": "tools/audit_kb/api.py:60",
        "preconditions": "AuditKBToolkit 未初始化",
        "steps": ["GET /api/audit_kb/... 检索"],
        "expected_result": "503，detail=AuditKBToolkit 未初始化",
        "assertion_type": "contract",
    },
    {
        "case_id": "TC-AKB-02",
        "module": "audit_kb",
        "title": "越界 source 路径被拒",
        "scope": "安全",
        "kind": "api",
        "tag": "全量",
        "priority": "P1",
        "source_ref": "tools/audit_kb/api.py:88",
        "preconditions": "source 指向允许目录外",
        "steps": ["GET /api/audit_kb/document?source=<越界路径>"],
        "expected_result": "403，detail=source 路径越界",
        "assertion_type": "contract",
    },
    {
        "case_id": "TC-AKB-03",
        "module": "audit_kb",
        "title": "不支持文件类型",
        "scope": "边界",
        "kind": "api",
        "tag": "全量",
        "priority": "P2",
        "source_ref": "tools/audit_kb/api.py:290",
        "preconditions": "文件后缀不支持",
        "steps": ["GET /api/audit_kb/document?source=<不支持类型>"],
        "expected_result": "400，detail=不支持的文件类型",
        "assertion_type": "contract",
    },
    # ---- cockpit ----
    {
        "case_id": "TC-COCK-01",
        "module": "cockpit",
        "title": "国密代理签名失败",
        "scope": "安全",
        "kind": "api",
        "tag": "全量",
        "priority": "P1",
        "source_ref": "tools/cockpit/api.py:231",
        "preconditions": "国密签名校验不通过",
        "steps": ["POST /api/v1/cockpit/proxy"],
        "expected_result": "502，detail=国密 API 签名验证失败",
        "assertion_type": "contract",
    },
    {
        "case_id": "TC-COCK-02",
        "module": "cockpit",
        "title": "国密代理超时",
        "scope": "边界",
        "kind": "api",
        "tag": "全量",
        "priority": "P2",
        "source_ref": "tools/cockpit/api.py:334",
        "preconditions": "下游国密 API 超时",
        "steps": ["POST /api/v1/cockpit/proxy"],
        "expected_result": "504，detail=国密 API 超时",
        "assertion_type": "contract",
    },
    {
        "case_id": "TC-COCK-03",
        "module": "cockpit",
        "title": "国密服务未启用",
        "scope": "边界",
        "kind": "api",
        "tag": "全量",
        "priority": "P2",
        "source_ref": "tools/cockpit/api.py:289",
        "preconditions": "服务未启用",
        "steps": ["POST /api/v1/cockpit/proxy"],
        "expected_result": "503",
        "assertion_type": "contract",
    },
]


def build_json():
    payload = {
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "target": "research-agent",
        "method": "source-inferred (white-box, no requirements doc)",
        "modules": [{k: m[k] for k in ("key", "name", "prefix", "source")} for m in MODULES],
        "case_count": len(CASES),
        "cases": CASES,
    }
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return payload


def esc(x):
    return html.escape(str(x))


def build_html(payload):
    mod_by_key = {m["key"]: m for m in MODULES}
    # 统计
    by_mod = {}
    for c in CASES:
        by_mod.setdefault(c["module"], 0)
        by_mod[c["module"]] += 1
    by_scope = {}
    for c in CASES:
        by_scope.setdefault(c["scope"], 0)
        by_scope[c["scope"]] += 1

    parts = []
    parts.append("""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>research-agent 结构化测试用例（含预期结果）</title>
<style>
:root{--bg:#0f1115;--card:#1a1e26;--ink:#e6e8ee;--sub:#9aa3b2;--line:#2a2f3a;--accent:#4f9dff;--ok:#39b54a;--warn:#f0a020;--bad:#e5484d}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.7 -apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:28px 22px 80px}
h1{font-size:26px;margin:0 0 6px}
h2{font-size:20px;margin:34px 0 12px;border-left:4px solid var(--accent);padding-left:10px}
h3{font-size:16px;margin:20px 0 8px;color:var(--accent)}
.meta{color:var(--sub);font-size:13px;margin-bottom:20px}
.cards{display:flex;gap:12px;flex-wrap:wrap;margin:14px 0 6px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 16px;min-width:120px}
.card b{font-size:22px;display:block;color:var(--accent)}
.card span{color:var(--sub);font-size:12px}
table{border-collapse:collapse;width:100%;margin:12px 0 8px;font-size:13.5px}
th,td{border:1px solid var(--line);padding:8px 10px;vertical-align:top;text-align:left}
th{background:#20262f;color:var(--sub);position:sticky;top:0}
tr:nth-child(even){background:#161a21}
code{background:#0c0e12;padding:1px 6px;border-radius:5px;color:#8fd0ff;font-size:12.5px}
.pill{display:inline-block;padding:1px 8px;border-radius:20px;font-size:11.5px;border:1px solid var(--line)}
.s-normal{color:var(--ok);border-color:#1f5530}
.s-exception{color:var(--warn);border-color:#5a4410}
.s-security{color:var(--bad);border-color:#5a2226}
.s-boundary{color:#b58bff;border-color:#3a2a55}
.p0{color:var(--bad)}.p1{color:var(--warn)}.p2{color:var(--sub)}
.func{border:1px solid var(--line);border-radius:10px;background:var(--card);padding:14px 16px;margin:12px 0}
.func h4{margin:0 0 8px;font-size:15px}
.tip{background:#13202b;border:1px solid #1d3a4a;color:#bfe3f2;padding:10px 14px;border-radius:8px;font-size:13px;margin:10px 0}
.note{color:var(--sub);font-size:12.5px}
ul{margin:6px 0;padding-left:20px}
</style></head><body><div class="wrap">""")

    parts.append("<h1>research-agent 结构化测试用例（含预期结果）</h1>")
    parts.append(
        f"<div class='meta'>生成时间：{esc(payload['generated_at'])} ｜ 目标：{esc(payload['target'])} ｜ 方法：{esc(payload['method'])} ｜ 用例数：<b>{len(CASES)}</b></div>"
    )
    parts.append(
        "<div class='tip'>本批用例的<strong>预期结果均直接来自源码</strong>（路由装饰器、<code>raise HTTPException</code> 状态码、<code>return</code> 返回形态、docstring），每条带 <code>source_ref</code> 可追溯到具体文件与行号。断言类型分两类：<b>contract</b>=校验状态码/返回结构；<b>value</b>=校验具体返回值（如 revoked:true）。这正好弥补了此前流程缺「期望结果」的空洞——但属<strong>白盒契约级</strong>预期，业务数值正确性仍需后续 AI 验证服务或需求基线补充。</div>"
    )

    # 总览卡
    parts.append("<div class='cards'>")
    parts.append(f"<div class='card'><b>{len(CASES)}</b><span>结构化用例</span></div>")
    parts.append(f"<div class='card'><b>{len(MODULES)}</b><span>覆盖模块</span></div>")
    parts.append(f"<div class='card'><b>{by_scope.get('正常', 0)}</b><span>正常</span></div>")
    parts.append(f"<div class='card'><b>{by_scope.get('异常', 0)}</b><span>异常</span></div>")
    parts.append(f"<div class='card'><b>{by_scope.get('安全', 0)}</b><span>安全</span></div>")
    parts.append(f"<div class='card'><b>{by_scope.get('边界', 0)}</b><span>边界</span></div>")
    parts.append("</div>")
    parts.append(
        "<div class='note'>各模块用例数："
        + "，".join(f"{mod_by_key[k]['name']} {v}" for k, v in by_mod.items())
        + "</div>"
    )

    # 模块章节
    anchor = 0
    for m in MODULES:
        anchor += 1
        parts.append(f"<h2>{anchor}. 模块：{esc(m['name'])} <code>{esc(m['prefix'])}</code></h2>")
        parts.append(f"<div class='note'>源码：<code>{esc(m['source'])}</code></div>")
        parts.append("<div class='func'><h4>推断实现的功能</h4><ul>")
        for fn in m["functions"]:
            parts.append(f"<li>{esc(fn)}</li>")
        parts.append("</ul><h4>应测试的内容与边界</h4><ul>")
        for b in m["boundaries"]:
            parts.append(f"<li>{esc(b)}</li>")
        parts.append("</ul></div>")

        parts.append(
            "<table><thead><tr><th>用例标识</th><th>标题</th><th>范围</th><th>优先级</th><th>前置条件</th><th>执行步骤</th><th>预期结果</th><th>源码</th></tr></thead><tbody>"
        )
        for c in [x for x in CASES if x["module"] == m["key"]]:
            scope_cls = {
                "正常": "s-normal",
                "异常": "s-exception",
                "安全": "s-security",
                "边界": "s-boundary",
            }.get(c["scope"], "")
            steps = "<br>".join(f"{i + 1}. {esc(s)}" for i, s in enumerate(c["steps"]))
            parts.append(
                f"<tr><td><code>{esc(c['case_id'])}</code></td>"
                f"<td>{esc(c['title'])}</td>"
                f"<td><span class='pill {scope_cls}'>{esc(c['scope'])}</span></td>"
                f"<td class='p{esc(c['priority'][-1])}'>{esc(c['priority'])}</td>"
                f"<td>{esc(c['preconditions'])}</td>"
                f"<td>{steps}</td>"
                f"<td>{esc(c['expected_result'])}</td>"
                f"<td class='note'>{esc(c['source_ref'])}</td></tr>"
            )
        parts.append("</tbody></table>")

    parts.append("""
<h2>附录：本批用例的方法学说明</h2>
<ul>
<li><b>为什么预期结果可信：</b>全部来自代码实际分支（状态码、返回字典键、注释约定），非主观猜测。</li>
<li><b>仍存在的盲区：</b>源码只声明"接口契约"，不声明"业务数值正确性"（如某查询应返回 95 条而非 100 条）。这类需需求基线或 AI 验证服务判定。</li>
<li><b>如何扩展：</b>按相同模板继续补齐其余 ~230 条路由即可；字段与 test-accel 的 case/point 模型一致，可直接入库驱动 UI 执行。</li>
</ul>
</div></body></html>""")
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write("".join(parts))


if __name__ == "__main__":
    payload = build_json()
    build_html(payload)
    print(f"cases={payload['case_count']} modules={len(MODULES)}")
    print("JSON ->", os.path.abspath(OUT_JSON))
    print("HTML ->", os.path.abspath(OUT_HTML))
