# backend/learning_engine/openrouter_client.py
"""
Centralized OpenRouter Client for AdaptiveLearning.

Strictly reads API_KEY and MODEL from environment variables / Django settings.
Zero hardcoded keys or model names.
Logs original OpenRouter HTTP status and responses for transparent error visibility.
"""

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

import requests
from django.conf import settings

logger = logging.getLogger('learning_engine.openrouter')

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterError(Exception):
    """Raised when an OpenRouter API request fails."""
    pass


def get_openrouter_config() -> tuple[str, str]:
    """Retrieve API_KEY and MODEL from settings / environment."""
    api_key = getattr(settings, 'API_KEY', '') or os.getenv('API_KEY', '')
    model = getattr(settings, 'MODEL', '') or os.getenv('MODEL', '')
    if not api_key:
        raise OpenRouterError("OpenRouter API_KEY is not configured in environment variables.")
    if not model:
        raise OpenRouterError("OpenRouter MODEL is not configured in environment variables.")
    return api_key, model


def call_openrouter(
    prompt: str,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    timeout: int = 45,
    api_key: Optional[str] = None,
    model: Optional[str] = None
) -> str:
    """
    Execute a chat completion call to OpenRouter.
    Returns the assistant's response string.
    Raises OpenRouterError on missing credentials or HTTP errors, with full error logging.
    """
    if not api_key or not model:
        env_key, env_model = get_openrouter_config()
        api_key = api_key or env_key
        model = model or env_model

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://adaptlearn.local",
        "X-Title": "AdaptiveLearning"
    }

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    try:
        response = requests.post(
            OPENROUTER_API_URL,
            headers=headers,
            json=payload,
            timeout=timeout
        )
    except requests.exceptions.Timeout as te:
        logger.error(f"OpenRouter request timed out after {timeout}s: {te}")
        raise OpenRouterError(f"OpenRouter connection timed out: {te}")
    except Exception as e:
        logger.error(f"OpenRouter connection failed: {e}")
        raise OpenRouterError(f"OpenRouter connection error: {e}")

    if response.status_code != 200:
        err_body = response.text[:400]
        logger.error(f"OpenRouter API error [HTTP {response.status_code}]: {err_body}")
        raise OpenRouterError(f"OpenRouter API returned HTTP {response.status_code}: {err_body}")

    try:
        data = response.json()
        content = data['choices'][0]['message']['content'] or ""
        return content
    except Exception as e:
        logger.error(f"Failed to parse OpenRouter JSON response: {e} | Raw: {response.text[:300]}")
        raise OpenRouterError(f"Failed to parse OpenRouter response: {e}")


def parse_json_from_text(raw_text: str) -> Any:
    """Safely extracts and parses JSON objects/arrays from LLM raw text."""
    if not raw_text or not raw_text.strip():
        return None

    text = raw_text.strip()
    if text.startswith("```"):
        lines = [ln.rstrip() for ln in text.splitlines()]
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()

    # Clean control characters
    text = re.sub(r'[\x00-\x1f\x7f]', lambda m: ' ' if m.group() in ('\n', '\r', '\t') else '', text)

    # Attempt direct parse
    try:
        return json.loads(text)
    except Exception:
        pass

    # Extract JSON substring
    match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', text)
    if match:
        candidate = match.group(1).strip()
        try:
            return json.loads(candidate)
        except Exception:
            candidate_cleaned = re.sub(r',\s*([\]\}])', r'\1', candidate)
            try:
                return json.loads(candidate_cleaned)
            except Exception:
                pass

    return None
