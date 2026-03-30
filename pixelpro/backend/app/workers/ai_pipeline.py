"""
AI Enhancement Pipeline
=======================
Real AI models — no stubs:

  • Upscaling   → Real-ESRGAN ONNX  (realesr-general-x4v3, CPU/GPU)
                  fallback: LapSRN x4  (OpenCV DNN, always available)
                  fallback: Lanczos  (PIL, always available)
  • Denoising   → OpenCV fastNlMeansDenoisingColored
  • Sharpening  → Unsharp-mask (Gaussian difference)
  • Color corr  → CLAHE on L* channel (LAB colorspace)
  • Face enh    → GFPGAN (optional, requires weights + PyTorch)
  • Bg removal  → rembg u2net (optional, requires rembg package)
"""

from __future__ import annotations

import cv2
import logging
import math
import numpy as np
import os
from pathlib import Path
from typing import Optional

import onnxruntime as ort
from PIL import Image as PILImage

from app.core.config import settings

logger = logging.getLogger(__name__)

MODELS_DIR = Path(getattr(settings, "MODELS_DIR", "models"))

# ── Singleton caches ───────────────────────────────────────────────────────────
_esrgan_session: Optional[ort.InferenceSession] = None
_lapsrn: dict = {}           # scale → cv2 DnnSuperResImpl
_gfpgan_model = None
_rembg_session = None


# ── Model loaders ──────────────────────────────────────────────────────────────

def _load_esrgan() -> Optional[ort.InferenceSession]:
    global _esrgan_session
    if _esrgan_session is not None:
        return _esrgan_session

    model_path = MODELS_DIR / "realesr-general-x4v3.onnx"
    if not model_path.exists():
        logger.warning("Real-ESRGAN ONNX not found at %s", model_path)
        return None

    providers = (["CUDAExecutionProvider", "CPUExecutionProvider"]
                 if ort.get_device() == "GPU"
                 else ["CPUExecutionProvider"])
    try:
        sess_opts = ort.SessionOptions()
        sess_opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        sess_opts.intra_op_num_threads = os.cpu_count() or 4
        _esrgan_session = ort.InferenceSession(str(model_path),
                                               sess_options=sess_opts,
                                               providers=providers)
        logger.info("Real-ESRGAN ONNX loaded (%s)", model_path.name)
        return _esrgan_session
    except Exception as exc:
        logger.error("Failed to load Real-ESRGAN ONNX: %s", exc)
        return None


def _load_lapsrn(scale: int = 4) -> Optional[object]:
    if scale in _lapsrn:
        return _lapsrn[scale]

    model_path = MODELS_DIR / f"LapSRN_x{scale}.pb"
    if not model_path.exists():
        logger.warning("LapSRN x%d not found at %s", scale, model_path)
        return None

    try:
        sr = cv2.dnn_superres.DnnSuperResImpl_create()
        sr.readModel(str(model_path))
        sr.setModel("lapsrn", scale)
        _lapsrn[scale] = sr
        logger.info("LapSRN x%d loaded", scale)
        return sr
    except Exception as exc:
        logger.error("Failed to load LapSRN x%d: %s", scale, exc)
        return None


def _get_gfpgan():
    global _gfpgan_model
    if _gfpgan_model is not None:
        return _gfpgan_model
    try:
        from gfpgan import GFPGANer
        model_path = MODELS_DIR / "GFPGANv1.4.pth"
        if not model_path.exists():
            return None
        _gfpgan_model = GFPGANer(
            model_path=str(model_path), upscale=1,
            arch="clean", channel_multiplier=2, bg_upsampler=None,
        )
        logger.info("GFPGAN loaded")
        return _gfpgan_model
    except (ImportError, Exception) as exc:
        logger.info("GFPGAN unavailable: %s", exc)
        return None


def _get_rembg():
    global _rembg_session
    if _rembg_session is not None:
        return _rembg_session
    try:
        from rembg import new_session
        _rembg_session = new_session("u2net")
        logger.info("rembg u2net loaded")
        return _rembg_session
    except (ImportError, Exception) as exc:
        logger.info("rembg unavailable: %s", exc)
        return None


# ── Core enhancement steps ─────────────────────────────────────────────────────

TILE_SIZE = 256   # pixels per tile fed to ESRGAN
TILE_PAD  = 16    # overlap padding to avoid seam artifacts


