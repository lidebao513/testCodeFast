# 测试用例清册 · research-agent

> 自动生成，共 **415** 条用例。 按类型（正常/异常）：{'正常': 237, '安全': 81, '边界': 71, '异常': 26}；按优先级：{'P1': 233, 'P2': 182}；按测试类型（全量/新增）：{'全量': 415}。

## 一、汇总

### 按类型（正常/异常）
- 正常: 237
- 安全: 81
- 边界: 71
- 异常: 26

### 按测试类型（全量/新增）
- 全量: 415

### 按优先级
- P1: 233
- P2: 182

### 按模块（Top）
- 账户/用户/鉴权 Auth: 114
- 线程 Thread: 37
- 审计/审核看板 Audit: 35
- 产物/文档 Artifact: 30
- 前端 Frontend: 28
- 业务函数·数据模型定义: 24
- 业务函数·账户/用户/鉴权: 24
- 业务函数·调度/同步任务: 23
- 对话/会话 Chat: 21
- 业务函数·通知推送: 21
- 业务函数·工具/集成: 12
- 业务函数·简报/总结: 12
- 业务函数·对话/智能体编排: 12
- 业务函数·产物/文档: 10
- 智能体 Agent: 3
- 健康/其它: 3
- 未归类 Other: 3
- 简报 Briefing: 3

## 二、用例明细

### TP-001 · [正常] 账户/用户/鉴权·登录鉴权（POST /api/v1/auth/login）· 正常-可用性
- 模块：账户/用户/鉴权 Auth
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-91b068ac` / TP `TP-001`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /api/v1/auth/login，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 POST /api/v1/auth/login 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·登录鉴权 功能可用：POST /api/v1/auth/login 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 login）

### TP-002 · [安全] 账户/用户/鉴权·登录鉴权（POST /api/v1/auth/login）· 安全-鉴权缺失
- 模块：账户/用户/鉴权 Auth
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-91b068ac` / TP `TP-002`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /api/v1/auth/login，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 POST /api/v1/auth/login 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·登录鉴权 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何账户/用户/鉴权业务数据；实现参考 login）

### TP-003 · [边界] 账户/用户/鉴权·登录鉴权（POST /api/v1/auth/login）· 边界-参数缺失/非法
- 模块：账户/用户/鉴权 Auth
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-91b068ac` / TP `TP-003`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /api/v1/auth/login，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 POST /api/v1/auth/login 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·登录鉴权 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 login）

### TP-004 · [正常] 账户/用户/鉴权·登录鉴权（POST /api/v1/auth/refresh）· 正常-可用性
- 模块：账户/用户/鉴权 Auth
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-57704045` / TP `TP-004`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /api/v1/auth/refresh，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 POST /api/v1/auth/refresh 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·登录鉴权 功能可用：POST /api/v1/auth/refresh 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 refresh）

### TP-005 · [安全] 账户/用户/鉴权·登录鉴权（POST /api/v1/auth/refresh）· 安全-鉴权缺失
- 模块：账户/用户/鉴权 Auth
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-57704045` / TP `TP-005`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /api/v1/auth/refresh，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 POST /api/v1/auth/refresh 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·登录鉴权 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何账户/用户/鉴权业务数据；实现参考 refresh）

### TP-006 · [边界] 账户/用户/鉴权·登录鉴权（POST /api/v1/auth/refresh）· 边界-参数缺失/非法
- 模块：账户/用户/鉴权 Auth
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-57704045` / TP `TP-006`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /api/v1/auth/refresh，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 POST /api/v1/auth/refresh 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·登录鉴权 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 refresh）

### TP-007 · [正常] 账户/用户/鉴权·登录鉴权（POST /api/v1/auth/logout）· 正常-可用性
- 模块：账户/用户/鉴权 Auth
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-fcc8d684` / TP `TP-007`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /api/v1/auth/logout，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 POST /api/v1/auth/logout 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·登录鉴权 功能可用：POST /api/v1/auth/logout 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 logout）

### TP-008 · [安全] 账户/用户/鉴权·登录鉴权（POST /api/v1/auth/logout）· 安全-鉴权缺失
- 模块：账户/用户/鉴权 Auth
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-fcc8d684` / TP `TP-008`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /api/v1/auth/logout，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 POST /api/v1/auth/logout 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·登录鉴权 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何账户/用户/鉴权业务数据；实现参考 logout）

### TP-009 · [边界] 账户/用户/鉴权·登录鉴权（POST /api/v1/auth/logout）· 边界-参数缺失/非法
- 模块：账户/用户/鉴权 Auth
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-fcc8d684` / TP `TP-009`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /api/v1/auth/logout，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 POST /api/v1/auth/logout 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·登录鉴权 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 logout）

### TP-010 · [正常] 账户/用户/鉴权·登录鉴权（GET /api/v1/auth/me）· 正常-可用性
- 模块：账户/用户/鉴权 Auth
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-0cab29dd` / TP `TP-010`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /api/v1/auth/me，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 GET /api/v1/auth/me 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·登录鉴权 功能可用：GET /api/v1/auth/me 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 me）

### TP-011 · [安全] 账户/用户/鉴权·登录鉴权（GET /api/v1/auth/me）· 安全-鉴权缺失
- 模块：账户/用户/鉴权 Auth
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-0cab29dd` / TP `TP-011`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /api/v1/auth/me，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 GET /api/v1/auth/me 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·登录鉴权 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何账户/用户/鉴权业务数据；实现参考 me）

### TP-012 · [边界] 账户/用户/鉴权·登录鉴权（GET /api/v1/auth/me）· 边界-参数缺失/非法
- 模块：账户/用户/鉴权 Auth
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-0cab29dd` / TP `TP-012`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /api/v1/auth/me，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 GET /api/v1/auth/me 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·登录鉴权 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 me）

### TP-013 · [正常] 线程·会话线程（GET /api/v1/threads）· 正常-可用性
- 模块：线程 Thread
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-b7cd0f90` / TP `TP-013`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /api/v1/threads，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 GET /api/v1/threads 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：线程·会话线程 功能可用：GET /api/v1/threads 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 list_threads）

### TP-014 · [安全] 线程·会话线程（GET /api/v1/threads）· 安全-鉴权缺失
- 模块：线程 Thread
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-b7cd0f90` / TP `TP-014`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /api/v1/threads，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 GET /api/v1/threads 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：线程·会话线程 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何线程业务数据；实现参考 list_threads）

### TP-015 · [边界] 线程·会话线程（GET /api/v1/threads）· 边界-参数缺失/非法
- 模块：线程 Thread
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-b7cd0f90` / TP `TP-015`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /api/v1/threads，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 GET /api/v1/threads 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：线程·会话线程 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 list_threads）

### TP-016 · [正常] 智能体·智能体编排（GET /api/v1/agents）· 正常-可用性
- 模块：智能体 Agent
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-c79dd3d3` / TP `TP-016`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /api/v1/agents，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 GET /api/v1/agents 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：智能体·智能体编排 功能可用：GET /api/v1/agents 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 list_agents）

### TP-017 · [安全] 智能体·智能体编排（GET /api/v1/agents）· 安全-鉴权缺失
- 模块：智能体 Agent
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-c79dd3d3` / TP `TP-017`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /api/v1/agents，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 GET /api/v1/agents 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：智能体·智能体编排 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何智能体业务数据；实现参考 list_agents）

### TP-018 · [边界] 智能体·智能体编排（GET /api/v1/agents）· 边界-参数缺失/非法
- 模块：智能体 Agent
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-c79dd3d3` / TP `TP-018`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /api/v1/agents，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 GET /api/v1/agents 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：智能体·智能体编排 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 list_agents）

### TP-019 · [正常] 线程·会话线程（GET /api/v1/threads/{tid}）· 正常-可用性
- 模块：线程 Thread
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-d08046c2` / TP `TP-019`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /api/v1/threads/{tid}，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 GET /api/v1/threads/{tid} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：线程·会话线程 功能可用：GET /api/v1/threads/{tid} 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 get_thread）

### TP-020 · [安全] 线程·会话线程（GET /api/v1/threads/{tid}）· 安全-鉴权缺失
- 模块：线程 Thread
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-d08046c2` / TP `TP-020`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /api/v1/threads/{tid}，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 GET /api/v1/threads/{tid} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：线程·会话线程 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何线程业务数据；实现参考 get_thread）

### TP-021 · [边界] 线程·会话线程（GET /api/v1/threads/{tid}）· 边界-参数缺失/非法
- 模块：线程 Thread
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-d08046c2` / TP `TP-021`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /api/v1/threads/{tid}，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 GET /api/v1/threads/{tid} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：线程·会话线程 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 get_thread）

### TP-022 · [异常] 线程·会话线程（GET /api/v1/threads/{tid}）· 异常-资源不存在
- 模块：线程 Thread
- 类型：异常　优先级：P1　测试类型：全量
- 关联：FP `FP-d08046c2` / TP `TP-022`
- 前置条件：被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
- 步骤：
  1. [前置] 被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
  2. [准备] 构造请求：GET /api/v1/threads/{tid}，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 GET /api/v1/threads/{tid} 请求并捕获响应
  4. [断言] 校验：接口对非法/边界输入返回预期错误（4xx/5xx），且不产生未捕获异常或数据损坏（预期：线程·会话线程 资源不存在：访问不存在或非法的 {id} → 404，提示明确且不暴露内部细节；实现参考 get_thread）

### TP-023 · [正常] 线程·取消中止（POST /api/v1/threads/{tid}/abort）· 正常-可用性
- 模块：线程 Thread
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-f6cd93f4` / TP `TP-023`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /api/v1/threads/{tid}/abort，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 POST /api/v1/threads/{tid}/abort 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：线程·取消中止 功能可用：POST /api/v1/threads/{tid}/abort 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 abort_thread：中断运行中任务（对齐真后端 POST /threads/{tid}/abort）：）

### TP-024 · [安全] 线程·取消中止（POST /api/v1/threads/{tid}/abort）· 安全-鉴权缺失
- 模块：线程 Thread
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-f6cd93f4` / TP `TP-024`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /api/v1/threads/{tid}/abort，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 POST /api/v1/threads/{tid}/abort 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：线程·取消中止 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何线程业务数据；实现参考 abort_thread：中断运行中任务（对齐真后端 POST /threads/{tid}/abort）：）

### TP-025 · [边界] 线程·取消中止（POST /api/v1/threads/{tid}/abort）· 边界-参数缺失/非法
- 模块：线程 Thread
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-f6cd93f4` / TP `TP-025`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /api/v1/threads/{tid}/abort，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 POST /api/v1/threads/{tid}/abort 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：线程·取消中止 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 abort_thread：中断运行中任务（对齐真后端 POST /threads/{tid}/abort）：）

### TP-026 · [异常] 线程·取消中止（POST /api/v1/threads/{tid}/abort）· 异常-资源不存在
- 模块：线程 Thread
- 类型：异常　优先级：P1　测试类型：全量
- 关联：FP `FP-f6cd93f4` / TP `TP-026`
- 前置条件：被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
- 步骤：
  1. [前置] 被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
  2. [准备] 构造请求：POST /api/v1/threads/{tid}/abort，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 POST /api/v1/threads/{tid}/abort 请求并捕获响应
  4. [断言] 校验：接口对非法/边界输入返回预期错误（4xx/5xx），且不产生未捕获异常或数据损坏（预期：线程·取消中止 资源不存在：访问不存在或非法的 {id} → 404，提示明确且不暴露内部细节；实现参考 abort_thread：中断运行中任务（对齐真后端 POST /threads/{tid}/abort）：）

### TP-027 · [正常] 线程·会话线程（GET /api/v1/threads/{tid}/result/{name}）· 正常-可用性
- 模块：线程 Thread
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-4f4c303d` / TP `TP-027`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /api/v1/threads/{tid}/result/{name}，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 GET /api/v1/threads/{tid}/result/{name} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：线程·会话线程 功能可用：GET /api/v1/threads/{tid}/result/{name} 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 get_result）

### TP-028 · [安全] 线程·会话线程（GET /api/v1/threads/{tid}/result/{name}）· 安全-鉴权缺失
- 模块：线程 Thread
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-4f4c303d` / TP `TP-028`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /api/v1/threads/{tid}/result/{name}，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 GET /api/v1/threads/{tid}/result/{name} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：线程·会话线程 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何线程业务数据；实现参考 get_result）

### TP-029 · [边界] 线程·会话线程（GET /api/v1/threads/{tid}/result/{name}）· 边界-参数缺失/非法
- 模块：线程 Thread
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-4f4c303d` / TP `TP-029`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /api/v1/threads/{tid}/result/{name}，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 GET /api/v1/threads/{tid}/result/{name} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：线程·会话线程 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 get_result）

### TP-030 · [异常] 线程·会话线程（GET /api/v1/threads/{tid}/result/{name}）· 异常-资源不存在
- 模块：线程 Thread
- 类型：异常　优先级：P1　测试类型：全量
- 关联：FP `FP-4f4c303d` / TP `TP-030`
- 前置条件：被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
- 步骤：
  1. [前置] 被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
  2. [准备] 构造请求：GET /api/v1/threads/{tid}/result/{name}，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 GET /api/v1/threads/{tid}/result/{name} 请求并捕获响应
  4. [断言] 校验：接口对非法/边界输入返回预期错误（4xx/5xx），且不产生未捕获异常或数据损坏（预期：线程·会话线程 资源不存在：访问不存在或非法的 {id} → 404，提示明确且不暴露内部细节；实现参考 get_result）

### TP-031 · [正常] 线程·审批审核（GET /api/v1/threads/{tid}/artifact/preview）· 正常-可用性
- 模块：线程 Thread
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-b65000bd` / TP `TP-031`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /api/v1/threads/{tid}/artifact/preview，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 GET /api/v1/threads/{tid}/artifact/preview 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：线程·审批审核 功能可用：GET /api/v1/threads/{tid}/artifact/preview 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 artifact_preview）

### TP-032 · [安全] 线程·审批审核（GET /api/v1/threads/{tid}/artifact/preview）· 安全-鉴权缺失
- 模块：线程 Thread
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-b65000bd` / TP `TP-032`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /api/v1/threads/{tid}/artifact/preview，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 GET /api/v1/threads/{tid}/artifact/preview 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：线程·审批审核 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何线程业务数据；实现参考 artifact_preview）

### TP-033 · [边界] 线程·审批审核（GET /api/v1/threads/{tid}/artifact/preview）· 边界-参数缺失/非法
- 模块：线程 Thread
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-b65000bd` / TP `TP-033`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /api/v1/threads/{tid}/artifact/preview，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 GET /api/v1/threads/{tid}/artifact/preview 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：线程·审批审核 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 artifact_preview）

### TP-034 · [异常] 线程·审批审核（GET /api/v1/threads/{tid}/artifact/preview）· 异常-资源不存在
- 模块：线程 Thread
- 类型：异常　优先级：P1　测试类型：全量
- 关联：FP `FP-b65000bd` / TP `TP-034`
- 前置条件：被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
- 步骤：
  1. [前置] 被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
  2. [准备] 构造请求：GET /api/v1/threads/{tid}/artifact/preview，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 GET /api/v1/threads/{tid}/artifact/preview 请求并捕获响应
  4. [断言] 校验：接口对非法/边界输入返回预期错误（4xx/5xx），且不产生未捕获异常或数据损坏（预期：线程·审批审核 资源不存在：访问不存在或非法的 {id} → 404，提示明确且不暴露内部细节；实现参考 artifact_preview）

### TP-035 · [正常] 对话/会话·对话交互（POST /api/v1/chat）· 正常-可用性
- 模块：对话/会话 Chat
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-56d862c1` / TP `TP-035`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /api/v1/chat，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 POST /api/v1/chat 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：对话/会话·对话交互 功能可用：POST /api/v1/chat 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 chat）

### TP-036 · [安全] 对话/会话·对话交互（POST /api/v1/chat）· 安全-鉴权缺失
- 模块：对话/会话 Chat
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-56d862c1` / TP `TP-036`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /api/v1/chat，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 POST /api/v1/chat 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：对话/会话·对话交互 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何对话/会话业务数据；实现参考 chat）

### TP-037 · [边界] 对话/会话·对话交互（POST /api/v1/chat）· 边界-参数缺失/非法
- 模块：对话/会话 Chat
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-56d862c1` / TP `TP-037`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /api/v1/chat，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 POST /api/v1/chat 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：对话/会话·对话交互 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 chat）

### TP-038 · [正常] 审计/审核看板·提交/创建（POST /mock/config）· 正常-可用性
- 模块：审计/审核看板 Audit
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-0e12e38e` / TP `TP-038`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /mock/config，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 POST /mock/config 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：审计/审核看板·提交/创建 功能可用：POST /mock/config 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 mock_config）

### TP-039 · [安全] 审计/审核看板·提交/创建（POST /mock/config）· 安全-鉴权缺失
- 模块：审计/审核看板 Audit
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-0e12e38e` / TP `TP-039`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /mock/config，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 POST /mock/config 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：审计/审核看板·提交/创建 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何审计/审核看板业务数据；实现参考 mock_config）

### TP-040 · [边界] 审计/审核看板·提交/创建（POST /mock/config）· 边界-参数缺失/非法
- 模块：审计/审核看板 Audit
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-0e12e38e` / TP `TP-040`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /mock/config，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 POST /mock/config 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：审计/审核看板·提交/创建 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 mock_config）

### TP-041 · [正常] 审计/审核看板·查询（GET /mock/state）· 正常-可用性
- 模块：审计/审核看板 Audit
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-2874864c` / TP `TP-041`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /mock/state，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 GET /mock/state 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：审计/审核看板·查询 功能可用：GET /mock/state 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 mock_state）

### TP-042 · [安全] 审计/审核看板·查询（GET /mock/state）· 安全-鉴权缺失
- 模块：审计/审核看板 Audit
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-2874864c` / TP `TP-042`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /mock/state，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 GET /mock/state 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：审计/审核看板·查询 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何审计/审核看板业务数据；实现参考 mock_state）

### TP-043 · [边界] 审计/审核看板·查询（GET /mock/state）· 边界-参数缺失/非法
- 模块：审计/审核看板 Audit
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-2874864c` / TP `TP-043`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /mock/state，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 GET /mock/state 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：审计/审核看板·查询 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 mock_state）

### TP-044 · [正常] 对话/会话·提交/创建（POST /diag-log）· 正常-可用性
- 模块：对话/会话 Chat
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-f74dac84` / TP `TP-044`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /diag-log，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 POST /diag-log 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：对话/会话·提交/创建 功能可用：POST /diag-log 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 diag_log_push）

### TP-045 · [安全] 对话/会话·提交/创建（POST /diag-log）· 安全-鉴权缺失
- 模块：对话/会话 Chat
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-f74dac84` / TP `TP-045`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /diag-log，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 POST /diag-log 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：对话/会话·提交/创建 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何对话/会话业务数据；实现参考 diag_log_push）

### TP-046 · [边界] 对话/会话·提交/创建（POST /diag-log）· 边界-参数缺失/非法
- 模块：对话/会话 Chat
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-f74dac84` / TP `TP-046`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /diag-log，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 POST /diag-log 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：对话/会话·提交/创建 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 diag_log_push）

### TP-047 · [正常] 对话/会话·查询（GET /diag-log）· 正常-可用性
- 模块：对话/会话 Chat
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-d9dc1169` / TP `TP-047`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /diag-log，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 GET /diag-log 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：对话/会话·查询 功能可用：GET /diag-log 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 diag_log_read）

### TP-048 · [安全] 对话/会话·查询（GET /diag-log）· 安全-鉴权缺失
- 模块：对话/会话 Chat
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-d9dc1169` / TP `TP-048`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /diag-log，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 GET /diag-log 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：对话/会话·查询 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何对话/会话业务数据；实现参考 diag_log_read）

### TP-049 · [边界] 对话/会话·查询（GET /diag-log）· 边界-参数缺失/非法
- 模块：对话/会话 Chat
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-d9dc1169` / TP `TP-049`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /diag-log，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 GET /diag-log 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：对话/会话·查询 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 diag_log_read）

### TP-050 · [正常] 健康/其它·健康检查（GET /api/v1/health）· 正常-可用性
- 模块：健康/其它
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-85b27ee2` / TP `TP-050`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /api/v1/health，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 GET /api/v1/health 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：健康/其它·健康检查 功能可用：GET /api/v1/health 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 health）

### TP-051 · [安全] 健康/其它·健康检查（GET /api/v1/health）· 安全-鉴权缺失
- 模块：健康/其它
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-85b27ee2` / TP `TP-051`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /api/v1/health，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 GET /api/v1/health 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：健康/其它·健康检查 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何健康/其它业务数据；实现参考 health）

### TP-052 · [边界] 健康/其它·健康检查（GET /api/v1/health）· 边界-参数缺失/非法
- 模块：健康/其它
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-85b27ee2` / TP `TP-052`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /api/v1/health，来源文件 frontend/mock-server/server.py
  3. [执行] 发送 GET /api/v1/health 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：健康/其它·健康检查 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 health）

### TP-053 · [正常] 产物/文档·产物文档（GET /document）· 正常-可用性
- 模块：产物/文档 Artifact
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-c0ed59cb` / TP `TP-053`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /document，来源文件 backend/research-agent-source/tools/audit_kb/api.py
  3. [执行] 发送 GET /document 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：产物/文档·产物文档 功能可用：GET /document 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 get_audit_kb_document）

### TP-054 · [安全] 产物/文档·产物文档（GET /document）· 安全-鉴权缺失
- 模块：产物/文档 Artifact
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-c0ed59cb` / TP `TP-054`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /document，来源文件 backend/research-agent-source/tools/audit_kb/api.py
  3. [执行] 发送 GET /document 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：产物/文档·产物文档 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何产物/文档业务数据；实现参考 get_audit_kb_document）

### TP-055 · [边界] 产物/文档·产物文档（GET /document）· 边界-参数缺失/非法
- 模块：产物/文档 Artifact
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-c0ed59cb` / TP `TP-055`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /document，来源文件 backend/research-agent-source/tools/audit_kb/api.py
  3. [执行] 发送 GET /document 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：产物/文档·产物文档 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 get_audit_kb_document）

### TP-056 · [正常] 产物/文档·产物文档（GET /document_info）· 正常-可用性
- 模块：产物/文档 Artifact
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-720a39fc` / TP `TP-056`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /document_info，来源文件 backend/research-agent-source/tools/audit_kb/api.py
  3. [执行] 发送 GET /document_info 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：产物/文档·产物文档 功能可用：GET /document_info 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 get_audit_kb_document_info：返回文件元信息（类型、总页数）。轻量、不渲染大内容。）

### TP-057 · [安全] 产物/文档·产物文档（GET /document_info）· 安全-鉴权缺失
- 模块：产物/文档 Artifact
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-720a39fc` / TP `TP-057`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /document_info，来源文件 backend/research-agent-source/tools/audit_kb/api.py
  3. [执行] 发送 GET /document_info 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：产物/文档·产物文档 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何产物/文档业务数据；实现参考 get_audit_kb_document_info：返回文件元信息（类型、总页数）。轻量、不渲染大内容。）

### TP-058 · [边界] 产物/文档·产物文档（GET /document_info）· 边界-参数缺失/非法
- 模块：产物/文档 Artifact
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-720a39fc` / TP `TP-058`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /document_info，来源文件 backend/research-agent-source/tools/audit_kb/api.py
  3. [执行] 发送 GET /document_info 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：产物/文档·产物文档 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 get_audit_kb_document_info：返回文件元信息（类型、总页数）。轻量、不渲染大内容。）

