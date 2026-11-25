import os

_SECRETS = ("OPENAI_API_KEY", "OPENAI_BASE_URL", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY")


def get_client():
    provider = os.getenv("LLM_PROVIDER", "mock").lower()
    if provider == "mock":
        for k in _SECRETS:                       # offline: nothing here can reach an API
            os.environ.pop(k, None)
        from .mock_client import MockClient
        return MockClient()
    if provider == "anthropic":
        from .anthropic_client import AnthropicClient
        return AnthropicClient()
    if provider == "openai":
        from .openai_client import OpenAIClient
        return OpenAIClient()
    if provider == "google":
        from .google_client import GoogleClient
        return GoogleClient()
    raise ValueError(f"Unknown LLM_PROVIDER '{provider}' (use mock, anthropic, openai or google)")
