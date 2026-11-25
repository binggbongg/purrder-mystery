import os


class GoogleClient:
    def __init__(self):
        from google import genai
        self.client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
        self.model = os.getenv("LLM_MODEL", "gemini-2.0-flash")

    def complete(self, system, messages, max_tokens=600):
        from google.genai import types
        contents = [types.Content(role="model" if m["role"] == "assistant" else "user",
                                  parts=[types.Part(text=m["content"])]) for m in messages]
        r = self.client.models.generate_content(
            model=self.model, contents=contents,
            config=types.GenerateContentConfig(system_instruction=system, max_output_tokens=max_tokens))
        return r.text or ""