### TP-059 · [正常] 审计/审核看板·检索查询（GET /regulations/search）· 正常-可用性
- 模块：审计/审核看板 Audit
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-6b26c560` / TP `TP-059`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /regulations/search，来源文件 backend/research-agent-source/tools/audit_kb/api.py
  3. [执行] 发送 GET /regulations/search 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：审计/审核看板·检索查询 功能可用：GET /regulations/search 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 search_regulations_for_replacement：废止 chunk「查看现行版本」跳转用。）

### TP-060 · [安全] 审计/审核看板·检索查询（GET /regulations/search）· 安全-鉴权缺失
- 模块：审计/审核看板 Audit
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-6b26c560` / TP `TP-060`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /regulations/search，来源文件 backend/research-agent-source/tools/audit_kb/api.py
  3. [执行] 发送 GET /regulations/search 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：审计/审核看板·检索查询 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何审计/审核看板业务数据；实现参考 search_regulations_for_replacement：废止 chunk「查看现行版本」跳转用。）

### TP-061 · [边界] 审计/审核看板·检索查询（GET /regulations/search）· 边界-参数缺失/非法
- 模块：审计/审核看板 Audit
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-6b26c560` / TP `TP-061`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /regulations/search，来源文件 backend/research-agent-source/tools/audit_kb/api.py
  3. [执行] 发送 GET /regulations/search 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：审计/审核看板·检索查询 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 search_regulations_for_replacement：废止 chunk「查看现行版本」跳转用。）

### TP-062 · [正常] 审计/审核看板·审批审核（GET /pending/count）· 正常-可用性
- 模块：审计/审核看板 Audit
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-99cc9204` / TP `TP-062`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /pending/count，来源文件 backend/research-agent-source/tools/audit_kb_admin/admin_api.py
  3. [执行] 发送 GET /pending/count 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：审计/审核看板·审批审核 功能可用：GET /pending/count 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 pending_count：返回待处理任务数量，供前端任务红点 badge 使用。）

### TP-063 · [安全] 审计/审核看板·审批审核（GET /pending/count）· 安全-鉴权缺失
- 模块：审计/审核看板 Audit
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-99cc9204` / TP `TP-063`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /pending/count，来源文件 backend/research-agent-source/tools/audit_kb_admin/admin_api.py
  3. [执行] 发送 GET /pending/count 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：审计/审核看板·审批审核 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何审计/审核看板业务数据；实现参考 pending_count：返回待处理任务数量，供前端任务红点 badge 使用。）

### TP-064 · [边界] 审计/审核看板·审批审核（GET /pending/count）· 边界-参数缺失/非法
- 模块：审计/审核看板 Audit
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-99cc9204` / TP `TP-064`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /pending/count，来源文件 backend/research-agent-source/tools/audit_kb_admin/admin_api.py
  3. [执行] 发送 GET /pending/count 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：审计/审核看板·审批审核 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 pending_count：返回待处理任务数量，供前端任务红点 badge 使用。）

### TP-065 · [正常] 审计/审核看板·审批审核（GET /pending）· 正常-可用性
- 模块：审计/审核看板 Audit
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-df3b362f` / TP `TP-065`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /pending，来源文件 backend/research-agent-source/tools/audit_kb_admin/admin_api.py
  3. [执行] 发送 GET /pending 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：审计/审核看板·审批审核 功能可用：GET /pending 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 list_pending：列出待处理任务。）

### TP-066 · [安全] 审计/审核看板·审批审核（GET /pending）· 安全-鉴权缺失
- 模块：审计/审核看板 Audit
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-df3b362f` / TP `TP-066`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /pending，来源文件 backend/research-agent-source/tools/audit_kb_admin/admin_api.py
  3. [执行] 发送 GET /pending 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：审计/审核看板·审批审核 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何审计/审核看板业务数据；实现参考 list_pending：列出待处理任务。）

### TP-067 · [边界] 审计/审核看板·审批审核（GET /pending）· 边界-参数缺失/非法
- 模块：审计/审核看板 Audit
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-df3b362f` / TP `TP-067`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /pending，来源文件 backend/research-agent-source/tools/audit_kb_admin/admin_api.py
  3. [执行] 发送 GET /pending 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：审计/审核看板·审批审核 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 list_pending：列出待处理任务。）

### TP-068 · [正常] 审计/审核看板·审批审核（POST /pending/{task_id}/confirm）· 正常-可用性
- 模块：审计/审核看板 Audit
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-13621e82` / TP `TP-068`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /pending/{task_id}/confirm，来源文件 backend/research-agent-source/tools/audit_kb_admin/admin_api.py
  3. [执行] 发送 POST /pending/{task_id}/confirm 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：审计/审核看板·审批审核 功能可用：POST /pending/{task_id}/confirm 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 confirm_pending：审计老师确认任务（废止核验 / 政策查阅）。）

### TP-069 · [安全] 审计/审核看板·审批审核（POST /pending/{task_id}/confirm）· 安全-鉴权缺失
- 模块：审计/审核看板 Audit
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-13621e82` / TP `TP-069`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /pending/{task_id}/confirm，来源文件 backend/research-agent-source/tools/audit_kb_admin/admin_api.py
  3. [执行] 发送 POST /pending/{task_id}/confirm 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：审计/审核看板·审批审核 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何审计/审核看板业务数据；实现参考 confirm_pending：审计老师确认任务（废止核验 / 政策查阅）。）

### TP-070 · [边界] 审计/审核看板·审批审核（POST /pending/{task_id}/confirm）· 边界-参数缺失/非法
- 模块：审计/审核看板 Audit
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-13621e82` / TP `TP-070`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /pending/{task_id}/confirm，来源文件 backend/research-agent-source/tools/audit_kb_admin/admin_api.py
  3. [执行] 发送 POST /pending/{task_id}/confirm 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：审计/审核看板·审批审核 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 confirm_pending：审计老师确认任务（废止核验 / 政策查阅）。）

### TP-071 · [异常] 审计/审核看板·审批审核（POST /pending/{task_id}/confirm）· 异常-资源不存在
- 模块：审计/审核看板 Audit
- 类型：异常　优先级：P1　测试类型：全量
- 关联：FP `FP-13621e82` / TP `TP-071`
- 前置条件：被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
- 步骤：
  1. [前置] 被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
  2. [准备] 构造请求：POST /pending/{task_id}/confirm，来源文件 backend/research-agent-source/tools/audit_kb_admin/admin_api.py
  3. [执行] 发送 POST /pending/{task_id}/confirm 请求并捕获响应
  4. [断言] 校验：接口对非法/边界输入返回预期错误（4xx/5xx），且不产生未捕获异常或数据损坏（预期：审计/审核看板·审批审核 资源不存在：访问不存在或非法的 {id} → 404，提示明确且不暴露内部细节；实现参考 confirm_pending：审计老师确认任务（废止核验 / 政策查阅）。）

### TP-072 · [正常] 审计/审核看板·审批审核（POST /pending/{task_id}/dismiss）· 正常-可用性
- 模块：审计/审核看板 Audit
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-a63a8123` / TP `TP-072`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /pending/{task_id}/dismiss，来源文件 backend/research-agent-source/tools/audit_kb_admin/admin_api.py
  3. [执行] 发送 POST /pending/{task_id}/dismiss 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：审计/审核看板·审批审核 功能可用：POST /pending/{task_id}/dismiss 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 dismiss_pending：审计老师驳回/忽略任务。）

### TP-073 · [安全] 审计/审核看板·审批审核（POST /pending/{task_id}/dismiss）· 安全-鉴权缺失
- 模块：审计/审核看板 Audit
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-a63a8123` / TP `TP-073`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /pending/{task_id}/dismiss，来源文件 backend/research-agent-source/tools/audit_kb_admin/admin_api.py
  3. [执行] 发送 POST /pending/{task_id}/dismiss 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：审计/审核看板·审批审核 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何审计/审核看板业务数据；实现参考 dismiss_pending：审计老师驳回/忽略任务。）

### TP-074 · [边界] 审计/审核看板·审批审核（POST /pending/{task_id}/dismiss）· 边界-参数缺失/非法
- 模块：审计/审核看板 Audit
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-a63a8123` / TP `TP-074`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /pending/{task_id}/dismiss，来源文件 backend/research-agent-source/tools/audit_kb_admin/admin_api.py
  3. [执行] 发送 POST /pending/{task_id}/dismiss 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：审计/审核看板·审批审核 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 dismiss_pending：审计老师驳回/忽略任务。）

### TP-075 · [异常] 审计/审核看板·审批审核（POST /pending/{task_id}/dismiss）· 异常-资源不存在
- 模块：审计/审核看板 Audit
- 类型：异常　优先级：P1　测试类型：全量
- 关联：FP `FP-a63a8123` / TP `TP-075`
- 前置条件：被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
- 步骤：
  1. [前置] 被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
  2. [准备] 构造请求：POST /pending/{task_id}/dismiss，来源文件 backend/research-agent-source/tools/audit_kb_admin/admin_api.py
  3. [执行] 发送 POST /pending/{task_id}/dismiss 请求并捕获响应
  4. [断言] 校验：接口对非法/边界输入返回预期错误（4xx/5xx），且不产生未捕获异常或数据损坏（预期：审计/审核看板·审批审核 资源不存在：访问不存在或非法的 {id} → 404，提示明确且不暴露内部细节；实现参考 dismiss_pending：审计老师驳回/忽略任务。）

### TP-076 · [正常] 产物/文档·产物文档（GET /documents）· 正常-可用性
- 模块：产物/文档 Artifact
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-695b8ad8` / TP `TP-076`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /documents，来源文件 backend/research-agent-source/tools/audit_kb_admin/admin_api.py
  3. [执行] 发送 GET /documents 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：产物/文档·产物文档 功能可用：GET /documents 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 list_documents：列出知识库文件清单（读现有 audit_kb sqlite）。）

### TP-077 · [安全] 产物/文档·产物文档（GET /documents）· 安全-鉴权缺失
- 模块：产物/文档 Artifact
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-695b8ad8` / TP `TP-077`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /documents，来源文件 backend/research-agent-source/tools/audit_kb_admin/admin_api.py
  3. [执行] 发送 GET /documents 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：产物/文档·产物文档 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何产物/文档业务数据；实现参考 list_documents：列出知识库文件清单（读现有 audit_kb sqlite）。）

### TP-078 · [边界] 产物/文档·产物文档（GET /documents）· 边界-参数缺失/非法
- 模块：产物/文档 Artifact
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-695b8ad8` / TP `TP-078`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /documents，来源文件 backend/research-agent-source/tools/audit_kb_admin/admin_api.py
  3. [执行] 发送 GET /documents 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：产物/文档·产物文档 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 list_documents：列出知识库文件清单（读现有 audit_kb sqlite）。）

### TP-079 · [正常] 产物/文档·产物文档（GET /documents/{src_id}/content）· 正常-可用性
- 模块：产物/文档 Artifact
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-e245cd13` / TP `TP-079`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /documents/{src_id}/content，来源文件 backend/research-agent-source/tools/audit_kb_admin/admin_api.py
  3. [执行] 发送 GET /documents/{src_id}/content 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：产物/文档·产物文档 功能可用：GET /documents/{src_id}/content 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 document_content：直接读取知识库数据库中的文档内容（用于无物理文件的案例预览）。）

### TP-080 · [安全] 产物/文档·产物文档（GET /documents/{src_id}/content）· 安全-鉴权缺失
- 模块：产物/文档 Artifact
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-e245cd13` / TP `TP-080`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /documents/{src_id}/content，来源文件 backend/research-agent-source/tools/audit_kb_admin/admin_api.py
  3. [执行] 发送 GET /documents/{src_id}/content 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：产物/文档·产物文档 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何产物/文档业务数据；实现参考 document_content：直接读取知识库数据库中的文档内容（用于无物理文件的案例预览）。）

### TP-081 · [边界] 产物/文档·产物文档（GET /documents/{src_id}/content）· 边界-参数缺失/非法
- 模块：产物/文档 Artifact
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-e245cd13` / TP `TP-081`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /documents/{src_id}/content，来源文件 backend/research-agent-source/tools/audit_kb_admin/admin_api.py
  3. [执行] 发送 GET /documents/{src_id}/content 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：产物/文档·产物文档 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 document_content：直接读取知识库数据库中的文档内容（用于无物理文件的案例预览）。）

### TP-082 · [异常] 产物/文档·产物文档（GET /documents/{src_id}/content）· 异常-资源不存在
- 模块：产物/文档 Artifact
- 类型：异常　优先级：P1　测试类型：全量
- 关联：FP `FP-e245cd13` / TP `TP-082`
- 前置条件：被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
- 步骤：
  1. [前置] 被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
  2. [准备] 构造请求：GET /documents/{src_id}/content，来源文件 backend/research-agent-source/tools/audit_kb_admin/admin_api.py
  3. [执行] 发送 GET /documents/{src_id}/content 请求并捕获响应
  4. [断言] 校验：接口对非法/边界输入返回预期错误（4xx/5xx），且不产生未捕获异常或数据损坏（预期：产物/文档·产物文档 资源不存在：访问不存在或非法的 {id} → 404，提示明确且不暴露内部细节；实现参考 document_content：直接读取知识库数据库中的文档内容（用于无物理文件的案例预览）。）

### TP-083 · [正常] 产物/文档·产物文档（GET /documents/{src_id}/diff）· 正常-可用性
- 模块：产物/文档 Artifact
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-326f35f8` / TP `TP-083`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /documents/{src_id}/diff，来源文件 backend/research-agent-source/tools/audit_kb_admin/admin_api.py
  3. [执行] 发送 GET /documents/{src_id}/diff 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：产物/文档·产物文档 功能可用：GET /documents/{src_id}/diff 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 document_diff：版本比对：返回段落级 diff（当前实现返回全文，前端做段落比对）。）

### TP-084 · [安全] 产物/文档·产物文档（GET /documents/{src_id}/diff）· 安全-鉴权缺失
- 模块：产物/文档 Artifact
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-326f35f8` / TP `TP-084`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /documents/{src_id}/diff，来源文件 backend/research-agent-source/tools/audit_kb_admin/admin_api.py
  3. [执行] 发送 GET /documents/{src_id}/diff 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：产物/文档·产物文档 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何产物/文档业务数据；实现参考 document_diff：版本比对：返回段落级 diff（当前实现返回全文，前端做段落比对）。）

### TP-085 · [边界] 产物/文档·产物文档（GET /documents/{src_id}/diff）· 边界-参数缺失/非法
- 模块：产物/文档 Artifact
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-326f35f8` / TP `TP-085`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /documents/{src_id}/diff，来源文件 backend/research-agent-source/tools/audit_kb_admin/admin_api.py
  3. [执行] 发送 GET /documents/{src_id}/diff 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：产物/文档·产物文档 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 document_diff：版本比对：返回段落级 diff（当前实现返回全文，前端做段落比对）。）

### TP-086 · [异常] 产物/文档·产物文档（GET /documents/{src_id}/diff）· 异常-资源不存在
- 模块：产物/文档 Artifact
- 类型：异常　优先级：P1　测试类型：全量
- 关联：FP `FP-326f35f8` / TP `TP-086`
- 前置条件：被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
- 步骤：
  1. [前置] 被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
  2. [准备] 构造请求：GET /documents/{src_id}/diff，来源文件 backend/research-agent-source/tools/audit_kb_admin/admin_api.py
  3. [执行] 发送 GET /documents/{src_id}/diff 请求并捕获响应
  4. [断言] 校验：接口对非法/边界输入返回预期错误（4xx/5xx），且不产生未捕获异常或数据损坏（预期：产物/文档·产物文档 资源不存在：访问不存在或非法的 {id} → 404，提示明确且不暴露内部细节；实现参考 document_diff：版本比对：返回段落级 diff（当前实现返回全文，前端做段落比对）。）

### TP-087 · [正常] 审计/审核看板·查询（GET /logs）· 正常-可用性
- 模块：审计/审核看板 Audit
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-ad480b34` / TP `TP-087`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /logs，来源文件 backend/research-agent-source/tools/audit_kb_admin/admin_api.py
  3. [执行] 发送 GET /logs 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：审计/审核看板·查询 功能可用：GET /logs 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 list_logs：审计日志查询。）

### TP-088 · [安全] 审计/审核看板·查询（GET /logs）· 安全-鉴权缺失
- 模块：审计/审核看板 Audit
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-ad480b34` / TP `TP-088`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /logs，来源文件 backend/research-agent-source/tools/audit_kb_admin/admin_api.py
  3. [执行] 发送 GET /logs 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：审计/审核看板·查询 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何审计/审核看板业务数据；实现参考 list_logs：审计日志查询。）

### TP-089 · [边界] 审计/审核看板·查询（GET /logs）· 边界-参数缺失/非法
- 模块：审计/审核看板 Audit
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-ad480b34` / TP `TP-089`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /logs，来源文件 backend/research-agent-source/tools/audit_kb_admin/admin_api.py
  3. [执行] 发送 GET /logs 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：审计/审核看板·查询 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 list_logs：审计日志查询。）

### TP-090 · [正常] 账户/用户/鉴权·提交/创建（POST /users）· 正常-可用性
- 模块：账户/用户/鉴权 Auth
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-560839ff` / TP `TP-090`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /users，来源文件 backend/research-agent-source/tools/auth/admin_routes.py
  3. [执行] 发送 POST /users 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·提交/创建 功能可用：POST /users 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 create_user：新建 user。）

### TP-091 · [安全] 账户/用户/鉴权·提交/创建（POST /users）· 安全-鉴权缺失
- 模块：账户/用户/鉴权 Auth
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-560839ff` / TP `TP-091`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /users，来源文件 backend/research-agent-source/tools/auth/admin_routes.py
  3. [执行] 发送 POST /users 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·提交/创建 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何账户/用户/鉴权业务数据；实现参考 create_user：新建 user。）

### TP-092 · [边界] 账户/用户/鉴权·提交/创建（POST /users）· 边界-参数缺失/非法
- 模块：账户/用户/鉴权 Auth
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-560839ff` / TP `TP-092`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /users，来源文件 backend/research-agent-source/tools/auth/admin_routes.py
  3. [执行] 发送 POST /users 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·提交/创建 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 create_user：新建 user。）

### TP-093 · [正常] 账户/用户/鉴权·查询（GET /users）· 正常-可用性
- 模块：账户/用户/鉴权 Auth
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-0ac402e0` / TP `TP-093`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /users，来源文件 backend/research-agent-source/tools/auth/admin_routes.py
  3. [执行] 发送 GET /users 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·查询 功能可用：GET /users 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 list_users：列 user。）

### TP-094 · [安全] 账户/用户/鉴权·查询（GET /users）· 安全-鉴权缺失
- 模块：账户/用户/鉴权 Auth
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-0ac402e0` / TP `TP-094`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /users，来源文件 backend/research-agent-source/tools/auth/admin_routes.py
  3. [执行] 发送 GET /users 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·查询 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何账户/用户/鉴权业务数据；实现参考 list_users：列 user。）

### TP-095 · [边界] 账户/用户/鉴权·查询（GET /users）· 边界-参数缺失/非法
- 模块：账户/用户/鉴权 Auth
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-0ac402e0` / TP `TP-095`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /users，来源文件 backend/research-agent-source/tools/auth/admin_routes.py
  3. [执行] 发送 GET /users 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·查询 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 list_users：列 user。）

### TP-096 · [正常] 账户/用户/鉴权·部分更新（PATCH /users/{user_id}）· 正常-可用性
- 模块：账户/用户/鉴权 Auth
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-78327682` / TP `TP-096`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：PATCH /users/{user_id}，来源文件 backend/research-agent-source/tools/auth/admin_routes.py
  3. [执行] 发送 PATCH /users/{user_id} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·部分更新 功能可用：PATCH /users/{user_id} 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 patch_user：改 is_admin / status / password。）

### TP-097 · [安全] 账户/用户/鉴权·部分更新（PATCH /users/{user_id}）· 安全-鉴权缺失
- 模块：账户/用户/鉴权 Auth
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-78327682` / TP `TP-097`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：PATCH /users/{user_id}，来源文件 backend/research-agent-source/tools/auth/admin_routes.py
  3. [执行] 发送 PATCH /users/{user_id} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·部分更新 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何账户/用户/鉴权业务数据；实现参考 patch_user：改 is_admin / status / password。）

### TP-098 · [边界] 账户/用户/鉴权·部分更新（PATCH /users/{user_id}）· 边界-参数缺失/非法
- 模块：账户/用户/鉴权 Auth
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-78327682` / TP `TP-098`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：PATCH /users/{user_id}，来源文件 backend/research-agent-source/tools/auth/admin_routes.py
  3. [执行] 发送 PATCH /users/{user_id} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·部分更新 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 patch_user：改 is_admin / status / password。）

### TP-099 · [异常] 账户/用户/鉴权·部分更新（PATCH /users/{user_id}）· 异常-资源不存在
- 模块：账户/用户/鉴权 Auth
- 类型：异常　优先级：P1　测试类型：全量
- 关联：FP `FP-78327682` / TP `TP-099`
- 前置条件：被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
- 步骤：
  1. [前置] 被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
  2. [准备] 构造请求：PATCH /users/{user_id}，来源文件 backend/research-agent-source/tools/auth/admin_routes.py
  3. [执行] 发送 PATCH /users/{user_id} 请求并捕获响应
  4. [断言] 校验：接口对非法/边界输入返回预期错误（4xx/5xx），且不产生未捕获异常或数据损坏（预期：账户/用户/鉴权·部分更新 资源不存在：访问不存在或非法的 {id} → 404，提示明确且不暴露内部细节；实现参考 patch_user：改 is_admin / status / password。）

### TP-100 · [安全] 账户/用户/鉴权·部分更新（PATCH /users/{user_id}）· 安全-越权
- 模块：账户/用户/鉴权 Auth
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-78327682` / TP `TP-100`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：PATCH /users/{user_id}，来源文件 backend/research-agent-source/tools/auth/admin_routes.py
  3. [执行] 发送 PATCH /users/{user_id} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·部分更新 越权防护：操作他人资源 → 403，不产生越权修改；实现参考 patch_user：改 is_admin / status / password。）

### TP-101 · [正常] 账户/用户/鉴权·删除（DELETE /users/{user_id}）· 正常-可用性
- 模块：账户/用户/鉴权 Auth
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-49b47738` / TP `TP-101`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：DELETE /users/{user_id}，来源文件 backend/research-agent-source/tools/auth/admin_routes.py
  3. [执行] 发送 DELETE /users/{user_id} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·删除 功能可用：DELETE /users/{user_id} 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 delete_user：删除 user。admin 不能删自己。）

### TP-102 · [安全] 账户/用户/鉴权·删除（DELETE /users/{user_id}）· 安全-鉴权缺失
- 模块：账户/用户/鉴权 Auth
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-49b47738` / TP `TP-102`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：DELETE /users/{user_id}，来源文件 backend/research-agent-source/tools/auth/admin_routes.py
  3. [执行] 发送 DELETE /users/{user_id} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·删除 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何账户/用户/鉴权业务数据；实现参考 delete_user：删除 user。admin 不能删自己。）

### TP-103 · [边界] 账户/用户/鉴权·删除（DELETE /users/{user_id}）· 边界-参数缺失/非法
- 模块：账户/用户/鉴权 Auth
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-49b47738` / TP `TP-103`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：DELETE /users/{user_id}，来源文件 backend/research-agent-source/tools/auth/admin_routes.py
  3. [执行] 发送 DELETE /users/{user_id} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·删除 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 delete_user：删除 user。admin 不能删自己。）

