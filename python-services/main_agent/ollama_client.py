"""
Backward-compatible Ollama client wrapper.
Internally uses Gemini while preserving the existing interface.
"""

from gemini_client import GeminiClient


class OllamaClient(GeminiClient):
    def __init__(self, base_url: str = None, model: str = None):
        # base_url is retained for backward compatibility with existing callers.
        # Gemini SDK calls use GEMINI_API_KEY and model configuration.
        super().__init__(model=model)
        if base_url:
            self.base_url = base_url
