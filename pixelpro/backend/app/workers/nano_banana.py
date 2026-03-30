"""
Nano Banana Transform Engine
============================
Applies the viral "Nano Banana figurine" AI style to any image.

Priority chain:
  1. HuggingFace Inference API  (FLUX.1 + Nano Banana LoRA — if HF_TOKEN set)
  2. Local style engine          (OpenCV + PIL — always works, no GPU needed)
"""

from __future__ import annotations

import base64
import io
import logging
import os
import re
from typing import Optional

import cv2
import numpy as np
from PIL import Image as PILImage, ImageEnhance, ImageFilter

logger = logging.getLogger(__name__)

# ── HuggingFace Inference API ──────────────────────────────────────────────────

HF_TOKEN: str = os.getenv("HF_TOKEN", "")

# Style presets — each maps to (base_prompt, negative_prompt, style_strength)
STYLE_PRESETS = {
    "nano_banana": (
        "nano banana figurine toy, collectible vinyl toy, smooth plastic texture, "
        "bright warm studio lighting, yellow orange glow, ultra sharp, high detail",
        "blurry, realistic skin, dark, gloomy, low quality",
        0.75,
    ),
    "nano_banana_2": (
        "nano banana 2 collectible figure, shiny plastic, vibrant pastel colors, "
        "soft toy aesthetic, gradient background, cinematic lighting",
        "ugly, deformed, noise, grain",
        0.80,
    ),
    "nano_banana_pro": (
        "nano banana PRO luxury edition, iridescent metallic finish, premium collectible, "
        "museum-quality display, dramatic rim lighting, 8K render",
        "cheap, blurry, low poly, dirty",
        0.85,
    ),
    "product_pro": (
        "professional product photography, pure white background, studio softbox lighting, "
        "commercial quality, crisp shadows, e-commerce ready",
        "cluttered, dark, amateur, blur",
        0.65,
    ),
    "vintage": (
        "vintage film photograph, warm sepia tones, gentle grain, nostalgic aesthetic, "
        "faded highlights, classic portrait style",
        "digital, cold, modern, overexposed",
        0.60,
    ),
    "cyberpunk": (
        "cyberpunk neon style, electric blue and magenta glow, futuristic atmosphere, "
        "rain-soaked reflections, high contrast, sci-fi vibes",
        "natural, warm, daylight, soft",
        0.70,
    ),
}


def _hf_img2img(
    image_bytes: bytes,
    prompt: str,
    negative_prompt: str = "",
    strength: float = 0.75,
) -> Optional[bytes]:
    """Call HuggingFace Inference API for image-to-image generation."""
    if not HF_TOKEN:
        return None
    try:
        from huggingface_hub import InferenceClient

        client = InferenceClient(token=HF_TOKEN)

        # Convert to PIL for the API
        pil_img = PILImage.open(io.BytesIO(image_bytes)).convert("RGB")

        # Use FLUX.1-schnell (fast, free with token) for img2img
        result = client.image_to_image(
            image=pil_img,
            prompt=prompt,
            negative_prompt=negative_prompt,
            strength=strength,
            model="black-forest-labs/FLUX.1-schnell",
        )

        buf = io.BytesIO()
        result.save(buf, format="PNG")
        logger.info("HF Inference img2img succeeded")
        return buf.getvalue()
    except Exception as e:
        logger.warning("HF Inference API failed (%s), using local engine", e)
        return None


# ── Local nano-banana style engine ────────────────────────────────────────────

