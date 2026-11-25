import os


class AnthropicClient:
    def __init__(self):
        import anthropic
        self.client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
        self.model = os.getenv("LLM_MODEL", "claude-sonnet-5-5")

    def complete(self, system, messages, max_tokens=600):
        r = self.client.messages.create(model=self.model, max_tokens=max_tokens,
                                        system=system, messages=messages)
        return "".join(b.text for b in r.content if b.type == "text")
