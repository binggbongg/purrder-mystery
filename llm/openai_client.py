import os


class OpenAIClient:
    def __init__(self, model: str | None = None):
        from openai import OpenAI
        self.model = model or os.getenv("OPENAI_MODEL") or os.getenv("LLM_MODEL", "gpt-6-luna")
        self.client = OpenAI(
            api_key=os.environ["OPENAI_API_KEY"],
            base_url=os.getenv("OPENAI_BASE_URL", "https://aiki-labs.up.railway.app/api/v1"),
        )

    def complete(self, system: str, messages: list[dict], max_tokens: int = 600) -> str:
        msgs = [{"role": "system", "content": system}, *messages]
        try:
            r = self.client.chat.completions.create(
                model=self.model, messages=msgs, max_completion_tokens=max_tokens)
        except Exception as e:
            if "max_completion_tokens" not in str(e):
                raise
            r = self.client.chat.completions.create(
                model=self.model, messages=msgs, max_tokens=max_tokens)
        return r.choices[0].message.content or ""
