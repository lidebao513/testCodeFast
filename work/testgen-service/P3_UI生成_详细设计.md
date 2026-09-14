# P3 详细设计 · 用「测试地址 + 账号密码」经 UI 层生成测试用例

> 状态：**M3.1–M3.2 已实现并验证**；M3.3（受保护页端到端验收）、M3.4（并入主链路）、M3.5（降级）待做。
> 关联：`P1-P3实现方案.md` §3（P3 运行时 UI 发现）、`engine/runtime_ui.py`（真实实现，见 §12 里程碑状态）。
> 设计基线：沿用既有「UI 优先」机制（`LAYER_STRATEGY=ui_first` + 用例 `coverage_role` 字段），
> 运行时发现的 UI 功能点与静态提取的功能点**汇入同一条主链路**，按名称去重、按 UI 优先排序。

---

## 0. 实施状态（截至 2026-09-14）

| 里程碑 | 状态 | 落地内容 |
|---|---|---|
| **M3.1** 配置与凭证模型 + 惰性导入探测 | ✅ 已实现 | `core/config.py` 新增 9 个 P3 配置项；`public_dict` 凭证只输出 `*_configured` 布尔；`_has_playwright()` 探测；`options_from_settings()` 映射 |
| **M3.2** `_login` + `_collect_page` + 路由优先级 | ✅ 已实现 | `engine/runtime_ui.py` 真实实现（登录/抓页/路由/控制台错误）；`tools/run_runtime_ui.py` 可执行入口 |
| **M3.3** 表单登录通路 + 受保护页发现 | 🟡 代码就绪、fixture 已验证 | `_login` 已实现；本地 fixture（登录页 + 受保护页）端到端通过；真实环境人工抽检待做 |
| **M3.4** `_to_functional_points` + pipeline 合并去重 | ⬜ 未做 | pipeline 已接线（`stage_runtime_ui` 真实调用），但发现结果**尚未并入功能点集合** |
| **M3.5** requests 降级 + 文档/技能同步 | ⬜ 未做 | `RuntimeUiOptions.degraded` 为占位字段 |

**已落地的事实（可直接引用）**：
- 依赖：`playwright` 走 `[project.optional-dependencies].runtime`，主链路默认不装，代码内惰性导入；
- 凭证红线已用测试锁死：`test_public_dict_hides_password_and_token`、`test_repo_has_no_plaintext_password_in_tracked_files`；
- 路由同源过滤 / 去重 / 上限、登录失败分类、控制台错误切片均有单测；
- 真浏览器端到端用本地 `http.server` 迷你站点验证（登录页 → 受保护页），无需外部环境。

---

## 1. 目标与价值

**一句话**：让平台能**真的打开被测网站、用给定账号登录、逐个页面点开**，把"真实渲染出来的页面与交互元素"变成测试用例——补上静态代码分析看不到的那一层。

静态分析（现有能力）与运行时发现的差异：

| 关注点 | 静态分析（已实现） | 运行时 UI 发现（本设计） |
|---|---|---|
| 依据 | 前端源码：路由声明、组件文件 | 真实浏览器渲染后的 DOM |
| 登录后菜单 | ❌ 看不到（由后端权限动态下发） | ✅ 能看到 |
| 懒加载区块 | ❌ 看不到（运行时才加载） | ✅ 能看到 |
| 真实表单字段/校验 | ⚠️ 只能读源码里的 JSX | ✅ 能读到实际渲染的 `input/button/form` |
| 数据依赖的页面 | ❌ 不知道是否可达 | ✅ 能断言可达/白屏/报错 |
| 控制台错误 | ❌ 无 | ✅ 可收集 |

**产出**：一批 `ftype=page/component` 的 `FunctionalPoint`（`source="runtime:<url>"`），
经既有的 `tp_expand → case_gen` 链路变成 UI 层用例。

---

## 2. 范围界定（做什么 / 不做什么）

**做**：
- 用 Playwright 打开测试地址；支持**账号+密码表单登录**与**令牌/自定义 Header 注入**两种鉴权方式；
- 登录后按路由清单遍历页面，抓取导航项、表单、按钮等可交互元素；
- 收集页面控制台错误与关键网络失败；
- 产出与 `fp_extract` 同构的 `FunctionalPoint`，按名称与静态结果合并去重。