### TP-104 · [异常] 账户/用户/鉴权·删除（DELETE /users/{user_id}）· 异常-资源不存在
- 模块：账户/用户/鉴权 Auth
- 类型：异常　优先级：P1　测试类型：全量
- 关联：FP `FP-49b47738` / TP `TP-104`
- 前置条件：被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
- 步骤：
  1. [前置] 被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
  2. [准备] 构造请求：DELETE /users/{user_id}，来源文件 backend/research-agent-source/tools/auth/admin_routes.py
  3. [执行] 发送 DELETE /users/{user_id} 请求并捕获响应
  4. [断言] 校验：接口对非法/边界输入返回预期错误（4xx/5xx），且不产生未捕获异常或数据损坏（预期：账户/用户/鉴权·删除 资源不存在：访问不存在或非法的 {id} → 404，提示明确且不暴露内部细节；实现参考 delete_user：删除 user。admin 不能删自己。）

### TP-105 · [安全] 账户/用户/鉴权·删除（DELETE /users/{user_id}）· 安全-越权
- 模块：账户/用户/鉴权 Auth
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-49b47738` / TP `TP-105`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：DELETE /users/{user_id}，来源文件 backend/research-agent-source/tools/auth/admin_routes.py
  3. [执行] 发送 DELETE /users/{user_id} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·删除 越权防护：操作他人资源 → 403，不产生越权修改；实现参考 delete_user：删除 user。admin 不能删自己。）

### TP-106 · [正常] 账户/用户/鉴权·查询（GET /me）· 正常-可用性
- 模块：账户/用户/鉴权 Auth
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-56627f76` / TP `TP-106`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /me，来源文件 backend/research-agent-source/tools/auth/rbac.py
  3. [执行] 发送 GET /me 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·查询 功能可用：GET /me 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 my_permissions）

### TP-107 · [安全] 账户/用户/鉴权·查询（GET /me）· 安全-鉴权缺失
- 模块：账户/用户/鉴权 Auth
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-56627f76` / TP `TP-107`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /me，来源文件 backend/research-agent-source/tools/auth/rbac.py
  3. [执行] 发送 GET /me 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·查询 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何账户/用户/鉴权业务数据；实现参考 my_permissions）

### TP-108 · [边界] 账户/用户/鉴权·查询（GET /me）· 边界-参数缺失/非法
- 模块：账户/用户/鉴权 Auth
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-56627f76` / TP `TP-108`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /me，来源文件 backend/research-agent-source/tools/auth/rbac.py
  3. [执行] 发送 GET /me 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·查询 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 my_permissions）

### TP-109 · [正常] 审计/审核看板·查询（GET /catalog）· 正常-可用性
- 模块：审计/审核看板 Audit
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-3d7331e6` / TP `TP-109`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /catalog，来源文件 backend/research-agent-source/tools/auth/rbac.py
  3. [执行] 发送 GET /catalog 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：审计/审核看板·查询 功能可用：GET /catalog 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 catalog）

### TP-110 · [安全] 审计/审核看板·查询（GET /catalog）· 安全-鉴权缺失
- 模块：审计/审核看板 Audit
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-3d7331e6` / TP `TP-110`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /catalog，来源文件 backend/research-agent-source/tools/auth/rbac.py
  3. [执行] 发送 GET /catalog 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：审计/审核看板·查询 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何审计/审核看板业务数据；实现参考 catalog）

### TP-111 · [边界] 审计/审核看板·查询（GET /catalog）· 边界-参数缺失/非法
- 模块：审计/审核看板 Audit
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-3d7331e6` / TP `TP-111`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /catalog，来源文件 backend/research-agent-source/tools/auth/rbac.py
  3. [执行] 发送 GET /catalog 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：审计/审核看板·查询 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 catalog）

### TP-112 · [正常] 账户/用户/鉴权·查询（GET /roles）· 正常-可用性
- 模块：账户/用户/鉴权 Auth
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-d4811a98` / TP `TP-112`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /roles，来源文件 backend/research-agent-source/tools/auth/rbac.py
  3. [执行] 发送 GET /roles 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·查询 功能可用：GET /roles 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 list_roles）

### TP-113 · [安全] 账户/用户/鉴权·查询（GET /roles）· 安全-鉴权缺失
- 模块：账户/用户/鉴权 Auth
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-d4811a98` / TP `TP-113`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /roles，来源文件 backend/research-agent-source/tools/auth/rbac.py
  3. [执行] 发送 GET /roles 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·查询 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何账户/用户/鉴权业务数据；实现参考 list_roles）

### TP-114 · [边界] 账户/用户/鉴权·查询（GET /roles）· 边界-参数缺失/非法
- 模块：账户/用户/鉴权 Auth
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-d4811a98` / TP `TP-114`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /roles，来源文件 backend/research-agent-source/tools/auth/rbac.py
  3. [执行] 发送 GET /roles 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·查询 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 list_roles）

### TP-115 · [正常] 账户/用户/鉴权·提交/创建（POST /roles）· 正常-可用性
- 模块：账户/用户/鉴权 Auth
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-1cdb3157` / TP `TP-115`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /roles，来源文件 backend/research-agent-source/tools/auth/rbac.py
  3. [执行] 发送 POST /roles 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·提交/创建 功能可用：POST /roles 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 create_role）

### TP-116 · [安全] 账户/用户/鉴权·提交/创建（POST /roles）· 安全-鉴权缺失
- 模块：账户/用户/鉴权 Auth
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-1cdb3157` / TP `TP-116`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /roles，来源文件 backend/research-agent-source/tools/auth/rbac.py
  3. [执行] 发送 POST /roles 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·提交/创建 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何账户/用户/鉴权业务数据；实现参考 create_role）

### TP-117 · [边界] 账户/用户/鉴权·提交/创建（POST /roles）· 边界-参数缺失/非法
- 模块：账户/用户/鉴权 Auth
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-1cdb3157` / TP `TP-117`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /roles，来源文件 backend/research-agent-source/tools/auth/rbac.py
  3. [执行] 发送 POST /roles 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·提交/创建 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 create_role）

### TP-118 · [正常] 账户/用户/鉴权·更新（PUT /roles/{role_id}）· 正常-可用性
- 模块：账户/用户/鉴权 Auth
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-194b0998` / TP `TP-118`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：PUT /roles/{role_id}，来源文件 backend/research-agent-source/tools/auth/rbac.py
  3. [执行] 发送 PUT /roles/{role_id} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·更新 功能可用：PUT /roles/{role_id} 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 update_role）

### TP-119 · [安全] 账户/用户/鉴权·更新（PUT /roles/{role_id}）· 安全-鉴权缺失
- 模块：账户/用户/鉴权 Auth
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-194b0998` / TP `TP-119`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：PUT /roles/{role_id}，来源文件 backend/research-agent-source/tools/auth/rbac.py
  3. [执行] 发送 PUT /roles/{role_id} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·更新 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何账户/用户/鉴权业务数据；实现参考 update_role）

### TP-120 · [边界] 账户/用户/鉴权·更新（PUT /roles/{role_id}）· 边界-参数缺失/非法
- 模块：账户/用户/鉴权 Auth
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-194b0998` / TP `TP-120`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：PUT /roles/{role_id}，来源文件 backend/research-agent-source/tools/auth/rbac.py
  3. [执行] 发送 PUT /roles/{role_id} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·更新 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 update_role）

### TP-121 · [异常] 账户/用户/鉴权·更新（PUT /roles/{role_id}）· 异常-资源不存在
- 模块：账户/用户/鉴权 Auth
- 类型：异常　优先级：P1　测试类型：全量
- 关联：FP `FP-194b0998` / TP `TP-121`
- 前置条件：被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
- 步骤：
  1. [前置] 被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
  2. [准备] 构造请求：PUT /roles/{role_id}，来源文件 backend/research-agent-source/tools/auth/rbac.py
  3. [执行] 发送 PUT /roles/{role_id} 请求并捕获响应
  4. [断言] 校验：接口对非法/边界输入返回预期错误（4xx/5xx），且不产生未捕获异常或数据损坏（预期：账户/用户/鉴权·更新 资源不存在：访问不存在或非法的 {id} → 404，提示明确且不暴露内部细节；实现参考 update_role）

### TP-122 · [安全] 账户/用户/鉴权·更新（PUT /roles/{role_id}）· 安全-越权
- 模块：账户/用户/鉴权 Auth
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-194b0998` / TP `TP-122`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：PUT /roles/{role_id}，来源文件 backend/research-agent-source/tools/auth/rbac.py
  3. [执行] 发送 PUT /roles/{role_id} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·更新 越权防护：操作他人资源 → 403，不产生越权修改；实现参考 update_role）

### TP-123 · [正常] 账户/用户/鉴权·删除（DELETE /roles/{role_id}）· 正常-可用性
- 模块：账户/用户/鉴权 Auth
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-2eaeabc3` / TP `TP-123`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：DELETE /roles/{role_id}，来源文件 backend/research-agent-source/tools/auth/rbac.py
  3. [执行] 发送 DELETE /roles/{role_id} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·删除 功能可用：DELETE /roles/{role_id} 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 delete_role：仅允许删除自定义角色；两个系统角色始终保留。）

### TP-124 · [安全] 账户/用户/鉴权·删除（DELETE /roles/{role_id}）· 安全-鉴权缺失
- 模块：账户/用户/鉴权 Auth
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-2eaeabc3` / TP `TP-124`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：DELETE /roles/{role_id}，来源文件 backend/research-agent-source/tools/auth/rbac.py
  3. [执行] 发送 DELETE /roles/{role_id} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·删除 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何账户/用户/鉴权业务数据；实现参考 delete_role：仅允许删除自定义角色；两个系统角色始终保留。）

### TP-125 · [边界] 账户/用户/鉴权·删除（DELETE /roles/{role_id}）· 边界-参数缺失/非法
- 模块：账户/用户/鉴权 Auth
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-2eaeabc3` / TP `TP-125`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：DELETE /roles/{role_id}，来源文件 backend/research-agent-source/tools/auth/rbac.py
  3. [执行] 发送 DELETE /roles/{role_id} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·删除 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 delete_role：仅允许删除自定义角色；两个系统角色始终保留。）

### TP-126 · [异常] 账户/用户/鉴权·删除（DELETE /roles/{role_id}）· 异常-资源不存在
- 模块：账户/用户/鉴权 Auth
- 类型：异常　优先级：P1　测试类型：全量
- 关联：FP `FP-2eaeabc3` / TP `TP-126`
- 前置条件：被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
- 步骤：
  1. [前置] 被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
  2. [准备] 构造请求：DELETE /roles/{role_id}，来源文件 backend/research-agent-source/tools/auth/rbac.py
  3. [执行] 发送 DELETE /roles/{role_id} 请求并捕获响应
  4. [断言] 校验：接口对非法/边界输入返回预期错误（4xx/5xx），且不产生未捕获异常或数据损坏（预期：账户/用户/鉴权·删除 资源不存在：访问不存在或非法的 {id} → 404，提示明确且不暴露内部细节；实现参考 delete_role：仅允许删除自定义角色；两个系统角色始终保留。）

### TP-127 · [安全] 账户/用户/鉴权·删除（DELETE /roles/{role_id}）· 安全-越权
- 模块：账户/用户/鉴权 Auth
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-2eaeabc3` / TP `TP-127`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：DELETE /roles/{role_id}，来源文件 backend/research-agent-source/tools/auth/rbac.py
  3. [执行] 发送 DELETE /roles/{role_id} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·删除 越权防护：操作他人资源 → 403，不产生越权修改；实现参考 delete_role：仅允许删除自定义角色；两个系统角色始终保留。）

### TP-128 · [正常] 账户/用户/鉴权·查询（GET /users）· 正常-可用性
- 模块：账户/用户/鉴权 Auth
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-0ae4b797` / TP `TP-128`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /users，来源文件 backend/research-agent-source/tools/auth/rbac.py
  3. [执行] 发送 GET /users 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·查询 功能可用：GET /users 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 list_role_users）

### TP-129 · [安全] 账户/用户/鉴权·查询（GET /users）· 安全-鉴权缺失
- 模块：账户/用户/鉴权 Auth
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-0ae4b797` / TP `TP-129`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /users，来源文件 backend/research-agent-source/tools/auth/rbac.py
  3. [执行] 发送 GET /users 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·查询 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何账户/用户/鉴权业务数据；实现参考 list_role_users）

### TP-130 · [边界] 账户/用户/鉴权·查询（GET /users）· 边界-参数缺失/非法
- 模块：账户/用户/鉴权 Auth
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-0ae4b797` / TP `TP-130`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /users，来源文件 backend/research-agent-source/tools/auth/rbac.py
  3. [执行] 发送 GET /users 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·查询 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 list_role_users）

### TP-131 · [正常] 账户/用户/鉴权·更新（PUT /users/{user_id}/role）· 正常-可用性
- 模块：账户/用户/鉴权 Auth
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-d38ecd31` / TP `TP-131`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：PUT /users/{user_id}/role，来源文件 backend/research-agent-source/tools/auth/rbac.py
  3. [执行] 发送 PUT /users/{user_id}/role 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·更新 功能可用：PUT /users/{user_id}/role 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 assign_role）

### TP-132 · [安全] 账户/用户/鉴权·更新（PUT /users/{user_id}/role）· 安全-鉴权缺失
- 模块：账户/用户/鉴权 Auth
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-d38ecd31` / TP `TP-132`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：PUT /users/{user_id}/role，来源文件 backend/research-agent-source/tools/auth/rbac.py
  3. [执行] 发送 PUT /users/{user_id}/role 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·更新 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何账户/用户/鉴权业务数据；实现参考 assign_role）

### TP-133 · [边界] 账户/用户/鉴权·更新（PUT /users/{user_id}/role）· 边界-参数缺失/非法
- 模块：账户/用户/鉴权 Auth
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-d38ecd31` / TP `TP-133`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：PUT /users/{user_id}/role，来源文件 backend/research-agent-source/tools/auth/rbac.py
  3. [执行] 发送 PUT /users/{user_id}/role 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·更新 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 assign_role）

### TP-134 · [异常] 账户/用户/鉴权·更新（PUT /users/{user_id}/role）· 异常-资源不存在
- 模块：账户/用户/鉴权 Auth
- 类型：异常　优先级：P1　测试类型：全量
- 关联：FP `FP-d38ecd31` / TP `TP-134`
- 前置条件：被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
- 步骤：
  1. [前置] 被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
  2. [准备] 构造请求：PUT /users/{user_id}/role，来源文件 backend/research-agent-source/tools/auth/rbac.py
  3. [执行] 发送 PUT /users/{user_id}/role 请求并捕获响应
  4. [断言] 校验：接口对非法/边界输入返回预期错误（4xx/5xx），且不产生未捕获异常或数据损坏（预期：账户/用户/鉴权·更新 资源不存在：访问不存在或非法的 {id} → 404，提示明确且不暴露内部细节；实现参考 assign_role）

### TP-135 · [安全] 账户/用户/鉴权·更新（PUT /users/{user_id}/role）· 安全-越权
- 模块：账户/用户/鉴权 Auth
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-d38ecd31` / TP `TP-135`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：PUT /users/{user_id}/role，来源文件 backend/research-agent-source/tools/auth/rbac.py
  3. [执行] 发送 PUT /users/{user_id}/role 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·更新 越权防护：操作他人资源 → 403，不产生越权修改；实现参考 assign_role）

### TP-136 · [正常] 账户/用户/鉴权·登录鉴权（POST /login）· 正常-可用性
- 模块：账户/用户/鉴权 Auth
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-81ad1b1d` / TP `TP-136`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /login，来源文件 backend/research-agent-source/tools/auth/routes.py
  3. [执行] 发送 POST /login 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·登录鉴权 功能可用：POST /login 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 login：账号密码登录。成功返回 access + refresh token pair。）

### TP-137 · [安全] 账户/用户/鉴权·登录鉴权（POST /login）· 安全-鉴权缺失
- 模块：账户/用户/鉴权 Auth
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-81ad1b1d` / TP `TP-137`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /login，来源文件 backend/research-agent-source/tools/auth/routes.py
  3. [执行] 发送 POST /login 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·登录鉴权 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何账户/用户/鉴权业务数据；实现参考 login：账号密码登录。成功返回 access + refresh token pair。）

### TP-138 · [边界] 账户/用户/鉴权·登录鉴权（POST /login）· 边界-参数缺失/非法
- 模块：账户/用户/鉴权 Auth
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-81ad1b1d` / TP `TP-138`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /login，来源文件 backend/research-agent-source/tools/auth/routes.py
  3. [执行] 发送 POST /login 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·登录鉴权 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 login：账号密码登录。成功返回 access + refresh token pair。）

### TP-139 · [正常] 账户/用户/鉴权·提交/创建（POST /refresh）· 正常-可用性
- 模块：账户/用户/鉴权 Auth
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-e6187b9d` / TP `TP-139`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /refresh，来源文件 backend/research-agent-source/tools/auth/routes.py
  3. [执行] 发送 POST /refresh 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·提交/创建 功能可用：POST /refresh 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 refresh：用 refresh token 换新的 access + refresh pair。）

### TP-140 · [安全] 账户/用户/鉴权·提交/创建（POST /refresh）· 安全-鉴权缺失
- 模块：账户/用户/鉴权 Auth
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-e6187b9d` / TP `TP-140`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /refresh，来源文件 backend/research-agent-source/tools/auth/routes.py
  3. [执行] 发送 POST /refresh 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·提交/创建 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何账户/用户/鉴权业务数据；实现参考 refresh：用 refresh token 换新的 access + refresh pair。）

### TP-141 · [边界] 账户/用户/鉴权·提交/创建（POST /refresh）· 边界-参数缺失/非法
- 模块：账户/用户/鉴权 Auth
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-e6187b9d` / TP `TP-141`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /refresh，来源文件 backend/research-agent-source/tools/auth/routes.py
  3. [执行] 发送 POST /refresh 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·提交/创建 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 refresh：用 refresh token 换新的 access + refresh pair。）

### TP-142 · [正常] 账户/用户/鉴权·登录鉴权（POST /logout）· 正常-可用性
- 模块：账户/用户/鉴权 Auth
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-d6e94f1e` / TP `TP-142`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /logout，来源文件 backend/research-agent-source/tools/auth/routes.py
  3. [执行] 发送 POST /logout 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·登录鉴权 功能可用：POST /logout 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 logout：把当前 access token 加入 blacklist。）

### TP-143 · [安全] 账户/用户/鉴权·登录鉴权（POST /logout）· 安全-鉴权缺失
- 模块：账户/用户/鉴权 Auth
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-d6e94f1e` / TP `TP-143`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /logout，来源文件 backend/research-agent-source/tools/auth/routes.py
  3. [执行] 发送 POST /logout 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·登录鉴权 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何账户/用户/鉴权业务数据；实现参考 logout：把当前 access token 加入 blacklist。）

### TP-144 · [边界] 账户/用户/鉴权·登录鉴权（POST /logout）· 边界-参数缺失/非法
- 模块：账户/用户/鉴权 Auth
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-d6e94f1e` / TP `TP-144`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /logout，来源文件 backend/research-agent-source/tools/auth/routes.py
  3. [执行] 发送 POST /logout 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·登录鉴权 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 logout：把当前 access token 加入 blacklist。）

### TP-145 · [正常] 账户/用户/鉴权·查询（GET /me）· 正常-可用性
- 模块：账户/用户/鉴权 Auth
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-af977b94` / TP `TP-145`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /me，来源文件 backend/research-agent-source/tools/auth/routes.py
  3. [执行] 发送 GET /me 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·查询 功能可用：GET /me 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 me：返回当前 user info（iOS App 启动时调一次拿 user 信息 + 验证 token 仍有效）。）

### TP-146 · [安全] 账户/用户/鉴权·查询（GET /me）· 安全-鉴权缺失
- 模块：账户/用户/鉴权 Auth
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-af977b94` / TP `TP-146`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /me，来源文件 backend/research-agent-source/tools/auth/routes.py
  3. [执行] 发送 GET /me 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·查询 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何账户/用户/鉴权业务数据；实现参考 me：返回当前 user info（iOS App 启动时调一次拿 user 信息 + 验证 token 仍有效）。）

### TP-147 · [边界] 账户/用户/鉴权·查询（GET /me）· 边界-参数缺失/非法
- 模块：账户/用户/鉴权 Auth
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-af977b94` / TP `TP-147`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /me，来源文件 backend/research-agent-source/tools/auth/routes.py
  3. [执行] 发送 GET /me 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·查询 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 me：返回当前 user info（iOS App 启动时调一次拿 user 信息 + 验证 token 仍有效）。）

### TP-148 · [正常] 账户/用户/鉴权·登录鉴权（POST /change-password）· 正常-可用性
- 模块：账户/用户/鉴权 Auth
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-1e11d8a6` / TP `TP-148`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /change-password，来源文件 backend/research-agent-source/tools/auth/routes.py
  3. [执行] 发送 POST /change-password 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·登录鉴权 功能可用：POST /change-password 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 change_password：改密码。验证旧密码后写新 hash，同时把该 user 所有未过期 token 加进 blacklist。）

### TP-149 · [安全] 账户/用户/鉴权·登录鉴权（POST /change-password）· 安全-鉴权缺失
- 模块：账户/用户/鉴权 Auth
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-1e11d8a6` / TP `TP-149`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /change-password，来源文件 backend/research-agent-source/tools/auth/routes.py
  3. [执行] 发送 POST /change-password 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·登录鉴权 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何账户/用户/鉴权业务数据；实现参考 change_password：改密码。验证旧密码后写新 hash，同时把该 user 所有未过期 token 加进 blacklist。）

### TP-150 · [边界] 账户/用户/鉴权·登录鉴权（POST /change-password）· 边界-参数缺失/非法
- 模块：账户/用户/鉴权 Auth
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-1e11d8a6` / TP `TP-150`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /change-password，来源文件 backend/research-agent-source/tools/auth/routes.py
  3. [执行] 发送 POST /change-password 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·登录鉴权 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 change_password：改密码。验证旧密码后写新 hash，同时把该 user 所有未过期 token 加进 blacklist。）

### TP-151 · [正常] 未归类·提交/创建（POST /proxy）· 正常-可用性
- 模块：未归类 Other
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-f937ddbc` / TP `TP-151`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /proxy，来源文件 backend/research-agent-source/tools/cockpit/api.py
  3. [执行] 发送 POST /proxy 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：未归类·提交/创建 功能可用：POST /proxy 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 cockpit_proxy）

### TP-152 · [安全] 未归类·提交/创建（POST /proxy）· 安全-鉴权缺失
- 模块：未归类 Other
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-f937ddbc` / TP `TP-152`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /proxy，来源文件 backend/research-agent-source/tools/cockpit/api.py
  3. [执行] 发送 POST /proxy 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：未归类·提交/创建 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何未归类业务数据；实现参考 cockpit_proxy）

### TP-153 · [边界] 未归类·提交/创建（POST /proxy）· 边界-参数缺失/非法
- 模块：未归类 Other
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-f937ddbc` / TP `TP-153`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /proxy，来源文件 backend/research-agent-source/tools/cockpit/api.py
  3. [执行] 发送 POST /proxy 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：未归类·提交/创建 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 cockpit_proxy）

### TP-154 · [正常] 审计/审核看板·健康检查（POST /status）· 正常-可用性
- 模块：审计/审核看板 Audit
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-50731db7` / TP `TP-154`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /status，来源文件 backend/research-agent-source/tools/email_auth/routes.py
  3. [执行] 发送 POST /status 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：审计/审核看板·健康检查 功能可用：POST /status 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 auth_status：查询授权状态（卢总逻辑第一步：任何操作前先验证）。）

### TP-155 · [安全] 审计/审核看板·健康检查（POST /status）· 安全-鉴权缺失
- 模块：审计/审核看板 Audit
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-50731db7` / TP `TP-155`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /status，来源文件 backend/research-agent-source/tools/email_auth/routes.py
  3. [执行] 发送 POST /status 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：审计/审核看板·健康检查 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何审计/审核看板业务数据；实现参考 auth_status：查询授权状态（卢总逻辑第一步：任何操作前先验证）。）

