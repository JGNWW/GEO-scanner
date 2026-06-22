import os
import time

from google import genai
from google.genai import types

from .base import LLMProvider, LLMResponse


class GeminiProvider(LLMProvider):
    name = "gemini"
    model = "gemini-2.5-flash"

    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY ontbreekt")
        self.client = genai.Client(api_key=api_key)

    def query(self, prompt_id: str, prompt_text: str) -> LLMResponse:
        config = types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            temperature=0.2,
        )
        try:
            resp = self.client.models.generate_content(
                model=self.model,
                contents=prompt_text,
                config=config,
            )
        except Exception as e:
            return LLMResponse(
                provider=self.name,
                model=self.model,
                prompt_id=prompt_id,
                prompt_text=prompt_text,
                answer="",
                error=str(e),
            )

        answer = resp.text or ""
        citations = _extract_citations(resp)

        time.sleep(1)
        return LLMResponse(
            provider=self.name,
            model=self.model,
            prompt_id=prompt_id,
            prompt_text=prompt_text,
            answer=answer,
            citations=citations,
        )


def _extract_citations(resp) -> list:
    urls = []
    seen = set()
    for cand in getattr(resp, "candidates", []) or []:
        meta = getattr(cand, "grounding_metadata", None)
        if not meta:
            continue
        for chunk in getattr(meta, "grounding_chunks", []) or []:
            web = getattr(chunk, "web", None)
            if not web:
                continue
            url = getattr(web, "uri", None)
            if url and url not in seen:
                seen.add(url)
                urls.append(url)
    return urls
