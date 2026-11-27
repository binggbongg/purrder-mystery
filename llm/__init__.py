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


def get_evaluator_client(gameplay_client, timeout: float, *,
                         local_timeout: float, local_batch_size: int):
    """Keep evaluator model and request limits independent of the gameplay client."""
    from .mock_client import MockClient

    if isinstance(gameplay_client, MockClient):
        return None
    if type(gameplay_client).__module__.startswith(("llm.openai_", "llm.anthropic_", "llm.google_")):
        model = os.getenv("SCORING_LLM_MODEL") or gameplay_client.model
        if getattr(gameplay_client, "is_local_ollama", False):
            return type(gameplay_client)(model=model, timeout=local_timeout,
                                         assessment_batch_size=local_batch_size)
        return type(gameplay_client)(model=model, timeout=timeout)
    return gameplay_client  # injected test or application client
