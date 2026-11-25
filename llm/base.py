from typing import Protocol


class LLMClient(Protocol):
    def complete(self, system: str, messages: list[dict], max_tokens: int = 600) -> str: ...