### TP-156 · [边界] 审计/审核看板·健康检查（POST /status）· 边界-参数缺失/非法
- 模块：审计/审核看板 Audit
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-50731db7` / TP `TP-156`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /status，来源文件 backend/research-agent-source/tools/email_auth/routes.py
  3. [执行] 发送 POST /status 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：审计/审核看板·健康检查 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 auth_status：查询授权状态（卢总逻辑第一步：任何操作前先验证）。）

### TP-157 · [正常] 账户/用户/鉴权·登录鉴权（POST /authorize）· 正常-可用性
- 模块：账户/用户/鉴权 Auth
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-d1cb1963` / TP `TP-157`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /authorize，来源文件 backend/research-agent-source/tools/email_auth/routes.py
  3. [执行] 发送 POST /authorize 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·登录鉴权 功能可用：POST /authorize 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 authorize：授权邮箱。先查状态：已授权 → 直接返回不重复添加；未授权/授权过期 → 添加（过期=续期）。）

### TP-158 · [安全] 账户/用户/鉴权·登录鉴权（POST /authorize）· 安全-鉴权缺失
- 模块：账户/用户/鉴权 Auth
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-d1cb1963` / TP `TP-158`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /authorize，来源文件 backend/research-agent-source/tools/email_auth/routes.py
  3. [执行] 发送 POST /authorize 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·登录鉴权 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何账户/用户/鉴权业务数据；实现参考 authorize：授权邮箱。先查状态：已授权 → 直接返回不重复添加；未授权/授权过期 → 添加（过期=续期）。）

### TP-159 · [边界] 账户/用户/鉴权·登录鉴权（POST /authorize）· 边界-参数缺失/非法
- 模块：账户/用户/鉴权 Auth
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-d1cb1963` / TP `TP-159`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /authorize，来源文件 backend/research-agent-source/tools/email_auth/routes.py
  3. [执行] 发送 POST /authorize 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·登录鉴权 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 authorize：授权邮箱。先查状态：已授权 → 直接返回不重复添加；未授权/授权过期 → 添加（过期=续期）。）

### TP-160 · [正常] 对话/会话·取消中止（POST /cancel）· 正常-可用性
- 模块：对话/会话 Chat
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-23b49b51` / TP `TP-160`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /cancel，来源文件 backend/research-agent-source/tools/email_auth/routes.py
  3. [执行] 发送 POST /cancel 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：对话/会话·取消中止 功能可用：POST /cancel 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 cancel：取消授权。先查状态：存在有效/过期记录 → 软删除；未授权 → 无需取消。）

### TP-161 · [安全] 对话/会话·取消中止（POST /cancel）· 安全-鉴权缺失
- 模块：对话/会话 Chat
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-23b49b51` / TP `TP-161`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /cancel，来源文件 backend/research-agent-source/tools/email_auth/routes.py
  3. [执行] 发送 POST /cancel 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：对话/会话·取消中止 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何对话/会话业务数据；实现参考 cancel：取消授权。先查状态：存在有效/过期记录 → 软删除；未授权 → 无需取消。）

### TP-162 · [边界] 对话/会话·取消中止（POST /cancel）· 边界-参数缺失/非法
- 模块：对话/会话 Chat
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-23b49b51` / TP `TP-162`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /cancel，来源文件 backend/research-agent-source/tools/email_auth/routes.py
  3. [执行] 发送 POST /cancel 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：对话/会话·取消中止 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 cancel：取消授权。先查状态：存在有效/过期记录 → 软删除；未授权 → 无需取消。）

### TP-163 · [正常] 简报·查询（GET /today）· 正常-可用性
- 模块：简报 Briefing
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-ab3827f0` / TP `TP-163`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /today，来源文件 backend/research-agent-source/tools/email_list/routes.py
  3. [执行] 发送 GET /today 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：简报·查询 功能可用：GET /today 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 list_today：最近 3 天邮件清单（不含正文，供列表页展示）。路由名 /today 保留兼容前端。）

### TP-164 · [安全] 简报·查询（GET /today）· 安全-鉴权缺失
- 模块：简报 Briefing
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-ab3827f0` / TP `TP-164`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /today，来源文件 backend/research-agent-source/tools/email_list/routes.py
  3. [执行] 发送 GET /today 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：简报·查询 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何简报业务数据；实现参考 list_today：最近 3 天邮件清单（不含正文，供列表页展示）。路由名 /today 保留兼容前端。）

### TP-165 · [边界] 简报·查询（GET /today）· 边界-参数缺失/非法
- 模块：简报 Briefing
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-ab3827f0` / TP `TP-165`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /today，来源文件 backend/research-agent-source/tools/email_list/routes.py
  3. [执行] 发送 GET /today 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：简报·查询 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 list_today：最近 3 天邮件清单（不含正文，供列表页展示）。路由名 /today 保留兼容前端。）

### TP-166 · [正常] 对话/会话·总结简报（POST /summarize）· 正常-可用性
- 模块：对话/会话 Chat
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-ccc7212b` / TP `TP-166`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /summarize，来源文件 backend/research-agent-source/tools/email_list/routes.py
  3. [执行] 发送 POST /summarize 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：对话/会话·总结简报 功能可用：POST /summarize 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 summarize：单封邮件 AI 总结（主动触发）。会议类自动写入日程库。）

### TP-167 · [安全] 对话/会话·总结简报（POST /summarize）· 安全-鉴权缺失
- 模块：对话/会话 Chat
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-ccc7212b` / TP `TP-167`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /summarize，来源文件 backend/research-agent-source/tools/email_list/routes.py
  3. [执行] 发送 POST /summarize 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：对话/会话·总结简报 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何对话/会话业务数据；实现参考 summarize：单封邮件 AI 总结（主动触发）。会议类自动写入日程库。）

### TP-168 · [边界] 对话/会话·总结简报（POST /summarize）· 边界-参数缺失/非法
- 模块：对话/会话 Chat
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-ccc7212b` / TP `TP-168`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /summarize，来源文件 backend/research-agent-source/tools/email_list/routes.py
  3. [执行] 发送 POST /summarize 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：对话/会话·总结简报 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 summarize：单封邮件 AI 总结（主动触发）。会议类自动写入日程库。）

### TP-169 · [正常] 对话/会话·对话交互（GET /ask-quota）· 正常-可用性
- 模块：对话/会话 Chat
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-bd8f759f` / TP `TP-169`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /ask-quota，来源文件 backend/research-agent-source/tools/email_list/routes.py
  3. [执行] 发送 GET /ask-quota 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：对话/会话·对话交互 功能可用：GET /ask-quota 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 ask_quota：「问福享」今日剩余次数（每人每天 1 次）。）

### TP-170 · [安全] 对话/会话·对话交互（GET /ask-quota）· 安全-鉴权缺失
- 模块：对话/会话 Chat
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-bd8f759f` / TP `TP-170`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /ask-quota，来源文件 backend/research-agent-source/tools/email_list/routes.py
  3. [执行] 发送 GET /ask-quota 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：对话/会话·对话交互 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何对话/会话业务数据；实现参考 ask_quota：「问福享」今日剩余次数（每人每天 1 次）。）

### TP-171 · [边界] 对话/会话·对话交互（GET /ask-quota）· 边界-参数缺失/非法
- 模块：对话/会话 Chat
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-bd8f759f` / TP `TP-171`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /ask-quota，来源文件 backend/research-agent-source/tools/email_list/routes.py
  3. [执行] 发送 GET /ask-quota 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：对话/会话·对话交互 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 ask_quota：「问福享」今日剩余次数（每人每天 1 次）。）

### TP-172 · [正常] 对话/会话·对话交互（POST /ask-context）· 正常-可用性
- 模块：对话/会话 Chat
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-f3750201` / TP `TP-172`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /ask-context，来源文件 backend/research-agent-source/tools/email_list/routes.py
  3. [执行] 发送 POST /ask-context 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：对话/会话·对话交互 功能可用：POST /ask-context 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 ask_context：生成「问福享」开场白（含邮件正文与回复纪律），并消耗今日额度。）

### TP-173 · [安全] 对话/会话·对话交互（POST /ask-context）· 安全-鉴权缺失
- 模块：对话/会话 Chat
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-f3750201` / TP `TP-173`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /ask-context，来源文件 backend/research-agent-source/tools/email_list/routes.py
  3. [执行] 发送 POST /ask-context 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：对话/会话·对话交互 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何对话/会话业务数据；实现参考 ask_context：生成「问福享」开场白（含邮件正文与回复纪律），并消耗今日额度。）

### TP-174 · [边界] 对话/会话·对话交互（POST /ask-context）· 边界-参数缺失/非法
- 模块：对话/会话 Chat
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-f3750201` / TP `TP-174`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /ask-context，来源文件 backend/research-agent-source/tools/email_list/routes.py
  3. [执行] 发送 POST /ask-context 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：对话/会话·对话交互 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 ask_context：生成「问福享」开场白（含邮件正文与回复纪律），并消耗今日额度。）

### TP-175 · [正常] 产物/文档·健康检查（GET /api/v1/onlyoffice-status）· 正常-可用性
- 模块：产物/文档 Artifact
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-179adbe5` / TP `TP-175`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /api/v1/onlyoffice-status，来源文件 backend/research-agent-source/tools/onlyoffice_bridge/routes.py
  3. [执行] 发送 GET /api/v1/onlyoffice-status 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：产物/文档·健康检查 功能可用：GET /api/v1/onlyoffice-status 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 onlyoffice_status：返回 DS 是否可达 + URL,供前端探测后决定走 DS 编辑器还是 PDF 回退。）

### TP-176 · [安全] 产物/文档·健康检查（GET /api/v1/onlyoffice-status）· 安全-鉴权缺失
- 模块：产物/文档 Artifact
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-179adbe5` / TP `TP-176`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /api/v1/onlyoffice-status，来源文件 backend/research-agent-source/tools/onlyoffice_bridge/routes.py
  3. [执行] 发送 GET /api/v1/onlyoffice-status 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：产物/文档·健康检查 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何产物/文档业务数据；实现参考 onlyoffice_status：返回 DS 是否可达 + URL,供前端探测后决定走 DS 编辑器还是 PDF 回退。）

### TP-177 · [边界] 产物/文档·健康检查（GET /api/v1/onlyoffice-status）· 边界-参数缺失/非法
- 模块：产物/文档 Artifact
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-179adbe5` / TP `TP-177`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /api/v1/onlyoffice-status，来源文件 backend/research-agent-source/tools/onlyoffice_bridge/routes.py
  3. [执行] 发送 GET /api/v1/onlyoffice-status 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：产物/文档·健康检查 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 onlyoffice_status：返回 DS 是否可达 + URL,供前端探测后决定走 DS 编辑器还是 PDF 回退。）

### TP-178 · [正常] 产物/文档·产物文档（GET /api/v1/artifact/office-onlyoffice-config）· 正常-可用性
- 模块：产物/文档 Artifact
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-d0186c09` / TP `TP-178`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /api/v1/artifact/office-onlyoffice-config，来源文件 backend/research-agent-source/tools/onlyoffice_bridge/routes.py
  3. [执行] 发送 GET /api/v1/artifact/office-onlyoffice-config 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：产物/文档·产物文档 功能可用：GET /api/v1/artifact/office-onlyoffice-config 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 office_onlyoffice_config：构造 OnlyOffice 编辑器配置(含 JWT),支持 docx / xlsx / pptx。）

### TP-179 · [安全] 产物/文档·产物文档（GET /api/v1/artifact/office-onlyoffice-config）· 安全-鉴权缺失
- 模块：产物/文档 Artifact
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-d0186c09` / TP `TP-179`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /api/v1/artifact/office-onlyoffice-config，来源文件 backend/research-agent-source/tools/onlyoffice_bridge/routes.py
  3. [执行] 发送 GET /api/v1/artifact/office-onlyoffice-config 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：产物/文档·产物文档 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何产物/文档业务数据；实现参考 office_onlyoffice_config：构造 OnlyOffice 编辑器配置(含 JWT),支持 docx / xlsx / pptx。）

### TP-180 · [边界] 产物/文档·产物文档（GET /api/v1/artifact/office-onlyoffice-config）· 边界-参数缺失/非法
- 模块：产物/文档 Artifact
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-d0186c09` / TP `TP-180`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /api/v1/artifact/office-onlyoffice-config，来源文件 backend/research-agent-source/tools/onlyoffice_bridge/routes.py
  3. [执行] 发送 GET /api/v1/artifact/office-onlyoffice-config 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：产物/文档·产物文档 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 office_onlyoffice_config：构造 OnlyOffice 编辑器配置(含 JWT),支持 docx / xlsx / pptx。）

### TP-181 · [正常] 产物/文档·产物文档（POST /api/v1/artifact/office-onlyoffice-callback）· 正常-可用性
- 模块：产物/文档 Artifact
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-ea62955c` / TP `TP-181`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /api/v1/artifact/office-onlyoffice-callback，来源文件 backend/research-agent-source/tools/onlyoffice_bridge/routes.py
  3. [执行] 发送 POST /api/v1/artifact/office-onlyoffice-callback 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：产物/文档·产物文档 功能可用：POST /api/v1/artifact/office-onlyoffice-callback 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 office_onlyoffice_callback：DS 在保存 / 关闭时回调;下载新文件后原子覆盖原文件(不备份)。）

### TP-182 · [安全] 产物/文档·产物文档（POST /api/v1/artifact/office-onlyoffice-callback）· 安全-鉴权缺失
- 模块：产物/文档 Artifact
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-ea62955c` / TP `TP-182`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /api/v1/artifact/office-onlyoffice-callback，来源文件 backend/research-agent-source/tools/onlyoffice_bridge/routes.py
  3. [执行] 发送 POST /api/v1/artifact/office-onlyoffice-callback 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：产物/文档·产物文档 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何产物/文档业务数据；实现参考 office_onlyoffice_callback：DS 在保存 / 关闭时回调;下载新文件后原子覆盖原文件(不备份)。）

### TP-183 · [边界] 产物/文档·产物文档（POST /api/v1/artifact/office-onlyoffice-callback）· 边界-参数缺失/非法
- 模块：产物/文档 Artifact
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-ea62955c` / TP `TP-183`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /api/v1/artifact/office-onlyoffice-callback，来源文件 backend/research-agent-source/tools/onlyoffice_bridge/routes.py
  3. [执行] 发送 POST /api/v1/artifact/office-onlyoffice-callback 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：产物/文档·产物文档 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 office_onlyoffice_callback：DS 在保存 / 关闭时回调;下载新文件后原子覆盖原文件(不备份)。）

### TP-184 · [正常] 线程·调度同步（PUT /{schedule_id}）· 正常-可用性
- 模块：线程 Thread
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-6ba2cb9b` / TP `TP-184`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：PUT /{schedule_id}，来源文件 backend/research-agent-source/tools/scheduler/api.py
  3. [执行] 发送 PUT /{schedule_id} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：线程·调度同步 功能可用：PUT /{schedule_id} 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 update_schedule：部分更新一条 schedule(仅 owner);不传 schedule 不更新。）

### TP-185 · [安全] 线程·调度同步（PUT /{schedule_id}）· 安全-鉴权缺失
- 模块：线程 Thread
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-6ba2cb9b` / TP `TP-185`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：PUT /{schedule_id}，来源文件 backend/research-agent-source/tools/scheduler/api.py
  3. [执行] 发送 PUT /{schedule_id} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：线程·调度同步 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何线程业务数据；实现参考 update_schedule：部分更新一条 schedule(仅 owner);不传 schedule 不更新。）

### TP-186 · [边界] 线程·调度同步（PUT /{schedule_id}）· 边界-参数缺失/非法
- 模块：线程 Thread
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-6ba2cb9b` / TP `TP-186`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：PUT /{schedule_id}，来源文件 backend/research-agent-source/tools/scheduler/api.py
  3. [执行] 发送 PUT /{schedule_id} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：线程·调度同步 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 update_schedule：部分更新一条 schedule(仅 owner);不传 schedule 不更新。）

### TP-187 · [异常] 线程·调度同步（PUT /{schedule_id}）· 异常-资源不存在
- 模块：线程 Thread
- 类型：异常　优先级：P1　测试类型：全量
- 关联：FP `FP-6ba2cb9b` / TP `TP-187`
- 前置条件：被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
- 步骤：
  1. [前置] 被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
  2. [准备] 构造请求：PUT /{schedule_id}，来源文件 backend/research-agent-source/tools/scheduler/api.py
  3. [执行] 发送 PUT /{schedule_id} 请求并捕获响应
  4. [断言] 校验：接口对非法/边界输入返回预期错误（4xx/5xx），且不产生未捕获异常或数据损坏（预期：线程·调度同步 资源不存在：访问不存在或非法的 {id} → 404，提示明确且不暴露内部细节；实现参考 update_schedule：部分更新一条 schedule(仅 owner);不传 schedule 不更新。）

### TP-188 · [安全] 线程·调度同步（PUT /{schedule_id}）· 安全-越权
- 模块：线程 Thread
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-6ba2cb9b` / TP `TP-188`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：PUT /{schedule_id}，来源文件 backend/research-agent-source/tools/scheduler/api.py
  3. [执行] 发送 PUT /{schedule_id} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：线程·调度同步 越权防护：操作他人资源 → 403，不产生越权修改；实现参考 update_schedule：部分更新一条 schedule(仅 owner);不传 schedule 不更新。）

### TP-189 · [正常] 线程·调度同步（DELETE /{schedule_id}）· 正常-可用性
- 模块：线程 Thread
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-5e173d23` / TP `TP-189`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：DELETE /{schedule_id}，来源文件 backend/research-agent-source/tools/scheduler/api.py
  3. [执行] 发送 DELETE /{schedule_id} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：线程·调度同步 功能可用：DELETE /{schedule_id} 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 delete_schedule：删除一条 schedule(仅 owner)。）

### TP-190 · [安全] 线程·调度同步（DELETE /{schedule_id}）· 安全-鉴权缺失
- 模块：线程 Thread
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-5e173d23` / TP `TP-190`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：DELETE /{schedule_id}，来源文件 backend/research-agent-source/tools/scheduler/api.py
  3. [执行] 发送 DELETE /{schedule_id} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：线程·调度同步 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何线程业务数据；实现参考 delete_schedule：删除一条 schedule(仅 owner)。）

### TP-191 · [边界] 线程·调度同步（DELETE /{schedule_id}）· 边界-参数缺失/非法
- 模块：线程 Thread
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-5e173d23` / TP `TP-191`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：DELETE /{schedule_id}，来源文件 backend/research-agent-source/tools/scheduler/api.py
  3. [执行] 发送 DELETE /{schedule_id} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：线程·调度同步 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 delete_schedule：删除一条 schedule(仅 owner)。）

### TP-192 · [异常] 线程·调度同步（DELETE /{schedule_id}）· 异常-资源不存在
- 模块：线程 Thread
- 类型：异常　优先级：P1　测试类型：全量
- 关联：FP `FP-5e173d23` / TP `TP-192`
- 前置条件：被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
- 步骤：
  1. [前置] 被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
  2. [准备] 构造请求：DELETE /{schedule_id}，来源文件 backend/research-agent-source/tools/scheduler/api.py
  3. [执行] 发送 DELETE /{schedule_id} 请求并捕获响应
  4. [断言] 校验：接口对非法/边界输入返回预期错误（4xx/5xx），且不产生未捕获异常或数据损坏（预期：线程·调度同步 资源不存在：访问不存在或非法的 {id} → 404，提示明确且不暴露内部细节；实现参考 delete_schedule：删除一条 schedule(仅 owner)。）

### TP-193 · [安全] 线程·调度同步（DELETE /{schedule_id}）· 安全-越权
- 模块：线程 Thread
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-5e173d23` / TP `TP-193`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：DELETE /{schedule_id}，来源文件 backend/research-agent-source/tools/scheduler/api.py
  3. [执行] 发送 DELETE /{schedule_id} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：线程·调度同步 越权防护：操作他人资源 → 403，不产生越权修改；实现参考 delete_schedule：删除一条 schedule(仅 owner)。）

### TP-194 · [正常] 线程·调度同步（POST /{schedule_id}/run）· 正常-可用性
- 模块：线程 Thread
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-59d19239` / TP `TP-194`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /{schedule_id}/run，来源文件 backend/research-agent-source/tools/scheduler/api.py
  3. [执行] 发送 POST /{schedule_id}/run 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：线程·调度同步 功能可用：POST /{schedule_id}/run 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 run_schedule：立即触发一次该 schedule（不修改 schedule 配置；后台跑，不阻塞返回）。）

### TP-195 · [安全] 线程·调度同步（POST /{schedule_id}/run）· 安全-鉴权缺失
- 模块：线程 Thread
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-59d19239` / TP `TP-195`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /{schedule_id}/run，来源文件 backend/research-agent-source/tools/scheduler/api.py
  3. [执行] 发送 POST /{schedule_id}/run 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：线程·调度同步 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何线程业务数据；实现参考 run_schedule：立即触发一次该 schedule（不修改 schedule 配置；后台跑，不阻塞返回）。）

### TP-196 · [边界] 线程·调度同步（POST /{schedule_id}/run）· 边界-参数缺失/非法
- 模块：线程 Thread
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-59d19239` / TP `TP-196`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /{schedule_id}/run，来源文件 backend/research-agent-source/tools/scheduler/api.py
  3. [执行] 发送 POST /{schedule_id}/run 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：线程·调度同步 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 run_schedule：立即触发一次该 schedule（不修改 schedule 配置；后台跑，不阻塞返回）。）

### TP-197 · [异常] 线程·调度同步（POST /{schedule_id}/run）· 异常-资源不存在
- 模块：线程 Thread
- 类型：异常　优先级：P1　测试类型：全量
- 关联：FP `FP-59d19239` / TP `TP-197`
- 前置条件：被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
- 步骤：
  1. [前置] 被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
  2. [准备] 构造请求：POST /{schedule_id}/run，来源文件 backend/research-agent-source/tools/scheduler/api.py
  3. [执行] 发送 POST /{schedule_id}/run 请求并捕获响应
  4. [断言] 校验：接口对非法/边界输入返回预期错误（4xx/5xx），且不产生未捕获异常或数据损坏（预期：线程·调度同步 资源不存在：访问不存在或非法的 {id} → 404，提示明确且不暴露内部细节；实现参考 run_schedule：立即触发一次该 schedule（不修改 schedule 配置；后台跑，不阻塞返回）。）

### TP-198 · [正常] 线程·调度同步（POST /{schedule_id}/toggle）· 正常-可用性
- 模块：线程 Thread
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-2405813e` / TP `TP-198`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /{schedule_id}/toggle，来源文件 backend/research-agent-source/tools/scheduler/api.py
  3. [执行] 发送 POST /{schedule_id}/toggle 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：线程·调度同步 功能可用：POST /{schedule_id}/toggle 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 toggle_schedule：切换 enabled 状态(仅 owner)。）

### TP-199 · [安全] 线程·调度同步（POST /{schedule_id}/toggle）· 安全-鉴权缺失
- 模块：线程 Thread
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-2405813e` / TP `TP-199`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /{schedule_id}/toggle，来源文件 backend/research-agent-source/tools/scheduler/api.py
  3. [执行] 发送 POST /{schedule_id}/toggle 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：线程·调度同步 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何线程业务数据；实现参考 toggle_schedule：切换 enabled 状态(仅 owner)。）

### TP-200 · [边界] 线程·调度同步（POST /{schedule_id}/toggle）· 边界-参数缺失/非法
- 模块：线程 Thread
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-2405813e` / TP `TP-200`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /{schedule_id}/toggle，来源文件 backend/research-agent-source/tools/scheduler/api.py
  3. [执行] 发送 POST /{schedule_id}/toggle 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：线程·调度同步 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 toggle_schedule：切换 enabled 状态(仅 owner)。）

