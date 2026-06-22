from .base import LLMProvider, LLMResponse
from .gemini import GeminiProvider

PROVIDERS = {
    "gemini": GeminiProvider,
}


def load_providers(names):
    return [PROVIDERS[n]() for n in names if n in PROVIDERS]
