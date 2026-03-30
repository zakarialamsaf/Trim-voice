"""
AI Content Editing Engine
=========================
Supports real instruction-following image editing — "make person wear a suit",
"change background to beach", "make it night time", etc.

Provider priority:
  1. fal.ai  (FAL_KEY in env)  → FLUX.1 Kontext-dev — state-of-the-art editing
  2. HF Inference API  (HF_TOKEN with inference scope) → Qwen-Image-Edit-2511
  3. Gradio client (open HF spaces) → fallback chain

What this model can handle that our style engine cannot:
  • "make the person wear a suit"
  • "change the background to a beach"
  • "add glasses to the person"
  • "turn this into a night scene"
  • "make the car red"
  • "put a hat on the person"
  • "change hair colour to blonde"
  • "make it look like winter"
  • + any other instruction that edits image *content*
"""

from __future__ import annotations

import base64
import io
import logging
import os
import re
import tempfile
from typing import Optional

logger = logging.getLogger(__name__)

FAL_KEY: str = os.getenv("FAL_KEY", "")
HF_TOKEN: str = os.getenv("HF_TOKEN", "")


# ── Provider: fal.ai (best, free tier available) ───────────────────────────────

def _edit_via_fal(image_bytes: bytes, prompt: str) -> Optional[bytes]:
    """Use fal.ai FLUX.1 Kontext-dev for instruction-following image editing."""
    if not FAL_KEY:
        return None
    try:
        import fal_client
        os.environ["FAL_KEY"] = FAL_KEY

        # Upload image to fal CDN
        import urllib.request, urllib.parse
        img_b64 = base64.b64encode(image_bytes).decode()
        data_uri = f"data:image/jpeg;base64,{img_b64}"

        result = fal_client.subscribe(
            "fal-ai/flux-kontext/dev",
            arguments={
                "image_url": data_uri,
                "prompt": prompt,
                "num_inference_steps": 28,
                "guidance_scale": 2.5,
                "num_images": 1,
                "output_format": "jpeg",
            },
        )

        images = result.get("images", [])
        if not images:
            return None

        img_url = images[0].get("url", "")
        if not img_url:
            return None

        # Download result
        if img_url.startswith("data:"):
            _, encoded = img_url.split(",", 1)
            return base64.b64decode(encoded)
        else:
            with urllib.request.urlopen(img_url) as resp:
                return resp.read()

    except Exception as e:
        logger.warning("fal.ai edit failed: %s", e)
        return None


# ── Provider: HuggingFace Inference API ───────────────────────────────────────

def _edit_via_hf(image_bytes: bytes, prompt: str) -> Optional[bytes]:
    """Use HF Inference API (requires token with inference.serverless.write scope)."""
    if not HF_TOKEN:
        return None
    try:
        from huggingface_hub import InferenceClient
        client = InferenceClient(token=HF_TOKEN)

        models = [
            "Qwen/Qwen-Image-Edit-2511",
            "lightx2v/Qwen-Image-Edit-2511-Lightning",
            "Qwen/Qwen-Image-Edit-2509",
        ]

        for model in models:
            try:
                result = client.image_to_image(
                    image=image_bytes,
                    prompt=prompt,
                    model=model,
                )
                buf = io.BytesIO()
                result.save(buf, format="PNG")
                logger.info("HF Inference edit succeeded with %s", model)
                return buf.getvalue()
            except Exception as e:
                logger.debug("HF model %s failed: %s", model, e)
                continue
        return None
    except Exception as e:
        logger.warning("HF Inference edit failed: %s", e)
        return None


# ── Provider: Gradio client (open spaces) ─────────────────────────────────────

def _read_gradio_result(result) -> Optional[bytes]:
    """Extract image bytes from a Gradio result (handles tuples, lists, strings, dicts)."""
    import urllib.request as _urllib

    # Unwrap tuple/list wrappers (some spaces return (image, seed) or [image])
    if isinstance(result, (tuple, list)):
        result = result[0]

    # String = local file path written by gradio_client
    if isinstance(result, str):
        if os.path.exists(result):
            with open(result, "rb") as fh:
                return fh.read()
        if result.startswith("data:"):
            _, encoded = result.split(",", 1)
            return base64.b64decode(encoded)
        if result.startswith("http"):
            with _urllib.urlopen(result) as resp:
                return resp.read()

    # Dict with 'path' or 'url' key (gradio_client FileData format)
    if isinstance(result, dict):
        img_path = result.get("path")
        if img_path and os.path.exists(img_path):
            with open(img_path, "rb") as fh:
                return fh.read()
        url = result.get("url", "")
        if url:
            if url.startswith("data:"):
                _, encoded = url.split(",", 1)
                return base64.b64decode(encoded)
            if url.startswith("http"):
                with _urllib.urlopen(url) as resp:
                    return resp.read()

    return None