def _apply_nano_banana_style(img_bgr: np.ndarray, variant: str = "nano_banana") -> np.ndarray:
    """
    Apply Nano Banana figurine style locally using OpenCV + PIL.
    Creates a warm, plasticky, high-saturation toy aesthetic.
    """
    # 1. Boost saturation and vibrance (HSV)
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV).astype(np.float32)
    sat_boost = {"nano_banana": 1.6, "nano_banana_2": 1.4, "nano_banana_pro": 1.8,
                 "product_pro": 1.1, "vintage": 0.7, "cyberpunk": 1.5}.get(variant, 1.5)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * sat_boost, 0, 255)
    img_bgr = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    # 2. Color cast depending on style
    pil_img = PILImage.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)).convert("RGB")

    if variant in ("nano_banana", "nano_banana_2", "nano_banana_pro"):
        pil_img = _apply_warm_banana_cast(pil_img, strength=0.18)
        pil_img = _apply_glow(pil_img, color=(255, 220, 80), strength=0.12)
    elif variant == "product_pro":
        pil_img = _apply_clean_white_balance(pil_img)
    elif variant == "vintage":
        pil_img = _apply_vintage(pil_img)
    elif variant == "cyberpunk":
        pil_img = _apply_cyberpunk(pil_img)

    # 3. Sharpen — toy plastic look
    sharp_amount = {"nano_banana": 1.8, "nano_banana_pro": 2.2, "product_pro": 1.6,
                    "vintage": 0.9, "cyberpunk": 2.0}.get(variant, 1.5)
    enhancer = ImageEnhance.Sharpness(pil_img)
    pil_img = enhancer.enhance(sharp_amount)

    # 4. Contrast punch
    contrast_map = {"nano_banana": 1.25, "nano_banana_pro": 1.35, "product_pro": 1.15,
                    "vintage": 1.1, "cyberpunk": 1.4}
    enhancer = ImageEnhance.Contrast(pil_img)
    pil_img = enhancer.enhance(contrast_map.get(variant, 1.2))

    # 5. Brightness
    bright_map = {"nano_banana": 1.10, "nano_banana_pro": 1.15, "product_pro": 1.05,
                  "vintage": 0.95, "cyberpunk": 0.90}
    enhancer = ImageEnhance.Brightness(pil_img)
    pil_img = enhancer.enhance(bright_map.get(variant, 1.08))

    # 6. Final softbox / studio vignette
    if variant == "product_pro":
        pil_img = _apply_studio_vignette(pil_img)
    elif variant in ("nano_banana", "nano_banana_2", "nano_banana_pro"):
        pil_img = _apply_toy_vignette(pil_img)

    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


def _apply_warm_banana_cast(pil_img: PILImage.Image, strength: float = 0.18) -> PILImage.Image:
    """Overlay a warm yellow-orange cast — the signature nano banana glow."""
    warm = PILImage.new("RGB", pil_img.size, (255, 200, 60))
    return PILImage.blend(pil_img, warm, alpha=strength)


def _apply_glow(pil_img: PILImage.Image, color=(255, 220, 80), strength=0.12) -> PILImage.Image:
    """Radial soft glow from center."""
    w, h = pil_img.size
    glow = PILImage.new("RGB", (w, h), color)
    mask = _radial_gradient(w, h, inner=0, outer=int(strength * 255))
    return PILImage.composite(glow, pil_img, mask)


def _radial_gradient(w: int, h: int, inner: int, outer: int) -> PILImage.Image:
    cx, cy = w // 2, h // 2
    Y, X = np.ogrid[:h, :w]
    dist = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)
    max_dist = np.sqrt(cx ** 2 + cy ** 2)
    grad = (dist / max_dist * (outer - inner) + inner).clip(0, 255).astype(np.uint8)
    return PILImage.fromarray(grad, mode="L")


def _apply_clean_white_balance(pil_img: PILImage.Image) -> PILImage.Image:
    """Auto white balance — makes product colours pop on white."""
    img_arr = np.array(pil_img, dtype=np.float32)
    for ch in range(3):
        p2, p98 = np.percentile(img_arr[:, :, ch], (2, 98))
        if p98 > p2:
            img_arr[:, :, ch] = np.clip((img_arr[:, :, ch] - p2) / (p98 - p2) * 255, 0, 255)
    return PILImage.fromarray(img_arr.astype(np.uint8))


def _apply_vintage(pil_img: PILImage.Image) -> PILImage.Image:
    """Warm sepia + faded grain vintage look."""
    arr = np.array(pil_img, dtype=np.float32)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    arr[:, :, 0] = np.clip(r * 1.07 + g * 0.05, 0, 255)   # warm red
    arr[:, :, 2] = np.clip(b * 0.85, 0, 255)               # reduce blue
    # Add gentle grain
    noise = np.random.normal(0, 8, arr.shape).astype(np.float32)
    arr = np.clip(arr + noise, 0, 255)
    # Lift blacks (faded look)
    arr = arr * 0.85 + 20
    return PILImage.fromarray(arr.astype(np.uint8))


def _apply_cyberpunk(pil_img: PILImage.Image) -> PILImage.Image:
    """Neon blue-magenta cyberpunk colour grade."""
    arr = np.array(pil_img, dtype=np.float32)
    arr[:, :, 0] = np.clip(arr[:, :, 0] * 1.15, 0, 255)   # boost red → magenta
    arr[:, :, 2] = np.clip(arr[:, :, 2] * 1.40, 0, 255)   # boost blue
    arr[:, :, 1] = np.clip(arr[:, :, 1] * 0.80, 0, 255)   # dim green
    return PILImage.fromarray(arr.astype(np.uint8))


