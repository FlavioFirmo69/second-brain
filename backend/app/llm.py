import asyncio
from typing import Any

import httpx

from .config import get_settings


class LlmUnavailable(RuntimeError):
    pass


async def complete(messages: list[dict[str, str]], response_format: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    if not settings.llm_enabled or not settings.llm_api_key or not settings.llm_model:
        raise LlmUnavailable("LLM non configurato. La richiesta è stata conservata nell'inbox.")
    url = settings.llm_base_url.rstrip("/") + "/chat/completions"
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            for attempt in range(3):
                body: dict[str, Any] = {
                    "model": settings.llm_model,
                    "messages": messages,
                    "temperature": 0.2,
                }
                if response_format is not None:
                    body["response_format"] = response_format
                response = await client.post(
                    url,
                    headers={"Authorization": f"Bearer {settings.llm_api_key}"},
                    json=body,
                )
                if response.status_code not in {429, 500, 502, 503, 504} or attempt == 2:
                    response.raise_for_status()
                    payload: dict[str, Any] = response.json()
                    return payload["choices"][0]["message"]["content"]
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after and retry_after.isdigit() else 2 ** attempt
                await asyncio.sleep(delay)
    except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
        raise LlmUnavailable(
            "LLM non raggiungibile o configurazione non valida. La richiesta è stata conservata nell'inbox."
        ) from exc
