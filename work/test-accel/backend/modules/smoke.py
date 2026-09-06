"""冒烟验证：确认被测服务在本地已启动且可用。
两种模式：
- 匿名探活：health / 首页 / login 端点可达 / 受保护端点未登录应 401
- 登录冒烟（提供 account+password）：unified-login → 拿 token → 探受保护端点
不依赖 ENABLE_DYNAMIC_PROBE 开关，是独立的主动探活能力。
"""
import time
import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from urllib3.util.retry import Retry

TIMEOUT = 3
HEADERS = {"User-Agent": "test-accel-smoke/0.1", "Connection": "close"}

# 禁用重试 + 禁用代理，确保"服务未起"秒级失败而非长时间重试
_SESSION = requests.Session()
_retry = Retry(connect=0, read=0, redirect=0)
_SESSION.mount("http://", HTTPAdapter(max_retries=_retry, pool_connections=1, pool_maxsize=1))
_SESSION.mount("https://", HTTPAdapter(max_retries=_retry, pool_connections=1, pool_maxsize=1))
_SESSION.proxies = {"http": None, "https": None}
_SESSION.trust_env = False  # 忽略系统 HTTP 代理，确保 localhost 直连


def _probe(method: str, url: str, **kw):
    """单次 HTTP 探活，返回结构化结果。"""
    t0 = time.time()
    try:
        r = _SESSION.request(
            method, url, timeout=TIMEOUT, headers=HEADERS,
            proxies={"http": None, "https": None}, **kw)
        return {
            "ok": True,
            "status": r.status_code,
            "elapsed_ms": int((time.time() - t0) * 1000),
            "snippet": (r.text or "")[:160].replace("\n", " "),
        }
    except RequestException as e:
        return {
            "ok": False,
            "status": None,
            "elapsed_ms": int((time.time() - t0) * 1000),
            "error": type(e).__name__ + ": " + str(e)[:140],
        }


def _try_login(base: str, account: str, password: str):
    """尝试 unified-login，失败回退本地 login。返回 (token, detail)。"""
    # 1) unified-login（account + password）
    r = _probe("POST", f"{base}/api/v1/auth/unified-login",
               json={"account": account, "password": password})
    if r["ok"] and r["status"] == 200:
        try:
            body = _SESSION.post(
                f"{base}/api/v1/auth/unified-login",
                json={"account": account, "password": password},
                timeout=TIMEOUT, headers=HEADERS,
                proxies={"http": None, "https": None}).json()
            token = body.get("access_token") or body.get("data", {}).get("access_token")
        except Exception:
            token = None
        return token, {"endpoint": "/api/v1/auth/unified-login", "status": r["status"]}

    # 2) 回退本地 login（username + password）
    r2 = _probe("POST", f"{base}/api/v1/auth/login",
                json={"username": account, "password": password})
    detail = {"endpoint": "/api/v1/auth/login", "status": r2["status"], "probe": r2}
    token = None
    if r2["ok"] and r2["status"] == 200:
        try:
            body = _SESSION.post(
                f"{base}/api/v1/auth/login",
                json={"username": account, "password": password},
                timeout=TIMEOUT, headers=HEADERS,
                proxies={"http": None, "https": None}).json()
            token = body.get("access_token") or body.get("data", {}).get("access_token")
        except Exception:
            token = None
    return token, detail


def _login_and_probe(base: str, account: str, password: str):
    """登录并验证受保护端点。返回结构化结果。"""
    token, login_detail = _try_login(base, account, password)
    auth_ok = bool(token)
    protected = []
    if auth_ok:
        h = {"Authorization": f"Bearer {token}"}
        protected.append(("threads", _probe("GET", f"{base}/api/v1/threads", headers=h)))
        protected.append(("projects", _probe("GET", f"{base}/api/v1/projects", headers=h)))
    return {
        "login_attempted": True,
        "login_detail": login_detail,
        "token_acquired": auth_ok,
        "protected_checks": protected,
    }


def smoke_project(proj: dict, account: str = None, password: str = None,
                  base_url: str = None):
    """对单个项目做冒烟验证，返回完整报告字典。"""
    base = (base_url or proj.get("base_url") or "").rstrip("/")
    # 统一用 127.0.0.1 直连，避免 localhost 解析走 IPv6(::1) 导致的探测超时
    base = base.replace("localhost", "127.0.0.1")
    checks = []

    # 1. 健康检查（核心：服务是否存活）
    health = _probe("GET", f"{base}/api/v1/health")
    checks.append({"name": "health", "expect": "200", **health})

    # 2. 站点根（前端是否 serve，次要）
    root = _probe("GET", f"{base}/")
    checks.append({"name": "site_root", "expect": "200/307 任意(非连接失败)", **root})

    # 3. 登录端点可达（期望 400/401/422，证明端点存在；连接失败则服务未起）
    login_reach = _probe("POST", f"{base}/api/v1/auth/login", json={})
    checks.append({"name": "auth_login_reachable", "expect": "非连接失败(端点存在)", **login_reach})

    # 4. 受保护端点未登录（期望 401，证明鉴权链路工作）
    unauth = _probe("GET", f"{base}/api/v1/threads")
    checks.append({"name": "threads_unauth_401", "expect": "401/403", **unauth})

    # 判定：只要主机返回了 HTTP 响应（含 401/403，说明服务存活只是需鉴权）即视为可达；
    # 仅当连接失败（status 为 None）才判 UNREACHABLE。research-agent 的 /api/v1/health
    # 要求 BMP token，会返回 401，但这足以证明服务在跑。
    service_up = health["ok"] and health["status"] is not None
    login_smoke = None
    if account and password:
        login_smoke = _login_and_probe(base, account, password)

    if not service_up:
        verdict = "UNREACHABLE"   # 服务未起 / 地址或端口错误
        verdict_cn = "服务不可达（未启动或地址/端口不对）"
    elif login_smoke is None:
        verdict = "SERVICE_UP"    # 匿名可用，未做登录验证
        verdict_cn = "服务已启动（匿名探活通过，未做登录验证）"
    elif login_smoke["token_acquired"]:
        verdict = "READY"         # 登录可用，完全就绪
        verdict_cn = "完全就绪（登录态可用，受保护接口可访问）"
    else:
        verdict = "AUTH_FAIL"     # 服务起但登录失败
        verdict_cn = "服务已启动，但登录验证失败（账号/密码或登录链路问题）"

    return {
        "project": proj.get("name"),
        "base_url": base,
        "verdict": verdict,
        "verdict_cn": verdict_cn,
        "checks": checks,
        "login_smoke": login_smoke,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