**不做（本期）**：
- ❌ 不做用例**执行**（点击/断言）——那是 `engine/executor.py` 的职责（另立里程碑）；
- ❌ 不做自愈/自修复；
- ❌ 不绕过被测系统的鉴权机制（不注入后门、不篡改前端）；
- ❌ 不在局域网外/未授权环境运行。

---

## 3. 总体流程

```
[配置] base_url + account/password（.env 注入）
   │
   ▼
① 启动浏览器（Playwright chromium，headless 可配）
   │
   ▼
② 打开 base_url → 检测登录表单 → 填账号密码 → 提交 → 等 SPA 就绪
   │   └─ 失败 → NotImplementedYet/EngineError（分类：凭证错误 / 超时 / 选择器未命中）
   ▼
③ 会话保持（同一 browser context，复用 cookie/localStorage）
   │
   ▼
④ 路由清单（优先级：用户显式清单 > 静态 page FP 的路径 > 首页可点链接）
   │
   ▼
⑤ 逐路由 goto：断言可渲染、抓可见导航/表单/按钮、收集控制台错误
   │
   ▼
⑥ 产出 FunctionalPoint（page/component，source=runtime:<url>）
   │
   ▼
⑦ 与静态功能点合并去重 → 汇入 pipeline（stage_cases 之前）
```

---

## 4. 配置与凭证模型

### 4.1 新增/调整的配置项（`core/config.py`）

| 环境变量 | 字段 | 默认 | 说明 |
|---|---|---|---|
| `RUNTIME_UI_ENABLED` | `runtime_ui_enabled` | `off` | 总开关（已存在） |
| `RUNTIME_BASE_URL` | `runtime_base_url` | 空 | 被测环境地址（已存在） |
| `PLAYWRIGHT_HEADLESS` | `playwright_headless` | `on` | 有头/无头（已存在） |
| `RUNTIME_UI_TIMEOUT` | `runtime_ui_timeout` | `30` | 单页超时秒数（**新增**） |
| `RUNTIME_ROUTES` | `runtime_routes` | 空 | 逗号分隔的显式路由清单（**新增**） |
| `RUNTIME_LOGIN_USER` | `runtime_login_user` | 空 | 登录账号（**新增**） |
| `RUNTIME_LOGIN_PASSWORD` | `runtime_login_password` | 空 | 登录密码（**新增，绝不入 public_dict / 日志**） |
| `RUNTIME_AUTH_TOKEN` | `runtime_auth_token_env` 指向的环境变量 | 空 | 令牌型鉴权的取值来源（已存在字段，语义保留） |

> **凭证优先级**：账号密码（表单登录）> 令牌（Header 注入）> 匿名（两者皆空时直连）。
> 三者都没有时，仍可对**无需登录**的公开页做发现。

### 4.2 凭证安全红线（硬约束）

1. 密码**只从 `.env` / 环境变量读取**，绝不硬编码、绝不写入代码库；
2. `Settings.public_dict()` **不输出** `runtime_login_password`（也不输出令牌值，仅输出 `bool` 是否已配置）；
3. 结构化日志**脱敏**：字段名含 `password/token/secret/authorization` 的值一律替换为 `***`（沿用 `core/log.py` 既有约定）；
4. 凭证**不进** `testgen.db`、不进产物 JSON、不进用例文本；
5. 浏览器 profile 用**临时目录**，`finally` 中清理，不留驻 cookie。

---

## 5. 依赖与安装

| 项 | 说明 |
|---|---|
| Python 依赖 | `playwright`（新增；**运行时惰性导入**，默认链路不受影响） |
| 浏览器内核 | `python -m playwright install chromium`（约 150MB） |
| 声明位置 | `requirements.txt` / `pyproject.toml` 的 `[project.optional-dependencies]` 建议新增 `runtime = ["playwright"]`，**默认不装**，仅在启用 P3 时安装 |