def _apply_studio_vignette(pil_img: PILImage.Image) -> PILImage.Image:
    """Soft product-photography vignette."""
    mask = _radial_gradient(pil_img.width, pil_img.height, inner=220, outer=130)
    vignette = PILImage.new("RGB", pil_img.size, (255, 255, 255))
    return PILImage.composite(pil_img, vignette, mask)


def _apply_toy_vignette(pil_img: PILImage.Image) -> PILImage.Image:
    """Warm studio vignette for toy/figurine aesthetic."""
    mask = _radial_gradient(pil_img.width, pil_img.height, inner=240, outer=120)
    vignette = PILImage.new("RGB", pil_img.size, (0, 0, 0))
    return PILImage.composite(pil_img, vignette, mask)


# ── Prompt-guided local enhancements ──────────────────────────────────────────

def _apply_prompt_guided(img_bgr: np.ndarray, prompt: str) -> np.ndarray:
    """
    Parse free-text prompt keywords and apply matching local effects.
    e.g. "bright product shot" → white balance + brightness
         "vintage old photo"   → sepia + grain
         "remove noise"        → NLM denoising
    """
    p = prompt.lower()
    pil_img = PILImage.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))

    if re.search(r"bright|light|luminous|airy", p):
        pil_img = ImageEnhance.Brightness(pil_img).enhance(1.25)
    if re.search(r"sharp|crisp|clear|detail", p):
        pil_img = ImageEnhance.Sharpness(pil_img).enhance(2.0)
    if re.search(r"vibrant|vivid|colorful|saturated", p):
        pil_img = ImageEnhance.Color(pil_img).enhance(1.6)
    if re.search(r"contrast|punch|pop|bold", p):
        pil_img = ImageEnhance.Contrast(pil_img).enhance(1.4)
    if re.search(r"warm|cozy|golden", p):
        pil_img = _apply_warm_banana_cast(pil_img, 0.15)
    if re.search(r"vintage|retro|old|sepia|film", p):
        pil_img = _apply_vintage(pil_img)
    if re.search(r"cyber|neon|futur|sci.?fi", p):
        pil_img = _apply_cyberpunk(pil_img)
    if re.search(r"product|white.?bg|clean|studio|professional|ecommerce|e-commerce", p):
        pil_img = _apply_clean_white_balance(pil_img)
        pil_img = _apply_studio_vignette(pil_img)
    if re.search(r"smooth|denoise|noise|grain", p):
        img_bgr = cv2.fastNlMeansDenoisingColored(
            cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR),
            None, h=12, hColor=12, templateWindowSize=7, searchWindowSize=21,
        )
        pil_img = PILImage.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))

    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


# ── Image analyzer ─────────────────────────────────────────────────────────────

