"""OpenRouter API client."""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, TypeVar  # noqa: TC003

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)

OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
T = TypeVar("T", bound=BaseModel)

_last_metrics: dict[str, Any] = {
    "latency_sec": None,
    "tokens": None,
    "last_error": None,
}


class AIClientError(Exception):
    """Raised when AI client fails."""


def get_last_ai_metrics() -> dict[str, Any]:
    return dict(_last_metrics)


class OpenRouterClient:
    """OpenAI-compatible OpenRouter client."""

    def __init__(self) -> None:
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
        self.enabled = os.getenv("AI_ENABLED", "true").lower() in ("1", "true", "yes")
        self.max_tokens = int(os.getenv("AI_MAX_TOKENS", "1024"))
        self.temperature = float(os.getenv("AI_TEMPERATURE", "0.3"))
        self.timeout = float(os.getenv("AI_TIMEOUT", "30"))
        self.max_retries = 2

    @property
    def is_available(self) -> bool:
        return self.enabled and bool(self.api_key)

    def chat_json(
        self,
        system: str,
        user_content: str,
        schema: type[T],
    ) -> T:
        if not self.is_available:
            raise AIClientError("AI not available")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://green-planner.local",
            "X-Title": "Green Planner",
        }

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_content},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "response_format": {"type": "json_object"},
        }

        last_error: Exception | None = None
        start = time.time()

        for attempt in range(self.max_retries + 1):
            try:
                logger.info("AI request started model=%s attempt=%d", self.model, attempt + 1)
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(
                        f"{OPENROUTER_BASE_URL}/chat/completions",
                        headers=headers,
                        json=payload,
                    )
                latency = time.time() - start

                if resp.status_code != 200:
                    detail = resp.text[:200]
                    try:
                        detail = resp.json().get("error", {}).get("message", detail)
                    except Exception:
                        pass
                    raise AIClientError(f"OpenRouter HTTP {resp.status_code}: {detail}")

                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                tokens = usage.get("total_tokens")
                logger.info(
                    "AI request success latency=%.2fs tokens=%s",
                    latency,
                    tokens if tokens is not None else "n/a",
                )
                _last_metrics.update({
                    "latency_sec": round(latency, 2),
                    "tokens": tokens,
                    "last_error": None,
                })

                parsed = json.loads(content)
                return schema.model_validate(parsed)

            except (json.JSONDecodeError, KeyError, ValueError) as e:
                last_error = e
                logger.warning("AI invalid JSON response attempt=%d: %s", attempt + 1, e)
            except Exception as e:
                last_error = e
                logger.warning("AI request failed attempt=%d: %s", attempt + 1, e)

        err = str(last_error) if last_error else "AI request failed"
        _last_metrics["last_error"] = err[:200]
        raise AIClientError(err)


_client: OpenRouterClient | None = None


def get_ai_client() -> OpenRouterClient:
    global _client
    if _client is None:
        _client = OpenRouterClient()
    return _client
