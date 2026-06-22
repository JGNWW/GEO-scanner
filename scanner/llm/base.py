from dataclasses import dataclass, field
from typing import List


@dataclass
class LLMResponse:
    provider: str
    model: str
    prompt_id: str
    prompt_text: str
    answer: str
    citations: List[str] = field(default_factory=list)
    error: str = ""


class LLMProvider:
    name: str = "base"
    model: str = ""

    def query(self, prompt_id: str, prompt_text: str) -> LLMResponse:
        raise NotImplementedError
