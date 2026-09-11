"""被测系统鉴权态获取与复用（阶段4 批次3 · D-②1）。

设计要点
1. **凭据只从环境变量或 projects.auth_config 读取**，绝不在代码里硬编码（D-②8 同源要求）。
2. 与 `smoke.py` 的登录链路保持一致：`unified-login`（account+password）优先，
   失败回退 `/api/v1/auth/login`（username+password）。
3. 进程内缓存 token（默认 30 分钟），避免 263 条用例逐条登录；提供 `invalidate()`
   供 401 后强制刷新。
4. 全程禁用系统代理 / trust_env——本机透明代理会拦截 127.0.0.1 导致假性失败。
5. 线程安全：取 token 走全局锁，配合 executor 的并发执行（D-②2）。
"""

import json
import threading
import time

from backend.config import settings


_LOCK = threading.Lock()
_TOKEN_CACHE: dict[
    str, dict
] = {}  # base -> {"token": str, "ts": float, "source": str, "detail": dict}


def _new_session():
    import requests
    from requests.adapters import HTTPAdapter

    s = requests.Session()
    s.trust_env = False  # 忽略 HTTP(S)_PROXY 环境变量
    s.proxies = {"http": None, "https": None}
    s.mount("http://", HTTPAdapter(pool_connections=4, pool_maxsize=8))
    s.mount("https://", HTTPAdapter(pool_connections=4, pool_maxsize=8))
    return s


_SESSION = None


def session():
    global _SESSION
    if _SESSION is None:
        _SESSION = _new_session()
    return _SESSION


def _base(proj) -> str:
    return (proj.get("base_url") or "").rstrip("/").replace("localhost", "127.0.0.1")


def resolve_creds(proj):
    """解析凭据：projects.auth_config（JSON）优先，其次环境变量。

    返回 dict：{account, password, otp, token, login_path, fallback_path, source}
    """
    cfg = {}
    raw = proj.get("auth_config")
    if raw:
        try:
            cfg = json.loads(raw) if isinstance(raw, str) else (raw or {})
        except Exception:
            cfg = {}
    return {
        "account": cfg.get("account") or settings.RA_ACCOUNT,
        "password": cfg.get("password") or settings.RA_PASSWORD,
        "otp": cfg.get("otp") or settings.RA_OTP,
        "token": cfg.get("token") or settings.RA_AUTH_TOKEN,
        "login_path": cfg.get("login_path") or settings.RA_LOGIN_PATH,
        "fallback_path": cfg.get("fallback_path") or settings.RA_LOGIN_FALLBACK_PATH,
        "source": "project.auth_config" if cfg else "env",
    }


def _extract_token(body):
    """从登录响应里提取 token，兼容 token / access_token / data.* 多种包裹。"""
    if not isinstance(body, dict):
        return None
    for k in ("access_token", "token", "accessToken"):
        if body.get(k):
            return body[k]
    data = body.get("data")
    if isinstance(data, dict):
        for k in ("access_token", "token", "accessToken"):
            if data.get(k):
                return data[k]
    return None


def _do_login(base, creds):
    """实际登录，返回 (token, detail)。失败返回 (None, detail)。"""
    s = session()
    detail = {}
    payload_primary = {"account": creds["account"], "password": creds["password"]}
    if creds.get("otp"):
        payload_primary["otp"] = creds["otp"]
    attempts = [
        (creds["login_path"], payload_primary),
        # 回退端点用 username 语义
        (creds["fallback_path"], {"username": creds["account"], "password": creds["password"]}),
    ]
    for path, payload in attempts:
        if not path:
            continue
        try:
            r = s.post(base + path, json=payload, timeout=8)
        except Exception as e:
            detail[path] = f"{type(e).__name__}: {str(e)[:120]}"
            continue
        detail[path] = r.status_code
        if r.status_code == 200:
            try:
                tok = _extract_token(r.json())
            except Exception:
                tok = None
            if tok:
                return tok, {"endpoint": path, "status": 200}
    return None, detail


def get_token(proj, force_refresh: bool = False):
    """取得可用 token。返回 (token|None, info)。

    info = {"source": static_token|login|cache|none, "reason": str, "detail": {...}}
    """
    base = _base(proj)
    if not base:
        return None, {"source": "none", "reason": "项目未配置 base_url"}
    creds = resolve_creds(proj)

    # 1) 静态 token（外部注入，无需登录）
    if creds.get("token"):
        return creds["token"], {"source": "static_token", "reason": "使用已配置的静态 token"}

    if not (creds.get("account") and creds.get("password")):
        return None, {
            "source": "none",
            "reason": "未配置账号密码（RA_ACCOUNT/RA_PASSWORD 或 projects.auth_config）",
        }

    with _LOCK:
        cached = _TOKEN_CACHE.get(base)
        now = time.time()
        if (not force_refresh) and cached and (now - cached["ts"] < settings.AUTH_TOKEN_TTL):
            return cached["token"], {
                "source": "cache",
                "reason": f"复用缓存 token（{int(now - cached['ts'])}s 前获取）",
            }
        tok, detail = _do_login(base, creds)
        if tok:
            _TOKEN_CACHE[base] = {"token": tok, "ts": now, "source": "login", "detail": detail}
            return tok, {"source": "login", "reason": "登录获取 token 成功", "detail": detail}
        return None, {"source": "none", "reason": "登录失败或未返回 token", "detail": detail}


def invalidate(proj=None):
    """清除 token 缓存（401/403 后强制刷新）。proj 为空则清空全部。"""
    with _LOCK:
        if proj is None:
            _TOKEN_CACHE.clear()
        else:
            _TOKEN_CACHE.pop(_base(proj), None)


def auth_headers(proj, force_refresh: bool = False):
    """返回可注入 requests 的鉴权头 + 元信息：(headers, info)。"""
    if not settings.AUTH_AUTO_LOGIN:
        return {}, {"source": "disabled", "reason": "AUTH_AUTO_LOGIN=off"}
    tok, info = get_token(proj, force_refresh=force_refresh)
    if not tok:
        return {}, info
    return {"Authorization": f"Bearer {tok}"}, info