def _edit_via_gradio_firered(image_bytes: bytes, prompt: str) -> Optional[bytes]:
    """Use FireRed-Image-Edit-1.0-Fast space (Qwen-based, recently updated)."""
    try:
        import json as _json
        from gradio_client import Client

        client = Client("prithivMLmods/FireRed-Image-Edit-1.0-Fast", verbose=False)
        img_b64 = "data:image/jpeg;base64," + base64.b64encode(image_bytes).decode()
        images_b64_json = _json.dumps([img_b64])

        result = client.predict(
            images_b64_json=images_b64_json,
            prompt=prompt,
            seed=42,
            randomize_seed=True,
            guidance_scale=1.0,
            steps=4,
            api_name="/infer",
        )
        data = _read_gradio_result(result)
        if data:
            logger.info("FireRed-Image-Edit Gradio edit succeeded (%d bytes)", len(data))
            return data
        logger.warning("FireRed Gradio returned empty result: %s", repr(result)[:200])
    except Exception as e:
        logger.warning("FireRed Gradio space failed: %s", e, exc_info=True)
    return None


def _edit_via_gradio_ip2p(image_bytes: bytes, prompt: str) -> Optional[bytes]:
    """Use Instruct-Pix-2-Pix Gradio space (classic SD-based editing)."""
    tmp_path = None
    try:
        from gradio_client import Client

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(image_bytes)
            tmp_path = f.name

        client = Client("Manjushri/Instruct-Pix-2-Pix", verbose=False)
        result = client.predict(
            source_img=tmp_path,
            instructions=prompt,
            guide=7.5,
            steps=5,
            seed=42,
            Strength=1.5,
            api_name="/predict",
        )
        data = _read_gradio_result(result)
        if data:
            logger.info("Instruct-Pix-2-Pix Gradio edit succeeded")
            return data
    except Exception as e:
        logger.warning("Instruct-Pix-2-Pix Gradio space failed: %s", e, exc_info=True)
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
    return None


def _edit_via_gradio(image_bytes: bytes, prompt: str) -> Optional[bytes]:
    """Try open HF Gradio spaces for image editing (FireRed → InstructPix2Pix)."""
    result = _edit_via_gradio_firered(image_bytes, prompt)
    if result:
        return result

    result = _edit_via_gradio_ip2p(image_bytes, prompt)
    if result:
        return result

    return None


# ── Detect if prompt requires content editing ──────────────────────────────────

CONTENT_EDIT_PATTERNS = [
    r"\b(wear|wearing|dressed in|put on|add|remove|replace|change|make|turn into|convert)\b",
    r"\b(suit|dress|shirt|hat|glasses|hair|color|colour|background|sky|season)\b",
    r"\b(night|day|winter|summer|beach|forest|city|studio)\b",
    r"\b(smile|sitting|standing|running|holding)\b",
    r"\b(older|younger|taller|thinner|bigger|smaller)\b",
]

def is_content_edit_prompt(prompt: str) -> bool:
    """Returns True if the prompt requests content/object-level changes."""
    p = prompt.lower()
    return any(re.search(pat, p) for pat in CONTENT_EDIT_PATTERNS)


# ── Main entry point ──────────────────────────────────────────────────────────

def run_ai_edit(image_bytes: bytes, prompt: str) -> bytes:
    """
    Apply instruction-following AI edit to image.

    Tries fal.ai → HF Inference → Gradio → raises ConfigurationError if none available.
    """
    # 1. fal.ai (best quality, free tier)
    result = _edit_via_fal(image_bytes, prompt)
    if result:
        return result

    # 2. HuggingFace Inference API
    result = _edit_via_hf(image_bytes, prompt)
    if result:
        return result

    # 3. Gradio open spaces
    result = _edit_via_gradio(image_bytes, prompt)
    if result:
        return result

    raise ConfigurationError(
        "All AI edit providers failed (fal.ai, HuggingFace, Gradio spaces). "
        "This may be a temporary outage. "
        "For best results: add FAL_KEY (https://fal.ai/dashboard/keys) or "
        "HF_TOKEN with inference scope (https://huggingface.co/settings/tokens) to .env.local."
    )


def get_provider_status() -> dict:
    """Return which providers are configured and available."""
    return {
        "fal_ai": {
            "available": bool(FAL_KEY),
            "model": "FLUX.1 Kontext-dev",
            "quality": "best",
            "setup_url": "https://fal.ai/dashboard/keys",
            "env_var": "FAL_KEY",
            "free_tier": True,
            "description": "Free tier · State-of-the-art FLUX.1 Kontext · Best for complex edits",
        },
        "huggingface": {
            "available": bool(HF_TOKEN),
            "model": "Qwen-Image-Edit-2511",
            "quality": "high",
            "setup_url": "https://huggingface.co/settings/tokens",
            "env_var": "HF_TOKEN",
            "free_tier": True,
            "description": "Free tier · Qwen Image Edit · Needs inference.serverless.write scope",
        },
        "gradio_spaces": {
            "available": True,
            "model": "FireRed-Image-Edit / Instruct-Pix2Pix",
            "quality": "good",
            "setup_url": "https://huggingface.co/spaces/prithivMLmods/FireRed-Image-Edit-1.0-Fast",
            "env_var": None,
            "free_tier": True,
            "description": "Always available · No API key needed · Uses public HF Spaces",
        },
    }


class ConfigurationError(Exception):
    """Raised when no AI edit provider is configured."""
    pass
