"""统一 LLM 客户端：默认 Qwen（读 .env），预留 DeepSeek。
功能点提取以读代码结构(AST)为主；本客户端仅用于可选的 LLM 增强（可在 .env 关闭 LLM_ENHANCE）。
"""
from openai import OpenAI
from backend.config import settings


class LLMClient:
    def __init__(self):
        if settings.LLM_PROVIDER == "qwen":
            self.base_url = settings.QWEN_BASE_URL
            self.api_key = settings.QWEN_API_KEY
            self.model = settings.QWEN_MODEL
        else:
            self.base_url = settings.DEEPSEEK_BASE_URL
            self.api_key = settings.DEEPSEEK_API_KEY
            self.model = settings.DEEPSEEK_MODEL
        self.client = OpenAI(base_url=self.base_url, api_key=self.api_key) if self.api_key else None

    def enhance(self, system_prompt: str, user_prompt: str, max_tokens: int = 1200):
        """可选增强：关闭 LLM_ENHANCE 或无 key 时返回 None，调用方回退到纯 AST 结果。"""
        if not settings.LLM_ENHANCE or not self.client:
            return None
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
                temperature=0.2,
            )
            return resp.choices[0].message.content
        except Exception as e:  # 解析失败降级为纯 AST，不阻塞主流程
            return f"[LLM_ERROR] {e}"


llm_client = LLMClient()
