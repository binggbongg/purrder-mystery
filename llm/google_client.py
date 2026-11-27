import os


class GoogleClient:
    def __init__(self, model: str | None = None, *, timeout: float | None = None):
        from google import genai
        from google.genai import types
        options = types.HttpOptions(timeout=int(timeout * 1000)) if timeout is not None else None
        self.client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"], http_options=options)
        self.model = model or os.getenv("LLM_MODEL", "gemini-2.0-flash")

    def complete(self, system, messages, max_tokens=600):
        from google.genai import types
        contents = [types.Content(role="model" if m["role"] == "assistant" else "user",
                                  parts=[types.Part(text=m["content"])]) for m in messages]
        r = self.client.models.generate_content(
            model=self.model, contents=contents,
            config=types.GenerateContentConfig(system_instruction=system, max_output_tokens=max_tokens))
        return r.text or ""
