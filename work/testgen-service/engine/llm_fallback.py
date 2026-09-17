"""引擎 · 统一 LLM 降级链（engine/llm_fallback）。

唯一入口：所有调用大模型的地方（专家通道 ExpertLLMClient、语义增强 LLMClient、
LLM 用例设计 DesignOptions 复用的 LLMClient）统一委托 `chat_with_fallback`，
**绝不**在每个调用点各自实现降级逻辑（统一化，避免散落、易漏）。

降级触发：当某模型返回 403/404/429 且消息含额度关键字（如
`AllocationQuota.FreeTierOnly.`）——视作该免费模型暂不可用，按 `model_chain`
顺序切到下一个模型。

快速切换：进程内缓存「已验证可用的最优模型下标」，按 (base_url, channel) 维度
隔离；二次调用直接命中已验证模型，避免每次都从链头重测坏模型（大模型停止后快速恢复）。
"""

from __future__ import annotations

from typing import Any

from core.errors import LLMError
from core.log import get_logger


log = get_logger(__name__)

# 进程内缓存：(base_url, channel) -> 已验证可用模型下标
_best_index: dict[tuple[str, str], int] = {}

# 免费额度耗尽 / 模型不可用 的关键字（作为降级触发信号，视作该模型暂不可用）
_QUOTA_HINTS = (
    "AllocationQuota.FreeTierOnly",
    "FreeTierOnly",
    "quota",
    "rate_limit",
)

# 视觉模型关键字（与 engine/expert/llm.is_vision_model 同源口径，本地自包含避免循环依赖）
_VISION_HINTS = ("vision", "vl", "qwen-vl", "gpt-4o", "gpt-4-turbo", "claude", "gemini")


def _is_quota_unavailable(exc: Exception) -> bool:
    """判断异常是否为「该模型暂不可用（免费额度耗尽 / 限流 / 模型下架）」——应降级到下一个模型。

    命中条件：HTTP 403/404/429（额度/限流/模型不存在），或错误文本含额度关键字。
    注意：**401 鉴权失败**不命中——同一 key 对所有模型都失败，切下一个无意义，应快速失败。
    """
    status = getattr(exc, "status_code", None)
    if status in (403, 404, 429):
        return True
    msg = (str(getattr(exc, "message", "")) + " " + str(exc)).lower()
    return any(h.lower() in msg for h in _QUOTA_HINTS)


def _model_is_vision(model: str) -> bool:
    """粗略判断模型是否视觉模型（仅用于降级时是否带图的安全决策）。"""
    m = (model or "").lower()
    return any(h in m for h in _VISION_HINTS)


def _strip_images(messages: list[dict[str, Any]], model: str) -> list[dict[str, Any]]:
    """若候选模型非视觉模型，则剥离消息体里的 image_url，避免非视觉模型报错打断降级链。"""
    if _model_is_vision(model):
        return messages
    out: list[dict[str, Any]] = []
    changed = False
    for msg in messages:
        content = msg.get("content")
        if isinstance(content, list):
            kept = [
                p for p in content if not (isinstance(p, dict) and p.get("type") == "image_url")
            ]
            if len(kept) != len(content):
                changed = True
            # 剥离图片后若仅剩文本，则折叠为纯文本（与「单文本消息」形态一致）
            text_parts = [p for p in kept if isinstance(p, dict) and p.get("type") == "text"]
            if text_parts:
                text = " ".join(str(p.get("text", "")) for p in text_parts)
                out.append({**msg, "content": text})
                continue
            out.append({**msg, "content": kept})
        else:
            out.append(msg)
    if changed:
        log.info("模型 %s 非视觉，已剥离 image_url 后降级调用", model)
    return out


def chat_with_fallback(
    *,
    channel: str,
    api_key: str,
    base_url: str,
    timeout: int,
    model: str,
    model_chain: list[str] | None,
    messages: list[dict[str, Any]],
    temperature: float = 0.2,
) -> Any:
    """统一 LLM 调用入口：按降级链顺序尝试模型，返回首个成功响应的 `chat.completions` 对象。

    参数：
    - channel：通道标识（"expert" / "llm"），用于最优模型缓存隔离；
    - api_key / base_url：OpenAI 兼容凭证（同一 key 复用，不入库/不入日志）；
    - model：主模型（降级链为空时回退用）；
    - model_chain：降级顺序（用户给定顺序），可为空（仅用 model）；
    - messages：已构造好的消息体（图片是否包含由调用方决定，本函数按候选模型视觉能力兜底剥离）。

    行为：
    - 命中额度/限流不可用 → 切下一个模型；
    - 其他异常（鉴权/网络/参数）→ 直接抛 LLMError，不降级；
    - 全链失败 → 抛 LLMError("all models in chain failed")。
    """
    chain = [m for m in (model_chain or []) if m] or [model]
    if not chain:
        raise LLMError("未提供可用模型（model / model_chain 均为空）")
    if not api_key or not base_url:
        raise LLMError("专家/LLM 未配置（需 api_key + base_url）")

    cache_key = (base_url, channel)
    best = _best_index.get(cache_key, 0)
    # 从已验证下标起尝试；到尾后回绕到链头，保证覆盖全链（含 best 之前可能已恢复的模型）
    order = list(range(best, len(chain))) + list(range(0, best))

    try:
        from openai import OpenAI
    except ImportError as exc:  # pragma: no cover - 依赖缺失
        raise LLMError("未安装 openai 依赖，无法调用 LLM") from exc

    client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
    last_err: Exception | None = None
    for idx in order:
        m = chain[idx]
        try:
            resp = client.chat.completions.create(
                model=m,
                messages=_strip_images(messages, m),
                temperature=temperature,
            )
        except Exception as exc:  # 需区分「额度不可用→降级」与「真实错误→失败」
            if _is_quota_unavailable(exc):
                last_err = exc
                log.warning(
                    "模型 %s 暂不可用（免费额度/限流/下架），降级到下一个：%s",
                    m,
                    str(exc)[:160],
                )
                continue
            # 真实错误（鉴权失败 / 网络 / 参数）：不降级，直接失败
            raise LLMError(f"模型 {m} 调用失败：{type(exc).__name__}") from exc
        # 成功：更新最优模型缓存并返回
        _best_index[cache_key] = idx
        log.info("模型 %s 调用成功（channel=%s）", m, channel)
        return resp

    raise LLMError(
        f"all models in chain failed（共 {len(chain)} 个）："
        f"{type(last_err).__name__ if last_err else 'unknown'}"
    )


def reset_fallback_cache() -> None:
    """清空最优模型缓存（测试用）。"""
    _best_index.clear()