### TP-201 · [异常] 线程·调度同步（POST /{schedule_id}/toggle）· 异常-资源不存在
- 模块：线程 Thread
- 类型：异常　优先级：P1　测试类型：全量
- 关联：FP `FP-2405813e` / TP `TP-201`
- 前置条件：被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
- 步骤：
  1. [前置] 被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
  2. [准备] 构造请求：POST /{schedule_id}/toggle，来源文件 backend/research-agent-source/tools/scheduler/api.py
  3. [执行] 发送 POST /{schedule_id}/toggle 请求并捕获响应
  4. [断言] 校验：接口对非法/边界输入返回预期错误（4xx/5xx），且不产生未捕获异常或数据损坏（预期：线程·调度同步 资源不存在：访问不存在或非法的 {id} → 404，提示明确且不暴露内部细节；实现参考 toggle_schedule：切换 enabled 状态(仅 owner)。）

### TP-202 · [正常] 账户/用户/鉴权·登录鉴权（POST /login/start）· 正常-可用性
- 模块：账户/用户/鉴权 Auth
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-ecb687b5` / TP `TP-202`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /login/start，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 POST /login/start 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·登录鉴权 功能可用：POST /login/start 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 login_start：申请一个扫码登录二维码。）

### TP-203 · [安全] 账户/用户/鉴权·登录鉴权（POST /login/start）· 安全-鉴权缺失
- 模块：账户/用户/鉴权 Auth
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-ecb687b5` / TP `TP-203`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /login/start，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 POST /login/start 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·登录鉴权 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何账户/用户/鉴权业务数据；实现参考 login_start：申请一个扫码登录二维码。）

### TP-204 · [边界] 账户/用户/鉴权·登录鉴权（POST /login/start）· 边界-参数缺失/非法
- 模块：账户/用户/鉴权 Auth
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-ecb687b5` / TP `TP-204`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /login/start，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 POST /login/start 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·登录鉴权 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 login_start：申请一个扫码登录二维码。）

### TP-205 · [正常] 账户/用户/鉴权·登录鉴权（GET /login/{session_key}）· 正常-可用性
- 模块：账户/用户/鉴权 Auth
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-e14195fe` / TP `TP-205`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /login/{session_key}，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 GET /login/{session_key} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·登录鉴权 功能可用：GET /login/{session_key} 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 login_status：轮询扫码状态（一次 poll_qr_status 调用即返回）。）

### TP-206 · [安全] 账户/用户/鉴权·登录鉴权（GET /login/{session_key}）· 安全-鉴权缺失
- 模块：账户/用户/鉴权 Auth
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-e14195fe` / TP `TP-206`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /login/{session_key}，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 GET /login/{session_key} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·登录鉴权 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何账户/用户/鉴权业务数据；实现参考 login_status：轮询扫码状态（一次 poll_qr_status 调用即返回）。）

### TP-207 · [边界] 账户/用户/鉴权·登录鉴权（GET /login/{session_key}）· 边界-参数缺失/非法
- 模块：账户/用户/鉴权 Auth
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-e14195fe` / TP `TP-207`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /login/{session_key}，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 GET /login/{session_key} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·登录鉴权 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 login_status：轮询扫码状态（一次 poll_qr_status 调用即返回）。）

### TP-208 · [异常] 账户/用户/鉴权·登录鉴权（GET /login/{session_key}）· 异常-资源不存在
- 模块：账户/用户/鉴权 Auth
- 类型：异常　优先级：P1　测试类型：全量
- 关联：FP `FP-e14195fe` / TP `TP-208`
- 前置条件：被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
- 步骤：
  1. [前置] 被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
  2. [准备] 构造请求：GET /login/{session_key}，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 GET /login/{session_key} 请求并捕获响应
  4. [断言] 校验：接口对非法/边界输入返回预期错误（4xx/5xx），且不产生未捕获异常或数据损坏（预期：账户/用户/鉴权·登录鉴权 资源不存在：访问不存在或非法的 {id} → 404，提示明确且不暴露内部细节；实现参考 login_status：轮询扫码状态（一次 poll_qr_status 调用即返回）。）

### TP-209 · [正常] 账户/用户/鉴权·登录鉴权（DELETE /login/{session_key}）· 正常-可用性
- 模块：账户/用户/鉴权 Auth
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-5bc8f455` / TP `TP-209`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：DELETE /login/{session_key}，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 DELETE /login/{session_key} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·登录鉴权 功能可用：DELETE /login/{session_key} 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 login_cancel：主动取消扫码会话。）

### TP-210 · [安全] 账户/用户/鉴权·登录鉴权（DELETE /login/{session_key}）· 安全-鉴权缺失
- 模块：账户/用户/鉴权 Auth
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-5bc8f455` / TP `TP-210`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：DELETE /login/{session_key}，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 DELETE /login/{session_key} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·登录鉴权 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何账户/用户/鉴权业务数据；实现参考 login_cancel：主动取消扫码会话。）

### TP-211 · [边界] 账户/用户/鉴权·登录鉴权（DELETE /login/{session_key}）· 边界-参数缺失/非法
- 模块：账户/用户/鉴权 Auth
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-5bc8f455` / TP `TP-211`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：DELETE /login/{session_key}，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 DELETE /login/{session_key} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·登录鉴权 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 login_cancel：主动取消扫码会话。）

### TP-212 · [异常] 账户/用户/鉴权·登录鉴权（DELETE /login/{session_key}）· 异常-资源不存在
- 模块：账户/用户/鉴权 Auth
- 类型：异常　优先级：P1　测试类型：全量
- 关联：FP `FP-5bc8f455` / TP `TP-212`
- 前置条件：被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
- 步骤：
  1. [前置] 被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
  2. [准备] 构造请求：DELETE /login/{session_key}，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 DELETE /login/{session_key} 请求并捕获响应
  4. [断言] 校验：接口对非法/边界输入返回预期错误（4xx/5xx），且不产生未捕获异常或数据损坏（预期：账户/用户/鉴权·登录鉴权 资源不存在：访问不存在或非法的 {id} → 404，提示明确且不暴露内部细节；实现参考 login_cancel：主动取消扫码会话。）

### TP-213 · [安全] 账户/用户/鉴权·登录鉴权（DELETE /login/{session_key}）· 安全-越权
- 模块：账户/用户/鉴权 Auth
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-5bc8f455` / TP `TP-213`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：DELETE /login/{session_key}，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 DELETE /login/{session_key} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·登录鉴权 越权防护：操作他人资源 → 403，不产生越权修改；实现参考 login_cancel：主动取消扫码会话。）

### TP-214 · [正常] 账户/用户/鉴权·查询（GET /accounts）· 正常-可用性
- 模块：账户/用户/鉴权 Auth
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-e7472679` / TP `TP-214`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /accounts，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 GET /accounts 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·查询 功能可用：GET /accounts 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 list_accounts：列出所有已登录账号 + 每个账号的 monitor 状态。）

### TP-215 · [安全] 账户/用户/鉴权·查询（GET /accounts）· 安全-鉴权缺失
- 模块：账户/用户/鉴权 Auth
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-e7472679` / TP `TP-215`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /accounts，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 GET /accounts 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·查询 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何账户/用户/鉴权业务数据；实现参考 list_accounts：列出所有已登录账号 + 每个账号的 monitor 状态。）

### TP-216 · [边界] 账户/用户/鉴权·查询（GET /accounts）· 边界-参数缺失/非法
- 模块：账户/用户/鉴权 Auth
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-e7472679` / TP `TP-216`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /accounts，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 GET /accounts 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·查询 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 list_accounts：列出所有已登录账号 + 每个账号的 monitor 状态。）

### TP-217 · [正常] 账户/用户/鉴权·删除（DELETE /accounts/{account_id}）· 正常-可用性
- 模块：账户/用户/鉴权 Auth
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-3e755d06` / TP `TP-217`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：DELETE /accounts/{account_id}，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 DELETE /accounts/{account_id} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·删除 功能可用：DELETE /accounts/{account_id} 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 remove_account：删除账号（先 stop monitor，再删除凭据）。）

### TP-218 · [安全] 账户/用户/鉴权·删除（DELETE /accounts/{account_id}）· 安全-鉴权缺失
- 模块：账户/用户/鉴权 Auth
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-3e755d06` / TP `TP-218`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：DELETE /accounts/{account_id}，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 DELETE /accounts/{account_id} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·删除 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何账户/用户/鉴权业务数据；实现参考 remove_account：删除账号（先 stop monitor，再删除凭据）。）

### TP-219 · [边界] 账户/用户/鉴权·删除（DELETE /accounts/{account_id}）· 边界-参数缺失/非法
- 模块：账户/用户/鉴权 Auth
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-3e755d06` / TP `TP-219`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：DELETE /accounts/{account_id}，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 DELETE /accounts/{account_id} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·删除 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 remove_account：删除账号（先 stop monitor，再删除凭据）。）

### TP-220 · [异常] 账户/用户/鉴权·删除（DELETE /accounts/{account_id}）· 异常-资源不存在
- 模块：账户/用户/鉴权 Auth
- 类型：异常　优先级：P1　测试类型：全量
- 关联：FP `FP-3e755d06` / TP `TP-220`
- 前置条件：被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
- 步骤：
  1. [前置] 被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
  2. [准备] 构造请求：DELETE /accounts/{account_id}，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 DELETE /accounts/{account_id} 请求并捕获响应
  4. [断言] 校验：接口对非法/边界输入返回预期错误（4xx/5xx），且不产生未捕获异常或数据损坏（预期：账户/用户/鉴权·删除 资源不存在：访问不存在或非法的 {id} → 404，提示明确且不暴露内部细节；实现参考 remove_account：删除账号（先 stop monitor，再删除凭据）。）

### TP-221 · [安全] 账户/用户/鉴权·删除（DELETE /accounts/{account_id}）· 安全-越权
- 模块：账户/用户/鉴权 Auth
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-3e755d06` / TP `TP-221`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：DELETE /accounts/{account_id}，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 DELETE /accounts/{account_id} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·删除 越权防护：操作他人资源 → 403，不产生越权修改；实现参考 remove_account：删除账号（先 stop monitor，再删除凭据）。）

### TP-222 · [正常] 账户/用户/鉴权·提交/创建（POST /accounts/{account_id}/start）· 正常-可用性
- 模块：账户/用户/鉴权 Auth
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-df4e1244` / TP `TP-222`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /accounts/{account_id}/start，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 POST /accounts/{account_id}/start 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·提交/创建 功能可用：POST /accounts/{account_id}/start 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 start_account_monitor：启动指定账号的 monitor（加入 MonitorPool）。）

### TP-223 · [安全] 账户/用户/鉴权·提交/创建（POST /accounts/{account_id}/start）· 安全-鉴权缺失
- 模块：账户/用户/鉴权 Auth
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-df4e1244` / TP `TP-223`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /accounts/{account_id}/start，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 POST /accounts/{account_id}/start 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·提交/创建 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何账户/用户/鉴权业务数据；实现参考 start_account_monitor：启动指定账号的 monitor（加入 MonitorPool）。）

### TP-224 · [边界] 账户/用户/鉴权·提交/创建（POST /accounts/{account_id}/start）· 边界-参数缺失/非法
- 模块：账户/用户/鉴权 Auth
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-df4e1244` / TP `TP-224`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /accounts/{account_id}/start，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 POST /accounts/{account_id}/start 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·提交/创建 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 start_account_monitor：启动指定账号的 monitor（加入 MonitorPool）。）

### TP-225 · [异常] 账户/用户/鉴权·提交/创建（POST /accounts/{account_id}/start）· 异常-资源不存在
- 模块：账户/用户/鉴权 Auth
- 类型：异常　优先级：P1　测试类型：全量
- 关联：FP `FP-df4e1244` / TP `TP-225`
- 前置条件：被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
- 步骤：
  1. [前置] 被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
  2. [准备] 构造请求：POST /accounts/{account_id}/start，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 POST /accounts/{account_id}/start 请求并捕获响应
  4. [断言] 校验：接口对非法/边界输入返回预期错误（4xx/5xx），且不产生未捕获异常或数据损坏（预期：账户/用户/鉴权·提交/创建 资源不存在：访问不存在或非法的 {id} → 404，提示明确且不暴露内部细节；实现参考 start_account_monitor：启动指定账号的 monitor（加入 MonitorPool）。）

### TP-226 · [正常] 账户/用户/鉴权·取消中止（POST /accounts/{account_id}/stop）· 正常-可用性
- 模块：账户/用户/鉴权 Auth
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-6b3b1099` / TP `TP-226`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /accounts/{account_id}/stop，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 POST /accounts/{account_id}/stop 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·取消中止 功能可用：POST /accounts/{account_id}/stop 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 stop_account_monitor：停止指定账号的 monitor（保留凭据）。）

### TP-227 · [安全] 账户/用户/鉴权·取消中止（POST /accounts/{account_id}/stop）· 安全-鉴权缺失
- 模块：账户/用户/鉴权 Auth
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-6b3b1099` / TP `TP-227`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /accounts/{account_id}/stop，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 POST /accounts/{account_id}/stop 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·取消中止 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何账户/用户/鉴权业务数据；实现参考 stop_account_monitor：停止指定账号的 monitor（保留凭据）。）

### TP-228 · [边界] 账户/用户/鉴权·取消中止（POST /accounts/{account_id}/stop）· 边界-参数缺失/非法
- 模块：账户/用户/鉴权 Auth
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-6b3b1099` / TP `TP-228`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /accounts/{account_id}/stop，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 POST /accounts/{account_id}/stop 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·取消中止 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 stop_account_monitor：停止指定账号的 monitor（保留凭据）。）

### TP-229 · [异常] 账户/用户/鉴权·取消中止（POST /accounts/{account_id}/stop）· 异常-资源不存在
- 模块：账户/用户/鉴权 Auth
- 类型：异常　优先级：P1　测试类型：全量
- 关联：FP `FP-6b3b1099` / TP `TP-229`
- 前置条件：被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
- 步骤：
  1. [前置] 被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
  2. [准备] 构造请求：POST /accounts/{account_id}/stop，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 POST /accounts/{account_id}/stop 请求并捕获响应
  4. [断言] 校验：接口对非法/边界输入返回预期错误（4xx/5xx），且不产生未捕获异常或数据损坏（预期：账户/用户/鉴权·取消中止 资源不存在：访问不存在或非法的 {id} → 404，提示明确且不暴露内部细节；实现参考 stop_account_monitor：停止指定账号的 monitor（保留凭据）。）

### TP-230 · [正常] 审计/审核看板·健康检查（GET /status）· 正常-可用性
- 模块：审计/审核看板 Audit
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-e79dfaa6` / TP `TP-230`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /status，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 GET /status 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：审计/审核看板·健康检查 功能可用：GET /status 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 wechat_status：整体状态概览。）

### TP-231 · [安全] 审计/审核看板·健康检查（GET /status）· 安全-鉴权缺失
- 模块：审计/审核看板 Audit
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-e79dfaa6` / TP `TP-231`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /status，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 GET /status 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：审计/审核看板·健康检查 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何审计/审核看板业务数据；实现参考 wechat_status：整体状态概览。）

### TP-232 · [边界] 审计/审核看板·健康检查（GET /status）· 边界-参数缺失/非法
- 模块：审计/审核看板 Audit
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-e79dfaa6` / TP `TP-232`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /status，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 GET /status 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：审计/审核看板·健康检查 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 wechat_status：整体状态概览。）

### TP-233 · [正常] 账户/用户/鉴权·查询（GET /accounts/{account_id}/whitelist）· 正常-可用性
- 模块：账户/用户/鉴权 Auth
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-d8ab6080` / TP `TP-233`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /accounts/{account_id}/whitelist，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 GET /accounts/{account_id}/whitelist 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·查询 功能可用：GET /accounts/{account_id}/whitelist 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 get_whitelist：列出某账号的白名单。）

### TP-234 · [安全] 账户/用户/鉴权·查询（GET /accounts/{account_id}/whitelist）· 安全-鉴权缺失
- 模块：账户/用户/鉴权 Auth
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-d8ab6080` / TP `TP-234`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /accounts/{account_id}/whitelist，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 GET /accounts/{account_id}/whitelist 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·查询 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何账户/用户/鉴权业务数据；实现参考 get_whitelist：列出某账号的白名单。）

### TP-235 · [边界] 账户/用户/鉴权·查询（GET /accounts/{account_id}/whitelist）· 边界-参数缺失/非法
- 模块：账户/用户/鉴权 Auth
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-d8ab6080` / TP `TP-235`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /accounts/{account_id}/whitelist，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 GET /accounts/{account_id}/whitelist 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·查询 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 get_whitelist：列出某账号的白名单。）

### TP-236 · [异常] 账户/用户/鉴权·查询（GET /accounts/{account_id}/whitelist）· 异常-资源不存在
- 模块：账户/用户/鉴权 Auth
- 类型：异常　优先级：P1　测试类型：全量
- 关联：FP `FP-d8ab6080` / TP `TP-236`
- 前置条件：被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
- 步骤：
  1. [前置] 被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
  2. [准备] 构造请求：GET /accounts/{account_id}/whitelist，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 GET /accounts/{account_id}/whitelist 请求并捕获响应
  4. [断言] 校验：接口对非法/边界输入返回预期错误（4xx/5xx），且不产生未捕获异常或数据损坏（预期：账户/用户/鉴权·查询 资源不存在：访问不存在或非法的 {id} → 404，提示明确且不暴露内部细节；实现参考 get_whitelist：列出某账号的白名单。）

### TP-237 · [正常] 账户/用户/鉴权·提交/创建（POST /accounts/{account_id}/whitelist）· 正常-可用性
- 模块：账户/用户/鉴权 Auth
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-3ce048fe` / TP `TP-237`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /accounts/{account_id}/whitelist，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 POST /accounts/{account_id}/whitelist 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·提交/创建 功能可用：POST /accounts/{account_id}/whitelist 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 add_to_whitelist：把 user_id 加入某账号白名单。）

### TP-238 · [安全] 账户/用户/鉴权·提交/创建（POST /accounts/{account_id}/whitelist）· 安全-鉴权缺失
- 模块：账户/用户/鉴权 Auth
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-3ce048fe` / TP `TP-238`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /accounts/{account_id}/whitelist，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 POST /accounts/{account_id}/whitelist 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·提交/创建 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何账户/用户/鉴权业务数据；实现参考 add_to_whitelist：把 user_id 加入某账号白名单。）

### TP-239 · [边界] 账户/用户/鉴权·提交/创建（POST /accounts/{account_id}/whitelist）· 边界-参数缺失/非法
- 模块：账户/用户/鉴权 Auth
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-3ce048fe` / TP `TP-239`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：POST /accounts/{account_id}/whitelist，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 POST /accounts/{account_id}/whitelist 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·提交/创建 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 add_to_whitelist：把 user_id 加入某账号白名单。）

### TP-240 · [异常] 账户/用户/鉴权·提交/创建（POST /accounts/{account_id}/whitelist）· 异常-资源不存在
- 模块：账户/用户/鉴权 Auth
- 类型：异常　优先级：P1　测试类型：全量
- 关联：FP `FP-3ce048fe` / TP `TP-240`
- 前置条件：被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
- 步骤：
  1. [前置] 被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
  2. [准备] 构造请求：POST /accounts/{account_id}/whitelist，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 POST /accounts/{account_id}/whitelist 请求并捕获响应
  4. [断言] 校验：接口对非法/边界输入返回预期错误（4xx/5xx），且不产生未捕获异常或数据损坏（预期：账户/用户/鉴权·提交/创建 资源不存在：访问不存在或非法的 {id} → 404，提示明确且不暴露内部细节；实现参考 add_to_whitelist：把 user_id 加入某账号白名单。）

### TP-241 · [正常] 账户/用户/鉴权·删除（DELETE /accounts/{account_id}/whitelist/{user_id}）· 正常-可用性
- 模块：账户/用户/鉴权 Auth
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-ac92ea8d` / TP `TP-241`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：DELETE /accounts/{account_id}/whitelist/{user_id}，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 DELETE /accounts/{account_id}/whitelist/{user_id} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·删除 功能可用：DELETE /accounts/{account_id}/whitelist/{user_id} 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 remove_from_whitelist：从某账号白名单移除 user_id。）

### TP-242 · [安全] 账户/用户/鉴权·删除（DELETE /accounts/{account_id}/whitelist/{user_id}）· 安全-鉴权缺失
- 模块：账户/用户/鉴权 Auth
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-ac92ea8d` / TP `TP-242`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：DELETE /accounts/{account_id}/whitelist/{user_id}，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 DELETE /accounts/{account_id}/whitelist/{user_id} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·删除 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何账户/用户/鉴权业务数据；实现参考 remove_from_whitelist：从某账号白名单移除 user_id。）

### TP-243 · [边界] 账户/用户/鉴权·删除（DELETE /accounts/{account_id}/whitelist/{user_id}）· 边界-参数缺失/非法
- 模块：账户/用户/鉴权 Auth
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-ac92ea8d` / TP `TP-243`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：DELETE /accounts/{account_id}/whitelist/{user_id}，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 DELETE /accounts/{account_id}/whitelist/{user_id} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·删除 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 remove_from_whitelist：从某账号白名单移除 user_id。）

### TP-244 · [异常] 账户/用户/鉴权·删除（DELETE /accounts/{account_id}/whitelist/{user_id}）· 异常-资源不存在
- 模块：账户/用户/鉴权 Auth
- 类型：异常　优先级：P1　测试类型：全量
- 关联：FP `FP-ac92ea8d` / TP `TP-244`
- 前置条件：被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
- 步骤：
  1. [前置] 被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
  2. [准备] 构造请求：DELETE /accounts/{account_id}/whitelist/{user_id}，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 DELETE /accounts/{account_id}/whitelist/{user_id} 请求并捕获响应
  4. [断言] 校验：接口对非法/边界输入返回预期错误（4xx/5xx），且不产生未捕获异常或数据损坏（预期：账户/用户/鉴权·删除 资源不存在：访问不存在或非法的 {id} → 404，提示明确且不暴露内部细节；实现参考 remove_from_whitelist：从某账号白名单移除 user_id。）

### TP-245 · [安全] 账户/用户/鉴权·删除（DELETE /accounts/{account_id}/whitelist/{user_id}）· 安全-越权
- 模块：账户/用户/鉴权 Auth
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-ac92ea8d` / TP `TP-245`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：DELETE /accounts/{account_id}/whitelist/{user_id}，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 DELETE /accounts/{account_id}/whitelist/{user_id} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：账户/用户/鉴权·删除 越权防护：操作他人资源 → 403，不产生越权修改；实现参考 remove_from_whitelist：从某账号白名单移除 user_id。）