def _esrgan_tile(img_bgr: np.ndarray) -> np.ndarray:
    """Run Real-ESRGAN ONNX on the image using tiling (handles any resolution)."""
    sess = _load_esrgan()
    if sess is None:
        raise RuntimeError("ESRGAN not available")

    inp_name = sess.get_inputs()[0].name
    h, w = img_bgr.shape[:2]

    # Pad image to multiple of TILE_SIZE
    pad_h = math.ceil(h / TILE_SIZE) * TILE_SIZE
    pad_w = math.ceil(w / TILE_SIZE) * TILE_SIZE
    img_padded = cv2.copyMakeBorder(img_bgr, 0, pad_h - h, 0, pad_w - w,
                                    cv2.BORDER_REFLECT_101)

    scale = 4
    out_h, out_w = pad_h * scale, pad_w * scale
    output = np.zeros((out_h, out_w, 3), dtype=np.float32)

    tiles_y = pad_h // TILE_SIZE
    tiles_x = pad_w // TILE_SIZE

    for ty in range(tiles_y):
        for tx in range(tiles_x):
            y0 = ty * TILE_SIZE
            x0 = tx * TILE_SIZE
            # Extract tile with padding
            y0p = max(0, y0 - TILE_PAD)
            x0p = max(0, x0 - TILE_PAD)
            y1p = min(pad_h, y0 + TILE_SIZE + TILE_PAD)
            x1p = min(pad_w, x0 + TILE_SIZE + TILE_PAD)

            tile = img_padded[y0p:y1p, x0p:x1p]

            # BGR → RGB, HWC → NCHW, [0,255] → [0,1]
            tile_rgb = cv2.cvtColor(tile, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
            tile_t = tile_rgb.transpose(2, 0, 1)[np.newaxis]

            out_tile = sess.run(None, {inp_name: tile_t})[0][0]  # CHW float

            # CHW → HWC, clip [0,1]
            out_tile = np.clip(out_tile.transpose(1, 2, 0), 0, 1)

            # Map padded output coords back to unpadded output
            oy0 = (y0 - y0p) * scale
            ox0 = (x0 - x0p) * scale
            oy1 = oy0 + TILE_SIZE * scale
            ox1 = ox0 + TILE_SIZE * scale

            # Write into output canvas
            out_oy0 = ty * TILE_SIZE * scale
            out_ox0 = tx * TILE_SIZE * scale
            output[out_oy0:out_oy0 + TILE_SIZE * scale,
                   out_ox0:out_ox0 + TILE_SIZE * scale] = \
                out_tile[oy0:oy1, ox0:ox1]

    # Crop back to original size * scale
    output = output[:h * scale, :w * scale]
    out_bgr = cv2.cvtColor((output * 255).astype(np.uint8), cv2.COLOR_RGB2BGR)
    return out_bgr


def upscale(img_array: np.ndarray, scale: int = 4) -> np.ndarray:
    """
    Upscale with the best available model:
      1. Real-ESRGAN ONNX (AI, best quality)
      2. LapSRN x4 (AI, OpenCV DNN, good quality)
      3. Lanczos (PIL, no AI, fallback)
    """
    # Real-ESRGAN: supports x4 natively; for x2 we run once and resize down
    try:
        logger.debug("Upscale: trying Real-ESRGAN ONNX x%d", scale)
        out4x = _esrgan_tile(img_array)
        if scale == 4:
            return out4x
        # scale == 2: downscale from 4x to 2x with high-quality Lanczos
        h, w = img_array.shape[:2]
        pil = PILImage.fromarray(cv2.cvtColor(out4x, cv2.COLOR_BGR2RGB))
        pil = pil.resize((w * scale, h * scale), PILImage.LANCZOS)
        return cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    except Exception as exc:
        logger.warning("Real-ESRGAN failed (%s), trying LapSRN", exc)

    # LapSRN fallback (x4 model used regardless, same downscale trick for x2)
    sr = _load_lapsrn(4)
    if sr:
        try:
            logger.debug("Upscale: using LapSRN x4")
            out4x = sr.upsample(img_array)
            if scale == 4:
                return out4x
            h, w = img_array.shape[:2]
            pil = PILImage.fromarray(cv2.cvtColor(out4x, cv2.COLOR_BGR2RGB))
            pil = pil.resize((w * scale, h * scale), PILImage.LANCZOS)
            return cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
        except Exception as exc:
            logger.warning("LapSRN failed (%s), falling back to Lanczos", exc)

    # Lanczos last resort
    logger.debug("Upscale: using Lanczos (no AI model available)")
    pil = PILImage.fromarray(cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB))
    h, w = img_array.shape[:2]
    pil = pil.resize((w * scale, h * scale), PILImage.LANCZOS)
    return cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)


