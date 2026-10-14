import asyncio
import logging
from typing import Any

import httpx

from .config import get_settings


logger = logging.getLogger(__name__)

class LlmUnavailable(RuntimeError):
    """Public, sanitized diagnosis; never include provider response bodies or keys."""
    def __init__(self, message: str, *, code: str = 'unavailable', status: int | None = None):
        super().__init__(message)
        self.code = code
        self.status = status


def response_error(status: int) -> LlmUnavailable:
    if status in (401, 403):
        return LlmUnavailable('Il servizio AI ha rifiutato le credenziali o l’accesso. Verifica la configurazione della chiave.', code='authentication', status=status)
    if status == 429:
        return LlmUnavailable('Il servizio AI ha raggiunto un limite di richieste o di quota. Riprova più tardi o verifica la quota.', code='rate_limit', status=status)
    if status == 404:
        return LlmUnavailable('Il modello AI o l’indirizzo del servizio non è disponibile. Verifica la configurazione.', code='model_or_endpoint', status=status)
    if status in (400, 413, 422):
        return LlmUnavailable('Il servizio AI ha rifiutato la richiesta: formato o dimensione del contesto non accettati.', code='invalid_request', status=status)
    return LlmUnavailable('Il servizio AI ha restituito un errore temporaneo. Riprova più tardi.', code='provider_error', status=status)


async def complete(messages: list[dict[str, str]], response_format: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    if not settings.llm_enabled or not settings.llm_api_key or not settings.llm_model:
        raise LlmUnavailable('Servizio AI non configurato: controlla attivazione, chiave e modello.', code='not_configured')
    url = settings.llm_base_url.rstrip("/") + "/chat/completions"
    # Providers using the OpenAI-compatible format may mishandle multiple system
    # messages. Preserve their content in one system message at the beginning.
    system = [message['content'] for message in messages if message['role'] == 'system']
    messages = ([{'role': 'system', 'content': '\n\n'.join(system)}] if system else []) + [
        message for message in messages if message['role'] != 'system']
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
                    if not response.is_success:
                        error = response_error(response.status_code)
                        logger.warning('LLM request failed: code=%s status=%s', error.code, error.status)
                        raise error
                    payload: dict[str, Any] = response.json()
                    content = payload['choices'][0]['message']['content']
                    if not isinstance(content, str) or not content.strip():
                        raise LlmUnavailable('Il servizio AI ha restituito una risposta vuota o non utilizzabile.', code='empty_response')
                    return content
                retry_after = response.headers.get("Retry-After")
                delay = min(float(retry_after), 5) if retry_after and retry_after.isdigit() else 2 ** attempt
                await asyncio.sleep(delay)
    except httpx.TimeoutException as exc:
        raise LlmUnavailable('Il servizio AI non ha risposto entro il tempo disponibile. Riprova con una richiesta più breve.', code='timeout') from exc
    except httpx.HTTPError as exc:
        raise LlmUnavailable('Impossibile raggiungere il servizio AI. Verifica la connessione e l’indirizzo configurato.', code='connection') from exc
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise LlmUnavailable('La risposta del servizio AI non ha il formato previsto.', code='invalid_response') from exc