**沙箱/网络风险与降级**：
- 若浏览器内核无法下载（代理/沙箱限制）→ 降级为「`requests` 拉 HTML + 解析 DOM」：
  仅覆盖**服务端渲染**页，**不覆盖** JS 懒加载与登录后菜单；结果中标注 `degraded=true`。
- 若环境完全不可跑浏览器 → 提示用户在**本机（非沙箱）**运行 P3 阶段，或改由用户手填路由清单。

---

## 6. 数据契约（只增不破）

### 6.1 现有骨架（保留，已落地）

```python
@dataclass
class RuntimeUiOptions:
    mode: str = RUNTIME_UI_PLAYWRIGHT
    headless: bool = True
    base_url: str = ""
    auth_token: str = ""      # 来自环境变量，不入库
    timeout: int = 30

@dataclass
class UiElement:
    selector: str
    kind: str = ""
    text: str = ""
    visible: bool = False

@dataclass
class RuntimeUiResult:
    base_url: str = ""
    elements: list[UiElement] = field(default_factory=list)
    console_errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
```

### 6.2 本期扩展（Additive）

```python
@dataclass
class RuntimeUiOptions:
    ...                       # 以上保留
    login_user: str = ""      # 新增：表单登录账号
    login_password: str = ""  # 新增：表单登录密码（不入库/不日志）
    routes: list[str] = field(default_factory=list)   # 新增：显式路由清单
    login_url: str = ""       # 新增：登录页地址（缺省用 base_url）
    degraded: bool = False    # 新增：是否降级为 requests 抓取

@dataclass
class UiPage:                 # 新增：一个被发现的可达页面
    url: str
    path: str
    title: str = ""
    reachable: bool = True
    console_errors: list[str] = field(default_factory=list)
    elements: list[UiElement] = field(default_factory=list)

@dataclass
class RuntimeUiResult:
    base_url: str = ""
    elements: list[UiElement] = field(default_factory=list)
    console_errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    pages: list[UiPage] = field(default_factory=list)  # 新增：按页聚合
    degraded: bool = False                             # 新增
```

### 6.3 产出的功能点（复用既有契约，不新造）

运行时发现的页面/组件直接产出 `core.contracts.FunctionalPoint`：

| 字段 | 取值 |
|---|---|
| `ftype` | `page`（页面） / `component`（含交互元素的区块） |
| `name` | `page` → 路径（如 `/pc/tasks`）；`component` → 组件/区块标识 |
| `title` | 页面标题或导航项文本 |
| `module` | 由路径首段推导（如 `/pc/tasks` → `pc`） |
| `file_path` / `source` | `runtime:<url>`（**非真实文件路径**，便于区隔） |
| `commit_ref` | 空（运行时发现无版本概念） |
| `review_status` | 跟随 `REVIEW_GATE` |

> **编号稳定性**：`fp_id = fp_id_of("page"|"component", "runtime:<url>", name)`，
> 依赖 URL 与路径名——同一环境重复跑编号不变（沿用 `contracts.fp_id_of`）。

---

## 7. 接口签名

```python
# engine/runtime_ui.py（现有桩函数，本期补实现）
def discover_ui(options: RuntimeUiOptions | None = None) -> RuntimeUiResult: ...
    """主入口：登录 + 遍历路由 + 抓元素 + 收控制台错误（同步封装 Playwright sync API）。"""

# 内部拆解（均私有，便于单测）
def _login(page, options) -> None: ...
    """检测登录表单并提交；无表单则视为已登录/匿名可访问。"""

def _resolve_routes(options, static_paths: list[str]) -> list[str]: ...
    """路由清单：显式 routes > static_paths > 首页可点链接。"""

def _collect_page(page, url) -> UiPage: ...
    """抓取单页：可达性、控制台错误、导航/表单/按钮元素。"""

def _to_functional_points(result: RuntimeUiResult) -> list[FunctionalPoint]: ...
    """RuntimeUiResult → FunctionalPoint（page/component）。"""

def _has_playwright() -> bool: ...
    """探测 playwright 是否可用（决定是否降级）。"""
```

---

## 8. 执行流程拆解（细化）

### 8.1 登录（`_login`）

