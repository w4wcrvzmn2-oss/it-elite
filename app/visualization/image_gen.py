"""OpenRouter image generation for presentation visualizations."""

from __future__ import annotations

import base64
import logging
import os
import re

import httpx

from app.ai.client import OPENROUTER_BASE_URL, get_ai_client

logger = logging.getLogger(__name__)

VIZ_PROMPTS = {
    "overview": (
        "Фотореалистичный общий вид городского двора после озеленения. "
        "Сохранить расположение зданий и дорог. {trees} деревьев, {shrubs} кустарников. "
        "Дневной свет, профессиональная архитектурная визуализация, 16:9."
    ),
    "pedestrian": (
        "Пешеходная перспектива городского двора на уровне человека после озеленения. "
        "Деревья и кустарники по рассчитанному плану ({trees} деревьев, {shrubs} кустарников). "
        "Не добавлять новые здания. 16:9."
    ),
    "detail": (
        "Крупный план озеленённой зоны двора: деревья, кустарники, дорожки. "
        "Презентационная визуализация рассчитанного проекта. 16:9."
    ),
}


def _extract_image_bytes_from_images_api(data: dict) -> bytes | None:
    """Parse OpenRouter POST /images response (b64_json or url)."""
    items = data.get("data") or []
    if not items:
        return None
    first = items[0]
    b64 = first.get("b64_json")
    if b64:
        return base64.b64decode(b64)
    url = first.get("url")
    if url and str(url).startswith("http"):
        with httpx.Client(timeout=60) as client:
            r = client.get(url)
            if r.status_code == 200:
                return r.content
    return None


def _extract_image_bytes_from_chat(data: dict) -> bytes | None:
    """Fallback: parse chat/completions multimodal response."""
    try:
        message = data["choices"][0]["message"]
    except (KeyError, IndexError):
        return None

    images = message.get("images") or message.get("image") or []
    if isinstance(images, dict):
        images = [images]
    for img in images:
        if not isinstance(img, dict):
            continue
        url = img.get("image_url", {}).get("url") or img.get("url") or ""
        if url.startswith("data:image"):
            b64 = url.split(",", 1)[-1]
            return base64.b64decode(b64)
        if url.startswith("http"):
            with httpx.Client(timeout=60) as client:
                r = client.get(url)
                if r.status_code == 200:
                    return r.content

    content = message.get("content")
    if isinstance(content, str) and "base64," in content:
        match = re.search(r"base64,([A-Za-z0-9+/=]+)", content)
        if match:
            return base64.b64decode(match.group(1))
    return None


def generate_ai_image(prompt: str) -> tuple[bytes | None, str]:
    """Generate image via OpenRouter. Returns (bytes, model_used)."""
    client = get_ai_client()
    image_model = os.getenv("OPENROUTER_IMAGE_MODEL", "").strip()
    if not client.is_available or not image_model:
        return None, ""

    headers = {
        "Authorization": f"Bearer {client.api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://green-planner.local",
        "X-Title": "Green Planner",
    }
    timeout = float(os.getenv("AI_TIMEOUT", "60"))

    try:
        logger.info("AI image request model=%s endpoint=/images", image_model)
        with httpx.Client(timeout=timeout) as http:
            resp = http.post(
                f"{OPENROUTER_BASE_URL}/images",
                headers=headers,
                json={
                    "model": image_model,
                    "prompt": prompt,
                    "aspect_ratio": "16:9",
                    "n": 1,
                },
            )
        if resp.status_code == 200:
            raw = _extract_image_bytes_from_images_api(resp.json())
            if raw:
                return raw, image_model
            logger.warning("AI image /images response had no image payload")

        # Legacy chat/completions path for older multimodal models
        if resp.status_code not in (200, 404, 422):
            detail = resp.text[:200]
            try:
                detail = resp.json().get("error", {}).get("message", detail)
            except Exception:
                pass
            logger.warning("AI image /images HTTP %s: %s", resp.status_code, detail)

        payload: dict = {
            "model": image_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1024,
        }
        if "gemini" in image_model.lower():
            payload["modalities"] = ["image", "text"]

        with httpx.Client(timeout=timeout) as http:
            resp = http.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
            )
        if resp.status_code != 200:
            detail = resp.text[:200]
            try:
                detail = resp.json().get("error", {}).get("message", detail)
            except Exception:
                pass
            logger.warning("AI image chat HTTP %s: %s", resp.status_code, detail)
            return None, image_model

        raw = _extract_image_bytes_from_chat(resp.json())
        return raw, image_model
    except Exception as e:
        logger.warning("AI image generation failed: %s", e)
        return None, image_model
