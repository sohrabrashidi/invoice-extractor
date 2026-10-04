from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass

import httpx

from .models import EXTRACTION_SCHEMA

SYSTEM_PROMPT = """You extract data from supplier invoices.
Return only what is printed on the invoice. Do not calculate missing values and do not guess.
Use null for fields that are not present. Dates must be YYYY-MM-DD.
Numbers must be plain numbers without currency symbols or thousands separators."""


@dataclass
class LlmConfig:
    api_key: str
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o-mini"
    timeout: float = 60.0
    retries: int = 3

    @classmethod
    def from_env(cls) -> "LlmConfig | None":
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            return None
        return cls(
            api_key=key,
            base_url=os.getenv("OPENAI_BASE_URL", cls.base_url),
            model=os.getenv("INVOICE_MODEL", cls.model),
        )


class LlmExtractor:
    """Calls any OpenAI-compatible chat endpoint with a strict JSON schema."""

    def __init__(self, config: LlmConfig, client: httpx.Client | None = None):
        self.config = config
        self.client = client or httpx.Client(timeout=config.timeout)

    def extract(self, invoice_text: str) -> dict:
        payload = {
            "model": self.config.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Invoice text:\n\n{invoice_text}"},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "invoice", "strict": True, "schema": EXTRACTION_SCHEMA},
            },
        }

        response = self._post("/chat/completions", payload)
        content = response["choices"][0]["message"]["content"]
        return json.loads(content)

    def _post(self, path: str, payload: dict) -> dict:
        url = self.config.base_url.rstrip("/") + path
        headers = {"Authorization": f"Bearer {self.config.api_key}"}

        for attempt in range(1, self.config.retries + 1):
            try:
                r = self.client.post(url, json=payload, headers=headers)
            except httpx.TransportError:
                if attempt == self.config.retries:
                    raise
            else:
                # Retry only on rate limits and server errors; a 400 won't fix itself.
                if r.status_code < 400:
                    return r.json()
                if r.status_code != 429 and r.status_code < 500 or attempt == self.config.retries:
                    r.raise_for_status()
            time.sleep(2 ** attempt)

        raise RuntimeError("unreachable")