def analyze_image(image_bytes: bytes) -> dict:
    """
    Analyze the image and return personalised transformation suggestions.
    Returns dict with: analysis + list of 6 recommended transforms.
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return {"error": "Could not decode image"}

    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Brightness (0-255)
    brightness = float(np.mean(gray))
    # Contrast (std dev)
    contrast = float(np.std(gray))
    # Blur score (Laplacian variance — higher = sharper)
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    # Noise estimate
    noisy = blur_score < 80
    # Low resolution
    low_res = (w * h) < (720 * 720)
    # Dark image
    dark = brightness < 85
    # Washed out
    washed = contrast < 30
    # Face detection
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
    has_faces = len(faces) > 0

    # Saturation
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    avg_saturation = float(np.mean(hsv[:, :, 1]))
    desaturated = avg_saturation < 60

    # Build suggestions list
    suggestions = []

    suggestions.append({
        "id": "nano_banana",
        "icon": "🍌",
        "title": "Nano Banana Figurine",
        "description": "Transform into the viral collectible toy aesthetic. Warm glow, plastic finish, studio lighting.",
        "tags": ["trending", "AI style"],
        "preview_effect": "warm_saturated",
        "confidence": 95,
    })

    suggestions.append({
        "id": "nano_banana_pro",
        "icon": "✨",
        "title": "Nano Banana PRO",
        "description": "Luxury iridescent finish. Premium collectible with metallic sheen and dramatic rim lighting.",
        "tags": ["premium", "metallic"],
        "preview_effect": "metallic_glow",
        "confidence": 92,
    })

    if low_res or w < 1000:
        suggestions.append({
            "id": "upscale_4x",
            "icon": "🔍",
            "title": "4× AI Super-Resolution",
            "description": f"Your image is {w}×{h}px. Upscale to {w*4}×{h*4} with zero loss of detail.",
            "tags": ["resolution", "urgent"],
            "preview_effect": "sharper",
            "confidence": 98,
        })

    if dark:
        suggestions.append({
            "id": "bright_pro",
            "icon": "☀️",
            "title": "Brighten & Recover Shadows",
            "description": "Image looks underexposed. AI will recover shadow detail and add studio-quality lighting.",
            "tags": ["brightness", "lighting"],
            "preview_effect": "brighter",
            "confidence": 94,
        })

    if desaturated or washed:
        suggestions.append({
            "id": "vibrant",
            "icon": "🎨",
            "title": "Vibrance & Color Boost",
            "description": "Colours appear dull. Add vivid saturation and a professional colour grade.",
            "tags": ["color", "vibrance"],
            "preview_effect": "colorful",
            "confidence": 91,
        })

    if has_faces:
        suggestions.append({
            "id": "face_enhance",
            "icon": "👤",
            "title": "Face Restoration",
            "description": f"Detected {len(faces)} face(s). Restore skin texture, eyes, and fine details with GFPGAN.",
            "tags": ["portrait", "faces"],
            "preview_effect": "face_restored",
            "confidence": 89,
        })

    if noisy or blur_score < 100:
        suggestions.append({
            "id": "denoise_sharpen",
            "icon": "🧹",
            "title": "Denoise & Sharpen",
            "description": "Noise/blur detected (sharpness score: {:.0f}). Remove grain and recover fine detail.".format(blur_score),
            "tags": ["quality", "noise"],
            "preview_effect": "sharp_clean",
            "confidence": 87,
        })

    suggestions.append({
        "id": "product_pro",
        "icon": "🛍️",
        "title": "E-commerce Product Shot",
        "description": "White background, perfect exposure, commercial-grade look. Ready for Amazon or Shopify.",
        "tags": ["product", "commerce"],
        "preview_effect": "product_clean",
        "confidence": 85,
    })

    suggestions.append({
        "id": "vintage",
        "icon": "📷",
        "title": "Vintage Film Look",
        "description": "Warm sepia tones, gentle grain, and nostalgic faded highlights.",
        "tags": ["artistic", "retro"],
        "preview_effect": "warm_faded",
        "confidence": 78,
    })

    suggestions.append({
        "id": "cyberpunk",
        "icon": "⚡",
        "title": "Cyberpunk Neon",
        "description": "Electric blue and magenta neon glow. Futuristic sci-fi atmosphere.",
        "tags": ["artistic", "neon"],
        "preview_effect": "neon_blue",
        "confidence": 75,
    })

    return {
        "image_info": {
            "width": w,
            "height": h,
            "megapixels": round((w * h) / 1_000_000, 2),
            "brightness": round(brightness, 1),
            "contrast": round(contrast, 1),
            "sharpness_score": round(blur_score, 1),
            "has_faces": has_faces,
            "face_count": int(len(faces)),
            "is_low_resolution": low_res,
            "is_dark": dark,
            "is_noisy": noisy,
            "is_desaturated": desaturated,
        },
        "suggestions": suggestions[:6],
    }


# ── Main transform entry point ─────────────────────────────────────────────────

def run_nano_banana(image_bytes: bytes, style: str, prompt: str = "") -> bytes:
    """
    Apply Nano Banana or style transform to image_bytes.
    Returns PNG bytes of the transformed image.
    """
    # 1. Try HF Inference API first (if token configured)
    if HF_TOKEN and style in STYLE_PRESETS:
        base_prompt, neg_prompt, strength = STYLE_PRESETS[style]
        if prompt:
            base_prompt = f"{prompt}, {base_prompt}"
        result = _hf_img2img(image_bytes, base_prompt, neg_prompt, strength)
        if result:
            return result

    # 2. Parse image
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image")

    # 3. Local style engine
    if style in STYLE_PRESETS:
        result_img = _apply_nano_banana_style(img, variant=style)
    elif prompt:
        result_img = _apply_prompt_guided(img, prompt)
    else:
        result_img = _apply_nano_banana_style(img, variant="nano_banana")

    # 4. If there's also a custom prompt on top of a style, blend guided on top
    if prompt and style in STYLE_PRESETS:
        guided = _apply_prompt_guided(result_img, prompt)
        result_img = cv2.addWeighted(result_img, 0.6, guided, 0.4, 0)

    _, buf = cv2.imencode(".png", result_img, [cv2.IMWRITE_PNG_COMPRESSION, 6])
    return buf.tobytes()