### TP-246 · [正常] 产物/文档·导出下载（GET /dl/{short_id}）· 正常-可用性
- 模块：产物/文档 Artifact
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-942506ae` / TP `TP-246`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /dl/{short_id}，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 GET /dl/{short_id} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：产物/文档·导出下载 功能可用：GET /dl/{short_id} 路由存在且可调用，合法请求返回预期业务结果（2xx），关键字段完整；实现参考 download_artifact：短链 → 产物下载。强制 ``Content-Disposition: attachment``，避免 inline 打开。）

### TP-247 · [安全] 产物/文档·导出下载（GET /dl/{short_id}）· 安全-鉴权缺失
- 模块：产物/文档 Artifact
- 类型：安全　优先级：P1　测试类型：全量
- 关联：FP `FP-942506ae` / TP `TP-247`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /dl/{short_id}，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 GET /dl/{short_id} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：产物/文档·导出下载 鉴权校验：缺失/错误 Authorization → 401/403，不得返回任何产物/文档业务数据；实现参考 download_artifact：短链 → 产物下载。强制 ``Content-Disposition: attachment``，避免 inline 打开。）

### TP-248 · [边界] 产物/文档·导出下载（GET /dl/{short_id}）· 边界-参数缺失/非法
- 模块：产物/文档 Artifact
- 类型：边界　优先级：P1　测试类型：全量
- 关联：FP `FP-942506ae` / TP `TP-248`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：GET /dl/{short_id}，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 GET /dl/{short_id} 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：产物/文档·导出下载 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，错误信息可定位到具体字段；实现参考 download_artifact：短链 → 产物下载。强制 ``Content-Disposition: attachment``，避免 inline 打开。）

### TP-249 · [异常] 产物/文档·导出下载（GET /dl/{short_id}）· 异常-资源不存在
- 模块：产物/文档 Artifact
- 类型：异常　优先级：P1　测试类型：全量
- 关联：FP `FP-942506ae` / TP `TP-249`
- 前置条件：被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
- 步骤：
  1. [前置] 被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式
  2. [准备] 构造请求：GET /dl/{short_id}，来源文件 backend/research-agent-source/tools/wechat_channel/admin_api.py
  3. [执行] 发送 GET /dl/{short_id} 请求并捕获响应
  4. [断言] 校验：接口对非法/边界输入返回预期错误（4xx/5xx），且不产生未捕获异常或数据损坏（预期：产物/文档·导出下载 资源不存在：访问不存在或非法的 {id} → 404，提示明确且不暴露内部细节；实现参考 download_artifact：短链 → 产物下载。强制 ``Content-Disposition: attachment``，避免 inline 打开。）

### TP-250 · [正常] models.py::MessageType — 消息类型，对齐 OpenClaw src/api/types.ts 的 MessageType。
- 模块：业务函数·数据模型定义
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-2875b3f3` / TP `TP-250`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC MessageType，来源文件 backend/research-agent-source/tools/wechat_channel/models.py
  3. [执行] 发送 FUNC MessageType 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 MessageType 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：消息类型，对齐 OpenClaw src/api/types.ts 的 MessageType。）

### TP-251 · [正常] models.py::MessageState — 消息状态，对齐 OpenClaw src/api/types.ts 的 MessageState。
- 模块：业务函数·数据模型定义
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-d6ffb058` / TP `TP-251`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC MessageState，来源文件 backend/research-agent-source/tools/wechat_channel/models.py
  3. [执行] 发送 FUNC MessageState 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 MessageState 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：消息状态，对齐 OpenClaw src/api/types.ts 的 MessageState。）

### TP-252 · [正常] models.py::MessageItemType — MessageItem.type，对齐 OpenClaw src/api/types.ts 的 MessageItemType。
- 模块：业务函数·数据模型定义
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-ecb76126` / TP `TP-252`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC MessageItemType，来源文件 backend/research-agent-source/tools/wechat_channel/models.py
  3. [执行] 发送 FUNC MessageItemType 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 MessageItemType 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：MessageItem.type，对齐 OpenClaw src/api/types.ts 的 MessageItemType。）

### TP-253 · [正常] models.py::TextItem — 业务逻辑逻辑覆盖
- 模块：业务函数·数据模型定义
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-1220136a` / TP `TP-253`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC TextItem，来源文件 backend/research-agent-source/tools/wechat_channel/models.py
  3. [执行] 发送 FUNC TextItem 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 TextItem 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-254 · [正常] models.py::CDNMedia — 业务逻辑逻辑覆盖
- 模块：业务函数·数据模型定义
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-395d6846` / TP `TP-254`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC CDNMedia，来源文件 backend/research-agent-source/tools/wechat_channel/models.py
  3. [执行] 发送 FUNC CDNMedia 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 CDNMedia 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-255 · [正常] models.py::ImageItem — 业务逻辑逻辑覆盖
- 模块：业务函数·数据模型定义
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-2b6b432c` / TP `TP-255`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC ImageItem，来源文件 backend/research-agent-source/tools/wechat_channel/models.py
  3. [执行] 发送 FUNC ImageItem 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 ImageItem 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-256 · [正常] models.py::VoiceItem — 业务逻辑逻辑覆盖
- 模块：业务函数·数据模型定义
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-c16b3267` / TP `TP-256`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC VoiceItem，来源文件 backend/research-agent-source/tools/wechat_channel/models.py
  3. [执行] 发送 FUNC VoiceItem 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 VoiceItem 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-257 · [正常] models.py::FileItem — 业务逻辑逻辑覆盖
- 模块：业务函数·数据模型定义
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-af3986de` / TP `TP-257`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC FileItem，来源文件 backend/research-agent-source/tools/wechat_channel/models.py
  3. [执行] 发送 FUNC FileItem 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 FileItem 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-258 · [正常] models.py::VideoItem — 业务逻辑逻辑覆盖
- 模块：业务函数·数据模型定义
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-e0296225` / TP `TP-258`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC VideoItem，来源文件 backend/research-agent-source/tools/wechat_channel/models.py
  3. [执行] 发送 FUNC VideoItem 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 VideoItem 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-259 · [正常] models.py::RefMessage — 业务逻辑逻辑覆盖
- 模块：业务函数·数据模型定义
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-3a7ba812` / TP `TP-259`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC RefMessage，来源文件 backend/research-agent-source/tools/wechat_channel/models.py
  3. [执行] 发送 FUNC RefMessage 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 RefMessage 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-260 · [正常] models.py::MessageItem — 业务逻辑逻辑覆盖
- 模块：业务函数·数据模型定义
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-0693f7a1` / TP `TP-260`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC MessageItem，来源文件 backend/research-agent-source/tools/wechat_channel/models.py
  3. [执行] 发送 FUNC MessageItem 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 MessageItem 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-261 · [正常] models.py::WeixinMessage — 业务逻辑逻辑覆盖
- 模块：业务函数·数据模型定义
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-4bed9a40` / TP `TP-261`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC WeixinMessage，来源文件 backend/research-agent-source/tools/wechat_channel/models.py
  3. [执行] 发送 FUNC WeixinMessage 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 WeixinMessage 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-262 · [正常] rbac.py::Role — 业务逻辑逻辑覆盖
- 模块：业务函数·账户/用户/鉴权
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-5a7ca1d3` / TP `TP-262`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC Role，来源文件 backend/research-agent-source/tools/auth/rbac.py
  3. [执行] 发送 FUNC Role 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 Role 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-263 · [正常] rbac.py::Menu — 菜单主数据：权限角色保存 key，展示名称与路由由此表统一维护。
- 模块：业务函数·账户/用户/鉴权
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-4f0754d7` / TP `TP-263`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC Menu，来源文件 backend/research-agent-source/tools/auth/rbac.py
  3. [执行] 发送 FUNC Menu 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 Menu 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：菜单主数据：权限角色保存 key，展示名称与路由由此表统一维护。）

### TP-264 · [正常] rbac.py::UserRole — 业务逻辑逻辑覆盖
- 模块：业务函数·账户/用户/鉴权
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-70a5addb` / TP `TP-264`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC UserRole，来源文件 backend/research-agent-source/tools/auth/rbac.py
  3. [执行] 发送 FUNC UserRole 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 UserRole 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-265 · [正常] rbac.py::ensure_rbac_schema — 幂等创建 RBAC 表、系统角色及用户角色绑定。
- 模块：业务函数·账户/用户/鉴权
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-6e7a49f3` / TP `TP-265`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC ensure_rbac_schema，来源文件 backend/research-agent-source/tools/auth/rbac.py
  3. [执行] 发送 FUNC ensure_rbac_schema 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 ensure_rbac_schema 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：幂等创建 RBAC 表、系统角色及用户角色绑定。）

### TP-266 · [正常] rbac.py::menu_catalog — 优先从菜单主数据表读取；老库尚未迁移时回退内置目录。
- 模块：业务函数·账户/用户/鉴权
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-2b4a4d40` / TP `TP-266`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC menu_catalog，来源文件 backend/research-agent-source/tools/auth/rbac.py
  3. [执行] 发送 FUNC menu_catalog 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 menu_catalog 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：优先从菜单主数据表读取；老库尚未迁移时回退内置目录。）

### TP-267 · [正常] rbac.py::roles_for_user — 业务逻辑逻辑覆盖
- 模块：业务函数·账户/用户/鉴权
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-428de33f` / TP `TP-267`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC roles_for_user，来源文件 backend/research-agent-source/tools/auth/rbac.py
  3. [执行] 发送 FUNC roles_for_user 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 roles_for_user 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-268 · [正常] rbac.py::is_rbac_admin — 业务逻辑逻辑覆盖
- 模块：业务函数·账户/用户/鉴权
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-c5550ce6` / TP `TP-268`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC is_rbac_admin，来源文件 backend/research-agent-source/tools/auth/rbac.py
  3. [执行] 发送 FUNC is_rbac_admin 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 is_rbac_admin 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-269 · [正常] rbac.py::require_rbac_admin — 业务逻辑逻辑覆盖
- 模块：业务函数·账户/用户/鉴权
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-fa3f0d87` / TP `TP-269`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC require_rbac_admin，来源文件 backend/research-agent-source/tools/auth/rbac.py
  3. [执行] 发送 FUNC require_rbac_admin 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 require_rbac_admin 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-270 · [正常] rbac.py::can_call_api — 业务逻辑逻辑覆盖
- 模块：业务函数·账户/用户/鉴权
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-aea501f8` / TP `TP-270`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC can_call_api，来源文件 backend/research-agent-source/tools/auth/rbac.py
  3. [执行] 发送 FUNC can_call_api 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 can_call_api 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-271 · [正常] rbac.py::RoleIn — 业务逻辑逻辑覆盖
- 模块：业务函数·账户/用户/鉴权
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-5c714dd2` / TP `TP-271`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC RoleIn，来源文件 backend/research-agent-source/tools/auth/rbac.py
  3. [执行] 发送 FUNC RoleIn 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 RoleIn 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-272 · [正常] rbac.py::RoleUpdate — 业务逻辑逻辑覆盖
- 模块：业务函数·账户/用户/鉴权
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-fa744190` / TP `TP-272`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC RoleUpdate，来源文件 backend/research-agent-source/tools/auth/rbac.py
  3. [执行] 发送 FUNC RoleUpdate 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 RoleUpdate 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-273 · [正常] rbac.py::AssignRole — 业务逻辑逻辑覆盖
- 模块：业务函数·账户/用户/鉴权
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-5164fdb0` / TP `TP-273`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC AssignRole，来源文件 backend/research-agent-source/tools/auth/rbac.py
  3. [执行] 发送 FUNC AssignRole 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 AssignRole 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-274 · [正常] aml_dataquery_server.py::search_query_templates — 根据用户自然语言检索 SQL 模板。
- 模块：业务函数·工具/集成
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-b1504950` / TP `TP-274`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC search_query_templates，来源文件 backend/research-agent-source/mcp_servers/aml_dataquery_server.py
  3. [执行] 发送 FUNC search_query_templates 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 search_query_templates 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：根据用户自然语言检索 SQL 模板。）

### TP-275 · [正常] aml_dataquery_server.py::list_categories — 列出所有 SQL 模板的分类（如 C03-大额交易、C07-可疑交易）。
- 模块：业务函数·工具/集成
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-7ff4492e` / TP `TP-275`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC list_categories，来源文件 backend/research-agent-source/mcp_servers/aml_dataquery_server.py
  3. [执行] 发送 FUNC list_categories 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 list_categories 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：列出所有 SQL 模板的分类（如 C03-大额交易、C07-可疑交易）。）

### TP-276 · [正常] aml_dataquery_server.py::get_template_params — 获取指定模板的参数定义（name/type/label/required/default/options）。
- 模块：业务函数·工具/集成
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-441aba17` / TP `TP-276`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC get_template_params，来源文件 backend/research-agent-source/mcp_servers/aml_dataquery_server.py
  3. [执行] 发送 FUNC get_template_params 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 get_template_params 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：获取指定模板的参数定义（name/type/label/required/default/options）。）

### TP-277 · [正常] aml_dataquery_server.py::execute_query_template — 执行 SQL 模板查询。强制脱敏 + 审计日志 + 行数截断。
- 模块：业务函数·工具/集成
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-ccf9a79a` / TP `TP-277`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC execute_query_template，来源文件 backend/research-agent-source/mcp_servers/aml_dataquery_server.py
  3. [执行] 发送 FUNC execute_query_template 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 execute_query_template 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：执行 SQL 模板查询。强制脱敏 + 审计日志 + 行数截断。）

### TP-278 · [正常] aml_dataquery_server.py::compose_query_plan — 多 SQL 编排：分别执行多个模板，按 join_key 关联（可选），输出合并表。
- 模块：业务函数·工具/集成
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-9db65236` / TP `TP-278`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC compose_query_plan，来源文件 backend/research-agent-source/mcp_servers/aml_dataquery_server.py
  3. [执行] 发送 FUNC compose_query_plan 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 compose_query_plan 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：多 SQL 编排：分别执行多个模板，按 join_key 关联（可选），输出合并表。）

### TP-279 · [正常] aml_dataquery_server.py::export_query_result — 把 result_id 对应的查询结果导出为 CSV / XLSX。
- 模块：业务函数·工具/集成
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-0cbfb474` / TP `TP-279`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC export_query_result，来源文件 backend/research-agent-source/mcp_servers/aml_dataquery_server.py
  3. [执行] 发送 FUNC export_query_result 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 export_query_result 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：把 result_id 对应的查询结果导出为 CSV / XLSX。）

### TP-280 · [正常] aml_dataquery_server.py::query_audit_log — 查审计日志（谁在什么时候跑过什么 SQL）。
- 模块：业务函数·工具/集成
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-b71b1d08` / TP `TP-280`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC query_audit_log，来源文件 backend/research-agent-source/mcp_servers/aml_dataquery_server.py
  3. [执行] 发送 FUNC query_audit_log 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 query_audit_log 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：查审计日志（谁在什么时候跑过什么 SQL）。）

### TP-281 · [正常] aml_dataquery_server.py::render_html_table — 把 result_id 对应的查询结果渲染为自包含 HTML 表格文件。
- 模块：业务函数·工具/集成
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-c86a9701` / TP `TP-281`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC render_html_table，来源文件 backend/research-agent-source/mcp_servers/aml_dataquery_server.py
  3. [执行] 发送 FUNC render_html_table 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 render_html_table 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：把 result_id 对应的查询结果渲染为自包含 HTML 表格文件。）

### TP-282 · [正常] aml_dataquery_server.py::FeedbackLogger — SQL 二次核验 feedback 持久化（v0.4.1.2 新增）。
- 模块：业务函数·工具/集成
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-f461b0ff` / TP `TP-282`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC FeedbackLogger，来源文件 backend/research-agent-source/mcp_servers/aml_dataquery_server.py
  3. [执行] 发送 FUNC FeedbackLogger 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 FeedbackLogger 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：SQL 二次核验 feedback 持久化（v0.4.1.2 新增）。）

### TP-283 · [正常] aml_dataquery_server.py::preview_query_template — v0.4.1.2 新增：渲染 SQL 但**不执行**。LLM 拿到 preview_id 后调 ask_user with type='sql_preview
- 模块：业务函数·工具/集成
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-49815f62` / TP `TP-283`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC preview_query_template，来源文件 backend/research-agent-source/mcp_servers/aml_dataquery_server.py
  3. [执行] 发送 FUNC preview_query_template 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 preview_query_template 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：v0.4.1.2 新增：渲染 SQL 但**不执行**。LLM 拿到 preview_id 后调 ask_user with type='sql_preview）

### TP-284 · [正常] aml_dataquery_server.py::confirm_query_template — v0.4.1.2 新增：用户在 SQLPreviewCard 提交后，LLM 调这个 tool 真跑 / 写 feedback。
- 模块：业务函数·工具/集成
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-40c2b0ee` / TP `TP-284`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC confirm_query_template，来源文件 backend/research-agent-source/mcp_servers/aml_dataquery_server.py
  3. [执行] 发送 FUNC confirm_query_template 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 confirm_query_template 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：v0.4.1.2 新增：用户在 SQLPreviewCard 提交后，LLM 调这个 tool 真跑 / 写 feedback。）

### TP-285 · [正常] aml_dataquery_server.py::check_sql_semantic_consistency — v0.4.1.6 #36 改造：评估 SQL 与用户问题的语义一致性（阿里 SqlGenerateNode → SemanticConsistencyNode 
- 模块：业务函数·工具/集成
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-7270228f` / TP `TP-285`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC check_sql_semantic_consistency，来源文件 backend/research-agent-source/mcp_servers/aml_dataquery_server.py
  3. [执行] 发送 FUNC check_sql_semantic_consistency 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 check_sql_semantic_consistency 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：v0.4.1.6 #36 改造：评估 SQL 与用户问题的语义一致性（阿里 SqlGenerateNode → SemanticConsistencyNode ）

### TP-286 · [正常] flash_daily_rollup.py::setv — 业务逻辑逻辑覆盖
- 模块：业务函数·简报/总结
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-e17f44bf` / TP `TP-286`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC setv，来源文件 backend/research-agent-source/tools/flash_daily_rollup.py
  3. [执行] 发送 FUNC setv 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 setv 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-287 · [正常] flash_daily_rollup.py::log — 业务逻辑逻辑覆盖
- 模块：业务函数·简报/总结
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-eef9b6da` / TP `TP-287`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC log，来源文件 backend/research-agent-source/tools/flash_daily_rollup.py
  3. [执行] 发送 FUNC log 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 log 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-288 · [正常] flash_daily_rollup.py::seq_progress — 业务逻辑逻辑覆盖
- 模块：业务函数·简报/总结
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-45c27469` / TP `TP-288`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC seq_progress，来源文件 backend/research-agent-source/tools/flash_daily_rollup.py
  3. [执行] 发送 FUNC seq_progress 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 seq_progress 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-289 · [正常] flash_daily_rollup.py::wf — 业务逻辑逻辑覆盖
- 模块：业务函数·简报/总结
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-95ebfd48` / TP `TP-289`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC wf，来源文件 backend/research-agent-source/tools/flash_daily_rollup.py
  3. [执行] 发送 FUNC wf 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 wf 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-290 · [正常] flash_daily_rollup.py::jit — 业务逻辑逻辑覆盖
- 模块：业务函数·简报/总结
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-9f2c7d86` / TP `TP-290`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC jit，来源文件 backend/research-agent-source/tools/flash_daily_rollup.py
  3. [执行] 发送 FUNC jit 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 jit 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-291 · [正常] flash_daily_rollup.py::D — 业务逻辑逻辑覆盖
- 模块：业务函数·简报/总结
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-a344f928` / TP `TP-291`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC D，来源文件 backend/research-agent-source/tools/flash_daily_rollup.py
  3. [执行] 发送 FUNC D 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 D 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-292 · [正常] flash_daily_rollup.py::advance_day — 业务逻辑逻辑覆盖
- 模块：业务函数·简报/总结
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-b112cbba` / TP `TP-292`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC advance_day，来源文件 backend/research-agent-source/tools/flash_daily_rollup.py
  3. [执行] 发送 FUNC advance_day 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 advance_day 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-293 · [正常] flash_daily_rollup.py::fmt_yi — 业务逻辑逻辑覆盖
- 模块：业务函数·简报/总结
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-3f1e0b8a` / TP `TP-293`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC fmt_yi，来源文件 backend/research-agent-source/tools/flash_daily_rollup.py
  3. [执行] 发送 FUNC fmt_yi 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 fmt_yi 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-294 · [正常] flash_daily_rollup.py::rebuild_tracking — 业务逻辑逻辑覆盖
- 模块：业务函数·简报/总结
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-5e8dbb17` / TP `TP-294`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC rebuild_tracking，来源文件 backend/research-agent-source/tools/flash_daily_rollup.py
  3. [执行] 发送 FUNC rebuild_tracking 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 rebuild_tracking 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-295 · [正常] flash_daily_rollup.py::ph — 业务逻辑逻辑覆盖
- 模块：业务函数·简报/总结
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-38053906` / TP `TP-295`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC ph，来源文件 backend/research-agent-source/tools/flash_daily_rollup.py
  3. [执行] 发送 FUNC ph 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 ph 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-296 · [正常] flash_daily_rollup.py::pct_str — 业务逻辑逻辑覆盖
- 模块：业务函数·简报/总结
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-092c3223` / TP `TP-296`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC pct_str，来源文件 backend/research-agent-source/tools/flash_daily_rollup.py
  3. [执行] 发送 FUNC pct_str 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 pct_str 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-297 · [正常] flash_daily_rollup.py::num — 业务逻辑逻辑覆盖
- 模块：业务函数·简报/总结
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-b358ef35` / TP `TP-297`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC num，来源文件 backend/research-agent-source/tools/flash_daily_rollup.py
  3. [执行] 发送 FUNC num 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 num 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-298 · [正常] models.py::get_db — 获取管理后台 sqlite 连接（单进程内复用）。
- 模块：业务函数·数据模型定义
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-7046e1ae` / TP `TP-298`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC get_db，来源文件 backend/research-agent-source/tools/audit_kb_admin/models.py
  3. [执行] 发送 FUNC get_db 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 get_db 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：获取管理后台 sqlite 连接（单进程内复用）。）

### TP-299 · [正常] models.py::set_document_status — 标记文档状态（如确认废止）。重复调用覆盖更新。
- 模块：业务函数·数据模型定义
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-630a9e80` / TP `TP-299`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC set_document_status，来源文件 backend/research-agent-source/tools/audit_kb_admin/models.py
  3. [执行] 发送 FUNC set_document_status 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 set_document_status 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：标记文档状态（如确认废止）。重复调用覆盖更新。）

### TP-300 · [正常] models.py::get_document_status_map — 返回 {src_id: {valid_status, confirmed_at, confirmed_by, kb_name}}。
- 模块：业务函数·数据模型定义
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-104291ac` / TP `TP-300`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC get_document_status_map，来源文件 backend/research-agent-source/tools/audit_kb_admin/models.py
  3. [执行] 发送 FUNC get_document_status_map 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 get_document_status_map 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：返回 {src_id: {valid_status, confirmed_at, confirmed_by, kb_name}}。）

### TP-301 · [正常] models.py::init_db — 初始化管理后台数据库（幂等）。
- 模块：业务函数·数据模型定义
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-2089d926` / TP `TP-301`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC init_db，来源文件 backend/research-agent-source/tools/audit_kb_admin/models.py
  3. [执行] 发送 FUNC init_db 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 init_db 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：初始化管理后台数据库（幂等）。）

### TP-302 · [正常] models.py::PendingTask — 业务逻辑逻辑覆盖
- 模块：业务函数·数据模型定义
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-0e41dc3e` / TP `TP-302`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC PendingTask，来源文件 backend/research-agent-source/tools/audit_kb_admin/models.py
  3. [执行] 发送 FUNC PendingTask 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 PendingTask 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-303 · [正常] models.py::AuditLogEntry — 业务逻辑逻辑覆盖
- 模块：业务函数·数据模型定义
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-003efec0` / TP `TP-303`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC AuditLogEntry，来源文件 backend/research-agent-source/tools/audit_kb_admin/models.py
  3. [执行] 发送 FUNC AuditLogEntry 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 AuditLogEntry 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-304 · [正常] models.py::create_pending_task — 创建一条待处理任务，返回 id。
- 模块：业务函数·数据模型定义
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-8b8e2039` / TP `TP-304`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC create_pending_task，来源文件 backend/research-agent-source/tools/audit_kb_admin/models.py
  3. [执行] 发送 FUNC create_pending_task 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 create_pending_task 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：创建一条待处理任务，返回 id。）

