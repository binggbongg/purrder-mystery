import os
from urllib.parse import urlsplit


class OpenAIClient:
    def __init__(self, model: str | None = None, *, timeout: float | None = None,
                 assessment_batch_size: int | None = None):
        from openai import OpenAI
        self.model = model or os.getenv("OPENAI_MODEL") or os.getenv("LLM_MODEL", "gpt-6-luna")
        self.client = OpenAI(
            api_key=os.environ["OPENAI_API_KEY"],
            base_url=os.getenv("OPENAI_BASE_URL", "https://aiki-labs.up.railway.app/api/v1"),
            **({"timeout": timeout, "max_retries": 0} if timeout is not None else {}),
        )
        self.assessment_batch_size = assessment_batch_size

    @property
    def is_local_ollama(self) -> bool:
        endpoint = urlsplit(str(self.client.base_url))
        return endpoint.hostname in ("localhost", "127.0.0.1", "::1") and endpoint.port == 11434

    def complete(self, system: str, messages: list[dict], max_tokens: int = 600,
                 *, response_format: dict | None = None) -> str:
        msgs = [{"role": "system", "content": system}, *messages]
        options = {"response_format": response_format, "temperature": 0} if response_format is not None else {}
        try:
            r = self.client.chat.completions.create(
                model=self.model, messages=msgs, max_completion_tokens=max_tokens, **options)
        except Exception as e:
            if "max_completion_tokens" not in str(e):
                raise
            r = self.client.chat.completions.create(
                model=self.model, messages=msgs, max_tokens=max_tokens, **options)
        return r.choices[0].message.content or ""

    def complete_assessment(self, system: str, messages: list[dict], max_tokens: int,
                            schema: dict) -> str:
        return self.complete(system, messages, max_tokens, response_format={
            "type": "json_schema",
            "json_schema": {"name": "investigation_assessment", "schema": schema},
        })