1. `page.goto(login_url or base_url)`，等待 `domcontentloaded`；
2. 定位登录表单：
   - 优先 `input[type=password]`（密码框）；
   - 相邻 `input[type=text]` 或 `input[name*=user|account|email]` 作为账号框；
   - 提交按钮：`button[type=submit]` 或含"登录/登陆/sign in/login"文本的按钮。
3. 填值并提交，等待跳转/网络空闲；
4. **判定成功**：离开登录页（URL 变化）且能定位到登录后特征元素（导航/菜单）；
5. **判定失败**：仍停留在登录页或出现错误提示 → 抛 `EngineError("登录失败：请核对账号密码或登录选择器")`（**不回显密码**）。

### 8.2 路由来源优先级（`_resolve_routes`）

| 优先级 | 来源 | 说明 |
|---|---|---|
| 1 | `RUNTIME_ROUTES` 显式清单 | 用户最可控 |
| 2 | 静态 `page` FP 的路径 | 复用静态已提取的路由（`fp_extract` 产出） |
| 3 | 首页可点链接爬取 | 兜底：抓 `<a href>` 中同源链接（限深度 1，去重，设上限） |

> 仅遍历**同源**路径；忽略外链、`#` 锚点、`javascript:`。设单次上限（如 ≤ 100 页）防爆。

### 8.3 单页抓取（`_collect_page`）

- 可达性：`goto` 成功 + 无未捕获导航错误 + 非白屏（正文节点数 > 阈值）；
- 控制台错误：监听 `page.on("console")` 中 `error` 级别 + `page.on("pageerror")`；
- 元素抓取：
  - 导航：`nav a, aside a, [role=menuitem]`（登录后才可见的权限菜单）；
  - 表单：`form`、`input`、`select`、`textarea`、`button`；
  - 每个元素记录 `selector / kind / text / visible`。

### 8.4 产出与合并（`_to_functional_points` + pipeline）

- 每个**可达页面** → 1 条 `page` FP；
- 每个**含交互元素的可达区块** → 1 条 `component` FP；
- 合并规则：
  - 与静态 FP **同名**（同 `ftype` + 同 `name`）→ **运行时优先**（`file_path` 改为 `runtime:<url>`），静态版丢弃；
  - 仅静态有 → 保留静态；
  - 仅运行时有的 → 追加（这正是价值所在：静态看不到的页）。
- `result.notes` 记录：`运行时补入 N 条 UI 功能点（静态漏掉 M 条）`。

---

## 9. pipeline 接入

`engine/pipeline.py` 现有钩子已就位（`stage_runtime_ui`，受 `s.runtime_ui_enabled` 守卫），本期把桩换成真实实现：

```python
result.functional_points = stage_extract(...)
if s.runtime_ui_enabled:                       # 在「测试点展开」之前合并运行时 FP
    result.functional_points = _merge_runtime_fps(result, stage_runtime_ui(opts, result, progress))
_, tag_by_fp = stage_tag(...)
tps = stage_test_points(...)                   # 运行时补入的 FP 也正常展开测试点
```

要点：
- 必须在 `stage_tag` / `stage_test_points` **之前**合并，否则运行时 FP 不参与展开；
- 增量（`incremental`）模式下运行时 FP **一律标「全量」**（运行时没有 diff 概念）；
- 幂等：同一环境重复跑，`fp_id` 稳定 → 落库走 `replace/reconcile`，不产生重复用例。

---

## 10. 错误处理与降级矩阵

| 场景 | 处理 | 状态/提示 |
|---|---|---|
| 未装 playwright / 内核缺失 | 降级 requests 抓 HTML | `degraded=true`，note 说明 |
| 浏览器启动失败 | 抛 `EngineError`，附环境信息 | 不吞异常 |
| 登录失败 | 抛 `EngineError`（不回显密码） | 分类：凭证/超时/选择器 |
| 单页超时 | 跳过该页并记录 | `pages[].reachable=false` |
| 单页白屏/JS 报错 | 记录控制台错误，仍产出 FP（标记） | `console_errors` 非空 |
| 全站不可达 | 抛 `EngineError` | 阻断 P3 阶段，主链路其余不受影响 |