### TP-305 · [正常] models.py::list_pending_tasks — 列出待处理任务。
- 模块：业务函数·数据模型定义
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-e16ed340` / TP `TP-305`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC list_pending_tasks，来源文件 backend/research-agent-source/tools/audit_kb_admin/models.py
  3. [执行] 发送 FUNC list_pending_tasks 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 list_pending_tasks 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：列出待处理任务。）

### TP-306 · [正常] models.py::get_pending_task — 业务逻辑逻辑覆盖
- 模块：业务函数·数据模型定义
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-cb784535` / TP `TP-306`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC get_pending_task，来源文件 backend/research-agent-source/tools/audit_kb_admin/models.py
  3. [执行] 发送 FUNC get_pending_task 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 get_pending_task 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-307 · [正常] models.py::confirm_task — 审计老师确认任务。
- 模块：业务函数·数据模型定义
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-935455a0` / TP `TP-307`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC confirm_task，来源文件 backend/research-agent-source/tools/audit_kb_admin/models.py
  3. [执行] 发送 FUNC confirm_task 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 confirm_task 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：审计老师确认任务。）

### TP-308 · [正常] models.py::dismiss_task — 审计老师驳回/忽略任务。
- 模块：业务函数·数据模型定义
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-5a7461c0` / TP `TP-308`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC dismiss_task，来源文件 backend/research-agent-source/tools/audit_kb_admin/models.py
  3. [执行] 发送 FUNC dismiss_task 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 dismiss_task 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：审计老师驳回/忽略任务。）

### TP-309 · [正常] models.py::count_pending_tasks — 统计各状态任务数。
- 模块：业务函数·数据模型定义
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-d59a246f` / TP `TP-309`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC count_pending_tasks，来源文件 backend/research-agent-source/tools/audit_kb_admin/models.py
  3. [执行] 发送 FUNC count_pending_tasks 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 count_pending_tasks 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：统计各状态任务数。）

### TP-310 · [正常] yaml_loader.py::AgentConfigError — agent YAML 解析/校验失败。
- 模块：业务函数·对话/智能体编排
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-18562599` / TP `TP-310`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC AgentConfigError，来源文件 backend/research-agent-source/agents/yaml_loader.py
  3. [执行] 发送 FUNC AgentConfigError 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 AgentConfigError 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：agent YAML 解析/校验失败。）

### TP-311 · [正常] yaml_loader.py::ReadOnlyAgentError — 尝试写入 builtin 目录的 agent。
- 模块：业务函数·对话/智能体编排
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-b1bdb55e` / TP `TP-311`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC ReadOnlyAgentError，来源文件 backend/research-agent-source/agents/yaml_loader.py
  3. [执行] 发送 FUNC ReadOnlyAgentError 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 ReadOnlyAgentError 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：尝试写入 builtin 目录的 agent。）

### TP-312 · [正常] yaml_loader.py::builtin_dir — 业务逻辑逻辑覆盖
- 模块：业务函数·对话/智能体编排
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-7c181436` / TP `TP-312`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC builtin_dir，来源文件 backend/research-agent-source/agents/yaml_loader.py
  3. [执行] 发送 FUNC builtin_dir 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 builtin_dir 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-313 · [正常] yaml_loader.py::user_dir — 业务逻辑逻辑覆盖
- 模块：业务函数·对话/智能体编排
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-aed71df1` / TP `TP-313`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC user_dir，来源文件 backend/research-agent-source/agents/yaml_loader.py
  3. [执行] 发送 FUNC user_dir 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 user_dir 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-314 · [正常] yaml_loader.py::ensure_dirs — 启动时确保 builtin/ 与 user/ 存在（user/ 用于放用户创建）。
- 模块：业务函数·对话/智能体编排
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-af5b78e9` / TP `TP-314`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC ensure_dirs，来源文件 backend/research-agent-source/agents/yaml_loader.py
  3. [执行] 发送 FUNC ensure_dirs 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 ensure_dirs 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：启动时确保 builtin/ 与 user/ 存在（user/ 用于放用户创建）。）

### TP-315 · [正常] yaml_loader.py::parse_agent_yaml — 读单个 .yaml → SubAgent dict；解析失败返 None。
- 模块：业务函数·对话/智能体编排
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-0f3b9edd` / TP `TP-315`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC parse_agent_yaml，来源文件 backend/research-agent-source/agents/yaml_loader.py
  3. [执行] 发送 FUNC parse_agent_yaml 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 parse_agent_yaml 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：读单个 .yaml → SubAgent dict；解析失败返 None。）

### TP-316 · [正常] yaml_loader.py::load_main_agent — 读 builtin/main.yaml 作为 coordinator 配置。
- 模块：业务函数·对话/智能体编排
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-c314c27a` / TP `TP-316`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC load_main_agent，来源文件 backend/research-agent-source/agents/yaml_loader.py
  3. [执行] 发送 FUNC load_main_agent 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 load_main_agent 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：读 builtin/main.yaml 作为 coordinator 配置。）

### TP-317 · [正常] yaml_loader.py::load_subagents — 扫描 builtin/*.yaml（除 main.yaml）+ user/*.yaml。
- 模块：业务函数·对话/智能体编排
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-f145ec35` / TP `TP-317`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC load_subagents，来源文件 backend/research-agent-source/agents/yaml_loader.py
  3. [执行] 发送 FUNC load_subagents 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 load_subagents 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：扫描 builtin/*.yaml（除 main.yaml）+ user/*.yaml。）

### TP-318 · [正常] yaml_loader.py::list_agents — 列出全部 agent（main + builtin + user），不含 source_path 与 system_prompt 全文。
- 模块：业务函数·对话/智能体编排
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-3878f86e` / TP `TP-318`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC list_agents，来源文件 backend/research-agent-source/agents/yaml_loader.py
  3. [执行] 发送 FUNC list_agents 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 list_agents 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：列出全部 agent（main + builtin + user），不含 source_path 与 system_prompt 全文。）

### TP-319 · [正常] yaml_loader.py::get_agent — 读单个 agent 完整配置（用于 GET /api/agents/{name}）。
- 模块：业务函数·对话/智能体编排
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-b05cb17c` / TP `TP-319`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC get_agent，来源文件 backend/research-agent-source/agents/yaml_loader.py
  3. [执行] 发送 FUNC get_agent 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 get_agent 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：读单个 agent 完整配置（用于 GET /api/agents/{name}）。）

### TP-320 · [正常] yaml_loader.py::write_agent_yaml — 写 agent YAML 到 user/ 目录。main 与 builtin 拒绝写入。
- 模块：业务函数·对话/智能体编排
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-3857951f` / TP `TP-320`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC write_agent_yaml，来源文件 backend/research-agent-source/agents/yaml_loader.py
  3. [执行] 发送 FUNC write_agent_yaml 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 write_agent_yaml 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：写 agent YAML 到 user/ 目录。main 与 builtin 拒绝写入。）

### TP-321 · [正常] yaml_loader.py::update_main_agent_config — 更新 builtin/main.yaml 的 tools / skills / subagents 三个白名单字段。
- 模块：业务函数·对话/智能体编排
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-741a9e88` / TP `TP-321`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC update_main_agent_config，来源文件 backend/research-agent-source/agents/yaml_loader.py
  3. [执行] 发送 FUNC update_main_agent_config 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 update_main_agent_config 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：更新 builtin/main.yaml 的 tools / skills / subagents 三个白名单字段。）

### TP-322 · [正常] sync.py::log — 业务逻辑逻辑覆盖
- 模块：业务函数·调度/同步任务
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-3d3e6b52` / TP `TP-322`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC log，来源文件 backend/research-agent-source/tools/cockpit_sync/sync.py
  3. [执行] 发送 FUNC log 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 log 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-323 · [正常] sync.py::num — 业务逻辑逻辑覆盖
- 模块：业务函数·调度/同步任务
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-c739e260` / TP `TP-323`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC num，来源文件 backend/research-agent-source/tools/cockpit_sync/sync.py
  3. [执行] 发送 FUNC num 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 num 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-324 · [正常] sync.py::rate — 业务逻辑逻辑覆盖
- 模块：业务函数·调度/同步任务
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-76f41439` / TP `TP-324`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC rate，来源文件 backend/research-agent-source/tools/cockpit_sync/sync.py
  3. [执行] 发送 FUNC rate 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 rate 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-325 · [正常] sync.py::txt — 业务逻辑逻辑覆盖
- 模块：业务函数·调度/同步任务
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-c3b263de` / TP `TP-325`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC txt，来源文件 backend/research-agent-source/tools/cockpit_sync/sync.py
  3. [执行] 发送 FUNC txt 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 txt 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-326 · [正常] sync.py::row_company — 业务逻辑逻辑覆盖
- 模块：业务函数·调度/同步任务
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-0264a2dd` / TP `TP-326`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC row_company，来源文件 backend/research-agent-source/tools/cockpit_sync/sync.py
  3. [执行] 发送 FUNC row_company 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 row_company 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-327 · [正常] sync.py::row_ep — 业务逻辑逻辑覆盖
- 模块：业务函数·调度/同步任务
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-d22d3779` / TP `TP-327`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC row_ep，来源文件 backend/research-agent-source/tools/cockpit_sync/sync.py
  3. [执行] 发送 FUNC row_ep 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 row_ep 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-328 · [正常] sync.py::row_op — 业务逻辑逻辑覆盖
- 模块：业务函数·调度/同步任务
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-85f7e399` / TP `TP-328`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC row_op，来源文件 backend/research-agent-source/tools/cockpit_sync/sync.py
  3. [执行] 发送 FUNC row_op 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 row_op 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-329 · [正常] sync.py::row_gp — 业务逻辑逻辑覆盖
- 模块：业务函数·调度/同步任务
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-d64d4926` / TP `TP-329`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC row_gp，来源文件 backend/research-agent-source/tools/cockpit_sync/sync.py
  3. [执行] 发送 FUNC row_gp 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 row_gp 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-330 · [正常] sync.py::row_cp — 业务逻辑逻辑覆盖
- 模块：业务函数·调度/同步任务
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-b1cb5ce3` / TP `TP-330`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC row_cp，来源文件 backend/research-agent-source/tools/cockpit_sync/sync.py
  3. [执行] 发送 FUNC row_cp 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 row_cp 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-331 · [正常] sync.py::row_tracking — 业务逻辑逻辑覆盖
- 模块：业务函数·调度/同步任务
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-3ddc88d8` / TP `TP-331`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC row_tracking，来源文件 backend/research-agent-source/tools/cockpit_sync/sync.py
  3. [执行] 发送 FUNC row_tracking 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 row_tracking 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-332 · [正常] sync.py::call_all — 依次调用 6 接口，返回 {方法名: {'ok':bool,'data':list,'error':str}}
- 模块：业务函数·调度/同步任务
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-ce653774` / TP `TP-332`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC call_all，来源文件 backend/research-agent-source/tools/cockpit_sync/sync.py
  3. [执行] 发送 FUNC call_all 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 call_all 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：依次调用 6 接口，返回 {方法名: {'ok':bool,'data':list,'error':str}}）

### TP-333 · [正常] sync.py::write_tables — 成功接口整表替换（同事务），失败接口表不动
- 模块：业务函数·调度/同步任务
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-9df45161` / TP `TP-333`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC write_tables，来源文件 backend/research-agent-source/tools/cockpit_sync/sync.py
  3. [执行] 发送 FUNC write_tables 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 write_tables 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：成功接口整表替换（同事务），失败接口表不动）

### TP-334 · [正常] routes.py::LoginRequest — 业务逻辑逻辑覆盖
- 模块：业务函数·账户/用户/鉴权
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-26d2055e` / TP `TP-334`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC LoginRequest，来源文件 backend/research-agent-source/tools/auth/routes.py
  3. [执行] 发送 FUNC LoginRequest 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 LoginRequest 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-335 · [正常] routes.py::TokenPair — 业务逻辑逻辑覆盖
- 模块：业务函数·账户/用户/鉴权
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-9dbc28bb` / TP `TP-335`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC TokenPair，来源文件 backend/research-agent-source/tools/auth/routes.py
  3. [执行] 发送 FUNC TokenPair 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 TokenPair 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-336 · [正常] routes.py::RefreshRequest — 业务逻辑逻辑覆盖
- 模块：业务函数·账户/用户/鉴权
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-42758cd5` / TP `TP-336`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC RefreshRequest，来源文件 backend/research-agent-source/tools/auth/routes.py
  3. [执行] 发送 FUNC RefreshRequest 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 RefreshRequest 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-337 · [正常] routes.py::LogoutResponse — 业务逻辑逻辑覆盖
- 模块：业务函数·账户/用户/鉴权
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-987aeb5c` / TP `TP-337`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC LogoutResponse，来源文件 backend/research-agent-source/tools/auth/routes.py
  3. [执行] 发送 FUNC LogoutResponse 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 LogoutResponse 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-338 · [正常] routes.py::MeResponse — 业务逻辑逻辑覆盖
- 模块：业务函数·账户/用户/鉴权
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-a25f467b` / TP `TP-338`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC MeResponse，来源文件 backend/research-agent-source/tools/auth/routes.py
  3. [执行] 发送 FUNC MeResponse 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 MeResponse 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-339 · [正常] routes.py::ChangePasswordRequest — 业务逻辑逻辑覆盖
- 模块：业务函数·账户/用户/鉴权
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-2486a645` / TP `TP-339`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC ChangePasswordRequest，来源文件 backend/research-agent-source/tools/auth/routes.py
  3. [执行] 发送 FUNC ChangePasswordRequest 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 ChangePasswordRequest 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-340 · [正常] routes.py::ChangePasswordResponse — 业务逻辑逻辑覆盖
- 模块：业务函数·账户/用户/鉴权
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-77a1b929` / TP `TP-340`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC ChangePasswordResponse，来源文件 backend/research-agent-source/tools/auth/routes.py
  3. [执行] 发送 FUNC ChangePasswordResponse 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 ChangePasswordResponse 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-341 · [正常] routes.py::login — 账号密码登录。成功返回 access + refresh token pair。
- 模块：业务函数·账户/用户/鉴权
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-dcee4468` / TP `TP-341`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC login，来源文件 backend/research-agent-source/tools/auth/routes.py
  3. [执行] 发送 FUNC login 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 login 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：账号密码登录。成功返回 access + refresh token pair。）

### TP-342 · [正常] routes.py::refresh — 用 refresh token 换新的 access + refresh pair。
- 模块：业务函数·账户/用户/鉴权
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-3c5d8a10` / TP `TP-342`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC refresh，来源文件 backend/research-agent-source/tools/auth/routes.py
  3. [执行] 发送 FUNC refresh 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 refresh 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：用 refresh token 换新的 access + refresh pair。）

### TP-343 · [正常] routes.py::logout — 把当前 access token 加入 blacklist。
- 模块：业务函数·账户/用户/鉴权
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-893aff43` / TP `TP-343`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC logout，来源文件 backend/research-agent-source/tools/auth/routes.py
  3. [执行] 发送 FUNC logout 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 logout 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：把当前 access token 加入 blacklist。）

### TP-344 · [正常] routes.py::me — 返回当前 user info（iOS App 启动时调一次拿 user 信息 + 验证 token 仍有效）。
- 模块：业务函数·账户/用户/鉴权
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-f0f6dd6e` / TP `TP-344`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC me，来源文件 backend/research-agent-source/tools/auth/routes.py
  3. [执行] 发送 FUNC me 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 me 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：返回当前 user info（iOS App 启动时调一次拿 user 信息 + 验证 token 仍有效）。）

### TP-345 · [正常] routes.py::change_password — 改密码。验证旧密码后写新 hash，同时把该 user 所有未过期 token 加进 blacklist。
- 模块：业务函数·账户/用户/鉴权
- 类型：正常　优先级：P1　测试类型：全量
- 关联：FP `FP-b0ff08d1` / TP `TP-345`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC change_password，来源文件 backend/research-agent-source/tools/auth/routes.py
  3. [执行] 发送 FUNC change_password 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 change_password 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：改密码。验证旧密码后写新 hash，同时把该 user 所有未过期 token 加进 blacklist。）

### TP-346 · [正常] gm_client.py::decompress_pub — 压缩公钥(02/03 前缀) → gmssl 需要的 128 hex (x||y)
- 模块：业务函数·调度/同步任务
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-f63abd75` / TP `TP-346`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC decompress_pub，来源文件 backend/research-agent-source/tools/cockpit_sync/gm_client.py
  3. [执行] 发送 FUNC decompress_pub 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 decompress_pub 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：压缩公钥(02/03 前缀) → gmssl 需要的 128 hex (x||y)）

### TP-347 · [正常] gm_client.py::sm2_encrypt — 返回 04||C1||C3||C2（或 C1C2C3）
- 模块：业务函数·调度/同步任务
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-397ae02f` / TP `TP-347`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC sm2_encrypt，来源文件 backend/research-agent-source/tools/cockpit_sync/gm_client.py
  3. [执行] 发送 FUNC sm2_encrypt 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 sm2_encrypt 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：返回 04||C1||C3||C2（或 C1C2C3））

### TP-348 · [正常] gm_client.py::sm2_decrypt — 业务逻辑逻辑覆盖
- 模块：业务函数·调度/同步任务
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-ddb3d8f8` / TP `TP-348`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC sm2_decrypt，来源文件 backend/research-agent-source/tools/cockpit_sync/gm_client.py
  3. [执行] 发送 FUNC sm2_decrypt 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 sm2_decrypt 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-349 · [正常] gm_client.py::sm4_cbc_encrypt — 业务逻辑逻辑覆盖
- 模块：业务函数·调度/同步任务
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-6ac993f8` / TP `TP-349`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC sm4_cbc_encrypt，来源文件 backend/research-agent-source/tools/cockpit_sync/gm_client.py
  3. [执行] 发送 FUNC sm4_cbc_encrypt 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 sm4_cbc_encrypt 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-350 · [正常] gm_client.py::sm4_ecb_encrypt — 业务逻辑逻辑覆盖
- 模块：业务函数·调度/同步任务
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-e58c77e3` / TP `TP-350`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC sm4_ecb_encrypt，来源文件 backend/research-agent-source/tools/cockpit_sync/gm_client.py
  3. [执行] 发送 FUNC sm4_ecb_encrypt 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 sm4_ecb_encrypt 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-351 · [正常] gm_client.py::sm4_cbc_decrypt — 业务逻辑逻辑覆盖
- 模块：业务函数·调度/同步任务
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-e50f2008` / TP `TP-351`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC sm4_cbc_decrypt，来源文件 backend/research-agent-source/tools/cockpit_sync/gm_client.py
  3. [执行] 发送 FUNC sm4_cbc_decrypt 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 sm4_cbc_decrypt 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-352 · [正常] gm_client.py::der_encode_rs — 业务逻辑逻辑覆盖
- 模块：业务函数·调度/同步任务
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-fa226209` / TP `TP-352`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC der_encode_rs，来源文件 backend/research-agent-source/tools/cockpit_sync/gm_client.py
  3. [执行] 发送 FUNC der_encode_rs 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 der_encode_rs 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-353 · [正常] gm_client.py::der_decode_rs — 业务逻辑逻辑覆盖
- 模块：业务函数·调度/同步任务
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-ccb25f21` / TP `TP-353`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC der_decode_rs，来源文件 backend/research-agent-source/tools/cockpit_sync/gm_client.py
  3. [执行] 发送 FUNC der_decode_rs 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 der_decode_rs 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-354 · [正常] gm_client.py::sign_sm3 — SM3withSM2 → DER(r,s)
- 模块：业务函数·调度/同步任务
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-9cdfda66` / TP `TP-354`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC sign_sm3，来源文件 backend/research-agent-source/tools/cockpit_sync/gm_client.py
  3. [执行] 发送 FUNC sign_sm3 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 sign_sm3 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：SM3withSM2 → DER(r,s)）

### TP-355 · [正常] gm_client.py::verify_sm3 — 业务逻辑逻辑覆盖
- 模块：业务函数·调度/同步任务
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-dce1b335` / TP `TP-355`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC verify_sm3，来源文件 backend/research-agent-source/tools/cockpit_sync/gm_client.py
  3. [执行] 发送 FUNC verify_sm3 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 verify_sm3 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-356 · [正常] gm_client.py::BmpGmClient — 业务逻辑逻辑覆盖
- 模块：业务函数·调度/同步任务
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-31fb1494` / TP `TP-356`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC BmpGmClient，来源文件 backend/research-agent-source/tools/cockpit_sync/gm_client.py
  3. [执行] 发送 FUNC BmpGmClient 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 BmpGmClient 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测）

### TP-357 · [正常] api.py::get_updates — 长轮询收消息。
- 模块：业务函数·通知推送
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-9c019573` / TP `TP-357`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC get_updates，来源文件 backend/research-agent-source/tools/wechat_channel/api.py
  3. [执行] 发送 FUNC get_updates 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 get_updates 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：长轮询收消息。）

### TP-358 · [正常] api.py::send_message — 发送一条文本消息。
- 模块：业务函数·通知推送
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-4c9a30c1` / TP `TP-358`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC send_message，来源文件 backend/research-agent-source/tools/wechat_channel/api.py
  3. [执行] 发送 FUNC send_message 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 send_message 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：发送一条文本消息。）

### TP-359 · [正常] api.py::send_message_with_items — 发任意 item_list 的 sendMessage（适用于 TEXT / IMAGE / FILE / VIDEO 消息）。
- 模块：业务函数·通知推送
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-945bb7f4` / TP `TP-359`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC send_message_with_items，来源文件 backend/research-agent-source/tools/wechat_channel/api.py
  3. [执行] 发送 FUNC send_message_with_items 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 send_message_with_items 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：发任意 item_list 的 sendMessage（适用于 TEXT / IMAGE / FILE / VIDEO 消息）。）

### TP-360 · [正常] api.py::notify_start — 启动 monitor 时通知腾讯侧。对应 src/api/api.ts:576-586。
- 模块：业务函数·通知推送
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-c16288f5` / TP `TP-360`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC notify_start，来源文件 backend/research-agent-source/tools/wechat_channel/api.py
  3. [执行] 发送 FUNC notify_start 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 notify_start 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：启动 monitor 时通知腾讯侧。对应 src/api/api.ts:576-586。）

### TP-361 · [正常] api.py::notify_stop — 停止 monitor 时通知腾讯侧。对应 src/api/api.ts:561-571。
- 模块：业务函数·通知推送
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-4fc391dc` / TP `TP-361`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC notify_stop，来源文件 backend/research-agent-source/tools/wechat_channel/api.py
  3. [执行] 发送 FUNC notify_stop 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 notify_stop 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：停止 monitor 时通知腾讯侧。对应 src/api/api.ts:561-571。）

### TP-362 · [正常] api.py::get_config — 获取账号配置（含 typing_ticket）。
- 模块：业务函数·通知推送
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-41b08985` / TP `TP-362`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC get_config，来源文件 backend/research-agent-source/tools/wechat_channel/api.py
  3. [执行] 发送 FUNC get_config 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 get_config 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：获取账号配置（含 typing_ticket）。）

### TP-363 · [正常] api.py::send_typing — 发送/取消"正在输入"指示。
- 模块：业务函数·通知推送
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-8507b548` / TP `TP-363`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC send_typing，来源文件 backend/research-agent-source/tools/wechat_channel/api.py
  3. [执行] 发送 FUNC send_typing 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 send_typing 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：发送/取消"正在输入"指示。）