def denoise(img_array: np.ndarray) -> np.ndarray:
    """OpenCV Non-Local Means denoising (colour-aware)."""
    return cv2.fastNlMeansDenoisingColored(
        img_array, None, h=10, hColor=10,
        templateWindowSize=7, searchWindowSize=21
    )


def sharpen(img_array: np.ndarray) -> np.ndarray:
    """Unsharp mask — sharpen without amplifying noise."""
    blur = cv2.GaussianBlur(img_array, (0, 0), sigmaX=1.5)
    sharpened = cv2.addWeighted(img_array, 1.4, blur, -0.4, 0)
    return sharpened


def color_correct(img_array: np.ndarray) -> np.ndarray:
    """CLAHE on the L* channel + subtle vibrance boost."""
    lab = cv2.cvtColor(img_array, cv2.COLOR_BGR2LAB)
    l_ch, a_ch, b_ch = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_ch = clahe.apply(l_ch)
    lab = cv2.merge([l_ch, a_ch, b_ch])
    result = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    # Subtle saturation boost (+10%)
    hsv = cv2.cvtColor(result, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.10, 0, 255)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)


def enhance_faces(img_array: np.ndarray) -> np.ndarray:
    gfpgan = _get_gfpgan()
    if not gfpgan:
        return img_array
    try:
        img_rgb = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
        _, _, restored = gfpgan.enhance(
            img_rgb, has_aligned=False, only_center_face=False, paste_back=True
        )
        if restored is not None:
            return cv2.cvtColor(restored, cv2.COLOR_RGB2BGR)
    except Exception as exc:
        logger.error("GFPGAN error: %s", exc)
    return img_array


def remove_background(img_bytes: bytes) -> bytes:
    session = _get_rembg()
    if not session:
        logger.info("rembg unavailable, skipping bg removal")
        return img_bytes
    try:
        from rembg import remove
        return remove(img_bytes, session=session)
    except Exception as exc:
        logger.error("rembg error: %s", exc)
        return img_bytes


# ── Pre-warm (call once at startup) ───────────────────────────────────────────

def warm_up():
    """Load models into memory at app startup so first request is fast."""
    logger.info("Warming up AI models...")
    _load_esrgan()
    _load_lapsrn(4)
    logger.info("AI models ready")


# ── Main pipeline ──────────────────────────────────────────────────────────────

def run_pipeline(image_bytes: bytes, options: dict) -> bytes:
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image — unsupported format or corrupted file")

    logger.info("Pipeline start  size=%dx%d  options=%s", img.shape[1], img.shape[0], options)

    if options.get("denoise"):
        logger.debug("Step: denoise")
        img = denoise(img)

    if options.get("upscale_factor", 1) > 1:
        logger.debug("Step: upscale x%d", options["upscale_factor"])
        img = upscale(img, scale=int(options["upscale_factor"]))

    if options.get("face_enhance"):
        logger.debug("Step: face_enhance")
        img = enhance_faces(img)

    if options.get("sharpen"):
        logger.debug("Step: sharpen")
        img = sharpen(img)

    if options.get("color_correct"):
        logger.debug("Step: color_correct")
        img = color_correct(img)

    logger.info("Pipeline done   output=%dx%d", img.shape[1], img.shape[0])

    # --- Encode output ---
    out_fmt = options.get("output_format", "png").lower()
    quality = int(options.get("output_quality", 95))

    if options.get("remove_background"):
        logger.debug("Step: remove_background")
        _, buf = cv2.imencode(".png", img)
        return remove_background(buf.tobytes())

    encode_map = {
        "jpg":  (".jpg",  [cv2.IMWRITE_JPEG_QUALITY, quality]),
        "webp": (".webp", [cv2.IMWRITE_WEBP_QUALITY, quality]),
        "png":  (".png",  [cv2.IMWRITE_PNG_COMPRESSION, 6]),
    }
    ext, params = encode_map.get(out_fmt, encode_map["png"])
    _, buf = cv2.imencode(ext, img, params)
    return buf.tobytes()