---

## 11. 测试策略

新增 `tests/test_p3_runtime_ui.py`：

1. **静态可测的部分**（无需浏览器，必跑）：
   - `_resolve_routes`：优先级、同源过滤、去重、上限；
   - `_to_functional_points`：页面/组件 → FP 字段正确、`source=runtime:`、`fp_id` 稳定；
   - 合并去重函数：运行时覆盖静态、仅静态保留、仅运行时追加；
   - 降级分支：`_has_playwright()` 为 False 时走 requests 路径；
   - `_login` 的选择器识别：用假 page 对象（stub）验证定位逻辑。
2. **真浏览器端到端**（`pytest.importorskip("playwright")`，无则跳过）：
   - 本地 `http.server` 起一个迷你站点：**登录页 + 受保护页**（静态源码里没有该页的路由声明）；
   - 断言 `discover_ui` 能发现「受保护页」——即**静态漏掉、运行时可补**的验收核心。

> 注：Windows + Playwright 的真浏览器测试已在本机验证过可行（见 `windows-browser-e2e-selftest` 技能）。

---

## 12. 里程碑拆分

| 里程碑 | 内容 | 可独立验收 |
|---|---|---|
| **M3.1** | 配置与凭证模型（含 account/password、脱敏、public_dict）+ playwright 惰性导入与可用性探测 | 配置单测 + `_has_playwright` 分支 |
| **M3.2** | `_login` + `_collect_page` + 路由来源优先级（无登录公开页先打通） | 本地 fixture 无登录页端到端 |
| **M3.3** | 表单登录通路（账号密码）+ 受保护页发现 | fixture 登录页端到端，断言发现受保护页 |
| **M3.4** | `_to_functional_points` + pipeline 合并去重 + 增量标「全量」 | pipeline 集成测试；静态/运行时可量化对比 |
| **M3.5** | 降级路径（requests 兜底）+ 文档 + 与 qa-test-points 技能同步 | 降级分支单测 |

---

## 13. 验收标准（可量化）

开启 `RUNTIME_UI_ENABLED=on` + 提供测试地址与账号后：

1. `UI 层功能点数量` 较纯静态**上升**（补入登录后菜单/懒加载页）；
2. 被静态漏掉、而运行时可发现的页面**全部被补入**（fixture 场景 ≥ 1 条，真实环境人工抽检）；
3. 每条运行时 FP 的 `source` 为 `runtime:<url>`，`coverage_role` 正确标注（UI 层 → `primary`）；
4. **接口层功能点不变**（运行时只增 UI 面，不动接口）；
5. 追溯孤儿测试点 = **0**；重复跑**不产生**重复用例（幂等）；
6. 任何日志 / 产物 / DB 中**不出现**明文密码。

---

## 14. 风险与限制

| 风险 | 影响 | 缓解 |
|---|---|---|
| 登录选择器因系统而异 | 登录失败 | 配置化选择器（后续）+ 明确的失败提示；优先标准 `type=password` |
| 动态路由/权限导致路由清单不全 | 覆盖不全 | 首页链接爬取兜底 + 用户可显式给清单 |
| 浏览器内核下载受限 | 无法运行 | requests 降级 + 本机运行指引 |
| 页面加载慢/无限流 | 遍历耗时 | 单页超时 + 全站上限 + 跳过策略 |
| 被测环境有风控/验证码 | 登录受阻 | 明确不绕过；提示用户改用测试专用账号或关闭风控 |
| 密码泄漏 | 安全事件 | 见 §4.2 五条红线（不入库/不日志/不产物/临时 profile） |

---

## 15. 后续衔接

- 本文落地后，把「运行时 UI 发现约定」「凭证注入红线」回写 `~/.workbuddy/skills/qa-test-points/SKILL.md`；
- `engine/executor.py`（用例执行器）另行设计：UI 用 Playwright、接口用 requests，为自愈/自修复预留接口；
- 与「测试加速平台服务化」衔接：运行时 UI 发现作为**发布后启动验证**的一环（探活 → 登录 → 关键页可达）。