### TP-364 · [正常] api.py::get_upload_url — 申请 CDN 上传 URL（用于发送图片 / 文件 / 视频消息）。
- 模块：业务函数·通知推送
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-2c105bb1` / TP `TP-364`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC get_upload_url，来源文件 backend/research-agent-source/tools/wechat_channel/api.py
  3. [执行] 发送 FUNC get_upload_url 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 get_upload_url 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：申请 CDN 上传 URL（用于发送图片 / 文件 / 视频消息）。）

### TP-365 · [正常] api.py::fetch_qr_code — 申请扫码登录二维码。
- 模块：业务函数·通知推送
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-5e52c776` / TP `TP-365`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC fetch_qr_code，来源文件 backend/research-agent-source/tools/wechat_channel/api.py
  3. [执行] 发送 FUNC fetch_qr_code 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 fetch_qr_code 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：申请扫码登录二维码。）

### TP-366 · [正常] api.py::poll_qr_status — 长轮询扫码状态。
- 模块：业务函数·通知推送
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-f02ed251` / TP `TP-366`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC poll_qr_status，来源文件 backend/research-agent-source/tools/wechat_channel/api.py
  3. [执行] 发送 FUNC poll_qr_status 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 poll_qr_status 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：长轮询扫码状态。）

### TP-367 · [正常] api.py::WeixinMessageLite — send_message 用：与完整 WeixinMessage 一致，只是让 IDE 知道这里要用到它。
- 模块：业务函数·通知推送
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-2cf2806f` / TP `TP-367`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC WeixinMessageLite，来源文件 backend/research-agent-source/tools/wechat_channel/api.py
  3. [执行] 发送 FUNC WeixinMessageLite 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 WeixinMessageLite 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：send_message 用：与完整 WeixinMessage 一致，只是让 IDE 知道这里要用到它。）

### TP-368 · [正常] config.py::get_onlyoffice_url — OnlyOffice Document Server URL（浏览器侧访问）。
- 模块：业务函数·产物/文档
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-65b000b9` / TP `TP-368`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC get_onlyoffice_url，来源文件 backend/research-agent-source/tools/onlyoffice_bridge/config.py
  3. [执行] 发送 FUNC get_onlyoffice_url 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 get_onlyoffice_url 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：OnlyOffice Document Server URL（浏览器侧访问）。）

### TP-369 · [正常] config.py::get_jwt_secret — JWT 共享密钥（HS256）。缺则视为 JWT 未启用（DS 也会拒加载）。
- 模块：业务函数·产物/文档
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-4ca744f4` / TP `TP-369`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC get_jwt_secret，来源文件 backend/research-agent-source/tools/onlyoffice_bridge/config.py
  3. [执行] 发送 FUNC get_jwt_secret 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 get_jwt_secret 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：JWT 共享密钥（HS256）。缺则视为 JWT 未启用（DS 也会拒加载）。）

### TP-370 · [正常] config.py::get_docker_backend_url — DS 容器视角下访问后端的 URL。
- 模块：业务函数·产物/文档
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-b8a23333` / TP `TP-370`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC get_docker_backend_url，来源文件 backend/research-agent-source/tools/onlyoffice_bridge/config.py
  3. [执行] 发送 FUNC get_docker_backend_url 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 get_docker_backend_url 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：DS 容器视角下访问后端的 URL。）

### TP-371 · [正常] config.py::is_onlyoffice_configured — 是否完成基础配置（URL + JWT 密钥齐备）。
- 模块：业务函数·产物/文档
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-8a03c4ea` / TP `TP-371`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC is_onlyoffice_configured，来源文件 backend/research-agent-source/tools/onlyoffice_bridge/config.py
  3. [执行] 发送 FUNC is_onlyoffice_configured 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 is_onlyoffice_configured 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：是否完成基础配置（URL + JWT 密钥齐备）。）

### TP-372 · [正常] config.py::sign_jwt — 用 HS256 签 payload；缺密钥返回 None。
- 模块：业务函数·产物/文档
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-4e550b28` / TP `TP-372`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC sign_jwt，来源文件 backend/research-agent-source/tools/onlyoffice_bridge/config.py
  3. [执行] 发送 FUNC sign_jwt 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 sign_jwt 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：用 HS256 签 payload；缺密钥返回 None。）

### TP-373 · [正常] config.py::verify_jwt — 校验 JWT;返回 payload(不是 bool);签名错 / 缺密钥 / 过期 均返回 None。
- 模块：业务函数·产物/文档
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-9f11a4a8` / TP `TP-373`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC verify_jwt，来源文件 backend/research-agent-source/tools/onlyoffice_bridge/config.py
  3. [执行] 发送 FUNC verify_jwt 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 verify_jwt 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：校验 JWT;返回 payload(不是 bool);签名错 / 缺密钥 / 过期 均返回 None。）

### TP-374 · [正常] config.py::office_sha1 — Office 文件字节的 sha1，作为 OnlyOffice ``document.key``。
- 模块：业务函数·产物/文档
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-0790d205` / TP `TP-374`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC office_sha1，来源文件 backend/research-agent-source/tools/onlyoffice_bridge/config.py
  3. [执行] 发送 FUNC office_sha1 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 office_sha1 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：Office 文件字节的 sha1，作为 OnlyOffice ``document.key``。）

### TP-375 · [正常] config.py::is_supported_office_ext — 是否 OnlyOffice 支持的 Office 扩展名（不区分大小写，带点号）。
- 模块：业务函数·产物/文档
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-356a353b` / TP `TP-375`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC is_supported_office_ext，来源文件 backend/research-agent-source/tools/onlyoffice_bridge/config.py
  3. [执行] 发送 FUNC is_supported_office_ext 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 is_supported_office_ext 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：是否 OnlyOffice 支持的 Office 扩展名（不区分大小写，带点号）。）

### TP-376 · [正常] config.py::office_file_type — 扩展名 → OnlyOffice ``document.fileType``；不支持返回 None。
- 模块：业务函数·产物/文档
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-d19a23d2` / TP `TP-376`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC office_file_type，来源文件 backend/research-agent-source/tools/onlyoffice_bridge/config.py
  3. [执行] 发送 FUNC office_file_type 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 office_file_type 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：扩展名 → OnlyOffice ``document.fileType``；不支持返回 None。）

### TP-377 · [正常] config.py::office_mime_type — 扩展名 → MIME；不支持返回 None。
- 模块：业务函数·产物/文档
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-a76969a1` / TP `TP-377`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC office_mime_type，来源文件 backend/research-agent-source/tools/onlyoffice_bridge/config.py
  3. [执行] 发送 FUNC office_mime_type 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 office_mime_type 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：扩展名 → MIME；不支持返回 None。）

### TP-378 · [正常] accounts.py::normalize_account_id — OpenClaw 风格：把 `xxx@im.bot` / `xxx@im.wechat` 转成文件系统安全的 key。
- 模块：业务函数·通知推送
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-97db5c75` / TP `TP-378`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC normalize_account_id，来源文件 backend/research-agent-source/tools/wechat_channel/accounts.py
  3. [执行] 发送 FUNC normalize_account_id 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 normalize_account_id 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：OpenClaw 风格：把 `xxx@im.bot` / `xxx@im.wechat` 转成文件系统安全的 key。）

### TP-379 · [正常] accounts.py::load_account — 读单账号凭据；缺失返回 None。
- 模块：业务函数·通知推送
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-9adc4886` / TP `TP-379`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC load_account，来源文件 backend/research-agent-source/tools/wechat_channel/accounts.py
  3. [执行] 发送 FUNC load_account 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 load_account 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：读单账号凭据；缺失返回 None。）

### TP-380 · [正常] accounts.py::save_account — 保存 / 更新单账号凭据。
- 模块：业务函数·通知推送
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-1ce9d8d3` / TP `TP-380`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC save_account，来源文件 backend/research-agent-source/tools/wechat_channel/accounts.py
  3. [执行] 发送 FUNC save_account 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 save_account 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：保存 / 更新单账号凭据。）

### TP-381 · [正常] accounts.py::delete_account — 删除单账号凭据与同步游标（不在 accounts.json 索引里登记的账号也可强删）。
- 模块：业务函数·通知推送
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-a2b2cee9` / TP `TP-381`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC delete_account，来源文件 backend/research-agent-source/tools/wechat_channel/accounts.py
  3. [执行] 发送 FUNC delete_account 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 delete_account 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：删除单账号凭据与同步游标（不在 accounts.json 索引里登记的账号也可强删）。）

### TP-382 · [正常] accounts.py::list_account_ids — 返回已登录账号 ID 列表（按注册顺序）。
- 模块：业务函数·通知推送
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-b6b7155c` / TP `TP-382`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC list_account_ids，来源文件 backend/research-agent-source/tools/wechat_channel/accounts.py
  3. [执行] 发送 FUNC list_account_ids 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 list_account_ids 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：返回已登录账号 ID 列表（按注册顺序）。）

### TP-383 · [正常] accounts.py::register_account_id — 把 accountId 加到持久化索引（已存在则跳过）。
- 模块：业务函数·通知推送
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-67d18ee4` / TP `TP-383`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC register_account_id，来源文件 backend/research-agent-source/tools/wechat_channel/accounts.py
  3. [执行] 发送 FUNC register_account_id 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 register_account_id 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：把 accountId 加到持久化索引（已存在则跳过）。）

### TP-384 · [正常] accounts.py::unregister_account_id — 从索引里移除（不删凭据文件，便于复登）。
- 模块：业务函数·通知推送
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-53381de5` / TP `TP-384`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC unregister_account_id，来源文件 backend/research-agent-source/tools/wechat_channel/accounts.py
  3. [执行] 发送 FUNC unregister_account_id 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 unregister_account_id 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：从索引里移除（不删凭据文件，便于复登）。）

### TP-385 · [正常] accounts.py::load_sync_buf — 读取上次的 get_updates_buf；缺失返回空串。
- 模块：业务函数·通知推送
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-ff68518b` / TP `TP-385`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC load_sync_buf，来源文件 backend/research-agent-source/tools/wechat_channel/accounts.py
  3. [执行] 发送 FUNC load_sync_buf 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 load_sync_buf 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：读取上次的 get_updates_buf；缺失返回空串。）

### TP-386 · [正常] accounts.py::save_sync_buf — 持久化最新 get_updates_buf。
- 模块：业务函数·通知推送
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-1b9cc73b` / TP `TP-386`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC save_sync_buf，来源文件 backend/research-agent-source/tools/wechat_channel/accounts.py
  3. [执行] 发送 FUNC save_sync_buf 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 save_sync_buf 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：持久化最新 get_updates_buf。）

### TP-387 · [正常] accounts.py::resolve_account — 汇总：账号文件里的 token + baseUrl + userId。
- 模块：业务函数·通知推送
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-6401975c` / TP `TP-387`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：FUNC resolve_account，来源文件 backend/research-agent-source/tools/wechat_channel/accounts.py
  3. [执行] 发送 FUNC resolve_account 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：业务逻辑 业务函数 resolve_account 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测；实现说明：汇总：账号文件里的 token + baseUrl + userId。）

### TP-388 · [正常] 页面可达 /login
- 模块：前端 Frontend
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-d6b9a773` / TP `TP-388`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：PAGE /login，来源文件 backend/research-agent-source/frontend/src/router/index.js
  3. [执行] 发送 PAGE /login 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：前端页面 /login 可导航加载：路由在 router 中定义，无白屏/404，关键区域正常渲染）

### TP-389 · [正常] 页面可达 /welcome
- 模块：前端 Frontend
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-06a3e5bc` / TP `TP-389`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：PAGE /welcome，来源文件 backend/research-agent-source/frontend/src/router/index.js
  3. [执行] 发送 PAGE /welcome 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：前端页面 /welcome 可导航加载：路由在 router 中定义，无白屏/404，关键区域正常渲染）

### TP-390 · [正常] 页面可达 /chat/:threadId
- 模块：前端 Frontend
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-1edff3c8` / TP `TP-390`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：PAGE /chat/:threadId，来源文件 backend/research-agent-source/frontend/src/router/index.js
  3. [执行] 发送 PAGE /chat/:threadId 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：前端页面 /chat/:threadId 可导航加载：路由在 router 中定义，无白屏/404，关键区域正常渲染）

### TP-391 · [正常] 页面可达 /experts
- 模块：前端 Frontend
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-9f97c94b` / TP `TP-391`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：PAGE /experts，来源文件 backend/research-agent-source/frontend/src/router/index.js
  3. [执行] 发送 PAGE /experts 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：前端页面 /experts 可导航加载：路由在 router 中定义，无白屏/404，关键区域正常渲染）

### TP-392 · [正常] 页面可达 /tools
- 模块：前端 Frontend
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-bab9d1f1` / TP `TP-392`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：PAGE /tools，来源文件 backend/research-agent-source/frontend/src/router/index.js
  3. [执行] 发送 PAGE /tools 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：前端页面 /tools 可导航加载：路由在 router 中定义，无白屏/404，关键区域正常渲染）

### TP-393 · [正常] 页面可达 /skills
- 模块：前端 Frontend
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-698661d8` / TP `TP-393`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：PAGE /skills，来源文件 backend/research-agent-source/frontend/src/router/index.js
  3. [执行] 发送 PAGE /skills 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：前端页面 /skills 可导航加载：路由在 router 中定义，无白屏/404，关键区域正常渲染）

### TP-394 · [正常] 页面可达 /tasks
- 模块：前端 Frontend
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-bb853f88` / TP `TP-394`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：PAGE /tasks，来源文件 backend/research-agent-source/frontend/src/router/index.js
  3. [执行] 发送 PAGE /tasks 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：前端页面 /tasks 可导航加载：路由在 router 中定义，无白屏/404，关键区域正常渲染）

### TP-395 · [正常] 页面可达 /settings
- 模块：前端 Frontend
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-36753be6` / TP `TP-395`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：PAGE /settings，来源文件 backend/research-agent-source/frontend/src/router/index.js
  3. [执行] 发送 PAGE /settings 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：前端页面 /settings 可导航加载：路由在 router 中定义，无白屏/404，关键区域正常渲染）

### TP-396 · [正常] 交互组件 交互组件 App.vue
- 模块：前端 Frontend
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-7a019220` / TP `TP-396`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：UI 交互组件 App.vue，来源文件 backend/research-agent-source/frontend/src/App.vue
  3. [执行] 发送 UI 交互组件 App.vue 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：交互组件 交互组件 App.vue 可正常触发：含交互钩子(@click/表单/上传)，操作有响应）

### TP-397 · [正常] 交互组件 交互组件 AgentsTab.vue
- 模块：前端 Frontend
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-f033fc41` / TP `TP-397`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：UI 交互组件 AgentsTab.vue，来源文件 backend/research-agent-source/frontend/src/components/AgentsTab.vue
  3. [执行] 发送 UI 交互组件 AgentsTab.vue 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：交互组件 交互组件 AgentsTab.vue 可正常触发：含交互钩子(@click/表单/上传)，操作有响应）

### TP-398 · [正常] 交互组件 交互组件 ArtifactCard.vue
- 模块：前端 Frontend
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-c9049607` / TP `TP-398`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：UI 交互组件 ArtifactCard.vue，来源文件 backend/research-agent-source/frontend/src/components/ArtifactCard.vue
  3. [执行] 发送 UI 交互组件 ArtifactCard.vue 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：交互组件 交互组件 ArtifactCard.vue 可正常触发：含交互钩子(@click/表单/上传)，操作有响应）

### TP-399 · [正常] 交互组件 交互组件 ArtifactDrawer.vue
- 模块：前端 Frontend
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-1feef904` / TP `TP-399`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：UI 交互组件 ArtifactDrawer.vue，来源文件 backend/research-agent-source/frontend/src/components/ArtifactDrawer.vue
  3. [执行] 发送 UI 交互组件 ArtifactDrawer.vue 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：交互组件 交互组件 ArtifactDrawer.vue 可正常触发：含交互钩子(@click/表单/上传)，操作有响应）

### TP-400 · [正常] 交互组件 交互组件 ArtifactPanel.vue
- 模块：前端 Frontend
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-b5583296` / TP `TP-400`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：UI 交互组件 ArtifactPanel.vue，来源文件 backend/research-agent-source/frontend/src/components/ArtifactPanel.vue
  3. [执行] 发送 UI 交互组件 ArtifactPanel.vue 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：交互组件 交互组件 ArtifactPanel.vue 可正常触发：含交互钩子(@click/表单/上传)，操作有响应）

### TP-401 · [正常] 交互组件 交互组件 AskUserCard.vue
- 模块：前端 Frontend
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-db08f506` / TP `TP-401`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：UI 交互组件 AskUserCard.vue，来源文件 backend/research-agent-source/frontend/src/components/AskUserCard.vue
  3. [执行] 发送 UI 交互组件 AskUserCard.vue 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：交互组件 交互组件 AskUserCard.vue 可正常触发：含交互钩子(@click/表单/上传)，操作有响应）

### TP-402 · [正常] 交互组件 交互组件 AuditSourceDrawer.vue
- 模块：前端 Frontend
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-6008bf1f` / TP `TP-402`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：UI 交互组件 AuditSourceDrawer.vue，来源文件 backend/research-agent-source/frontend/src/components/AuditSourceDrawer.vue
  3. [执行] 发送 UI 交互组件 AuditSourceDrawer.vue 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：交互组件 交互组件 AuditSourceDrawer.vue 可正常触发：含交互钩子(@click/表单/上传)，操作有响应）

### TP-403 · [正常] 交互组件 交互组件 ContributionsPage.vue
- 模块：前端 Frontend
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-5c4b2244` / TP `TP-403`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：UI 交互组件 ContributionsPage.vue，来源文件 backend/research-agent-source/frontend/src/components/ContributionsPage.vue
  3. [执行] 发送 UI 交互组件 ContributionsPage.vue 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：交互组件 交互组件 ContributionsPage.vue 可正常触发：含交互钩子(@click/表单/上传)，操作有响应）

### TP-404 · [正常] 交互组件 交互组件 LoginPage.vue
- 模块：前端 Frontend
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-1d6a0818` / TP `TP-404`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：UI 交互组件 LoginPage.vue，来源文件 backend/research-agent-source/frontend/src/components/LoginPage.vue
  3. [执行] 发送 UI 交互组件 LoginPage.vue 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：交互组件 交互组件 LoginPage.vue 可正常触发：含交互钩子(@click/表单/上传)，操作有响应）

### TP-405 · [正常] 交互组件 交互组件 MarkdownText.vue
- 模块：前端 Frontend
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-c91de92a` / TP `TP-405`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：UI 交互组件 MarkdownText.vue，来源文件 backend/research-agent-source/frontend/src/components/MarkdownText.vue
  3. [执行] 发送 UI 交互组件 MarkdownText.vue 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：交互组件 交互组件 MarkdownText.vue 可正常触发：含交互钩子(@click/表单/上传)，操作有响应）

### TP-406 · [正常] 交互组件 交互组件 SettingsTab.vue
- 模块：前端 Frontend
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-c13c2a23` / TP `TP-406`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：UI 交互组件 SettingsTab.vue，来源文件 backend/research-agent-source/frontend/src/components/SettingsTab.vue
  3. [执行] 发送 UI 交互组件 SettingsTab.vue 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：交互组件 交互组件 SettingsTab.vue 可正常触发：含交互钩子(@click/表单/上传)，操作有响应）

### TP-407 · [正常] 交互组件 交互组件 SkillsTab.vue
- 模块：前端 Frontend
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-5830c14a` / TP `TP-407`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：UI 交互组件 SkillsTab.vue，来源文件 backend/research-agent-source/frontend/src/components/SkillsTab.vue
  3. [执行] 发送 UI 交互组件 SkillsTab.vue 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：交互组件 交互组件 SkillsTab.vue 可正常触发：含交互钩子(@click/表单/上传)，操作有响应）

### TP-408 · [正常] 交互组件 交互组件 TasksTab.vue
- 模块：前端 Frontend
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-9a130fc7` / TP `TP-408`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：UI 交互组件 TasksTab.vue，来源文件 backend/research-agent-source/frontend/src/components/TasksTab.vue
  3. [执行] 发送 UI 交互组件 TasksTab.vue 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：交互组件 交互组件 TasksTab.vue 可正常触发：含交互钩子(@click/表单/上传)，操作有响应）

### TP-409 · [正常] 交互组件 交互组件 TeamSidebar.vue
- 模块：前端 Frontend
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-f54b4041` / TP `TP-409`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：UI 交互组件 TeamSidebar.vue，来源文件 backend/research-agent-source/frontend/src/components/TeamSidebar.vue
  3. [执行] 发送 UI 交互组件 TeamSidebar.vue 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：交互组件 交互组件 TeamSidebar.vue 可正常触发：含交互钩子(@click/表单/上传)，操作有响应）

### TP-410 · [正常] 交互组件 交互组件 ThinkingBlock.vue
- 模块：前端 Frontend
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-235d3028` / TP `TP-410`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：UI 交互组件 ThinkingBlock.vue，来源文件 backend/research-agent-source/frontend/src/components/ThinkingBlock.vue
  3. [执行] 发送 UI 交互组件 ThinkingBlock.vue 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：交互组件 交互组件 ThinkingBlock.vue 可正常触发：含交互钩子(@click/表单/上传)，操作有响应）

### TP-411 · [正常] 交互组件 交互组件 TodoPanel.vue
- 模块：前端 Frontend
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-30f30b1e` / TP `TP-411`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：UI 交互组件 TodoPanel.vue，来源文件 backend/research-agent-source/frontend/src/components/TodoPanel.vue
  3. [执行] 发送 UI 交互组件 TodoPanel.vue 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：交互组件 交互组件 TodoPanel.vue 可正常触发：含交互钩子(@click/表单/上传)，操作有响应）

### TP-412 · [正常] 交互组件 交互组件 ToolCallCard.vue
- 模块：前端 Frontend
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-9b3551ab` / TP `TP-412`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：UI 交互组件 ToolCallCard.vue，来源文件 backend/research-agent-source/frontend/src/components/ToolCallCard.vue
  3. [执行] 发送 UI 交互组件 ToolCallCard.vue 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：交互组件 交互组件 ToolCallCard.vue 可正常触发：含交互钩子(@click/表单/上传)，操作有响应）

### TP-413 · [正常] 交互组件 交互组件 ToolsTab.vue
- 模块：前端 Frontend
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-d22b7bfc` / TP `TP-413`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：UI 交互组件 ToolsTab.vue，来源文件 backend/research-agent-source/frontend/src/components/ToolsTab.vue
  3. [执行] 发送 UI 交互组件 ToolsTab.vue 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：交互组件 交互组件 ToolsTab.vue 可正常触发：含交互钩子(@click/表单/上传)，操作有响应）

### TP-414 · [正常] 交互组件 交互组件 KbPage.vue
- 模块：前端 Frontend
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-f4e4bde3` / TP `TP-414`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：UI 交互组件 KbPage.vue，来源文件 backend/research-agent-source/audit_ui/src/components/KbPage.vue
  3. [执行] 发送 UI 交互组件 KbPage.vue 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：交互组件 交互组件 KbPage.vue 可正常触发：含交互钩子(@click/表单/上传)，操作有响应）

### TP-415 · [正常] 交互组件 交互组件 TasksTab.vue
- 模块：前端 Frontend
- 类型：正常　优先级：P2　测试类型：全量
- 关联：FP `FP-76a78799` / TP `TP-415`
- 前置条件：被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
- 步骤：
  1. [前置] 被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）
  2. [准备] 构造请求：UI 交互组件 TasksTab.vue，来源文件 backend/research-agent-source/audit_ui/src/components/TasksTab.vue
  3. [执行] 发送 UI 交互组件 TasksTab.vue 请求并捕获响应
  4. [断言] 校验：响应状态码符合预期，关键业务字段完整（预期：交互组件 交互组件 TasksTab.vue 可正常触发：含交互钩子(@click/表单/上传)，操作有响应）
