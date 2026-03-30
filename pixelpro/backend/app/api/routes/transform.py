"""
Transform Routes
================
POST /transform/nano-banana  → Apply Nano Banana / style transform with optional prompt
POST /transform/analyze      → Analyze image and return personalized suggestions
"""

import uuid
import io
import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from PIL import Image as PILImage

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.models.user import User
from app.models.image import ProcessingStatus
from app.services.image_service import ImageService
from app.services.user_service import UserService
from app.services.s3_service import (
    upload_file_to_s3,
    download_file_from_s3,
    generate_s3_key,
    get_presigned_url,
)

router = APIRouter(prefix="/transform", tags=["transform"])
logger = logging.getLogger(__name__)

ALLOWED_STYLES = {
    "nano_banana", "nano_banana_2", "nano_banana_pro",
    "product_pro", "vintage", "cyberpunk",
}


@router.get("/provider-status")
async def provider_status(current_user: User = Depends(get_current_user)):
    """Return which AI edit providers are configured (fal.ai, HuggingFace)."""
    from app.workers.ai_edit import get_provider_status
    return get_provider_status()


@router.post("/edit")
async def ai_edit(
    file: UploadFile = File(...),
    prompt: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    **Instruction-following AI image editor.**

    Give any natural-language instruction and AI will edit the image content:
    - "make the person wear a suit"
    - "change background to beach"
    - "add glasses to the person"
    - "make it night time"
    - "change the car to red"
    - "put a hat on the person"

    Requires FAL_KEY or HF_TOKEN configured in .env.local
    (both have free tiers — see /transform/provider-status for setup links).
    """
    from app.workers.ai_edit import run_ai_edit, ConfigurationError

    if current_user.credits_remaining < 1:
        raise HTTPException(402, "Not enough credits")

    raw = await file.read()
    if len(raw) > settings.MAX_IMAGE_SIZE_MB * 1024 * 1024:
        raise HTTPException(413, f"File too large (max {settings.MAX_IMAGE_SIZE_MB}MB)")

    try:
        with PILImage.open(io.BytesIO(raw)) as pil_img:
            orig_w, orig_h = pil_img.size
            orig_fmt = (pil_img.format or "jpg").lower()
    except Exception:
        raise HTTPException(400, "Invalid image file")

    from app.models.image import Image as ImageModel
    import cv2

    image_id = str(uuid.uuid4())
    s3_orig_key = generate_s3_key(str(current_user.id), image_id, "original", orig_fmt)
    upload_file_to_s3(raw, s3_orig_key, settings.S3_BUCKET_INPUT, file.content_type or "image/jpeg")

    image = ImageModel(
        id=uuid.UUID(image_id),
        user_id=current_user.id,
        original_filename=file.filename or f"edit_{image_id}.jpg",
        original_s3_key=s3_orig_key,
        original_size_bytes=len(raw),
        original_width=orig_w,
        original_height=orig_h,
        original_format=orig_fmt,
        enhancement_options={"prompt": prompt, "transform": "ai_edit"},
        credits_consumed=1,
    )
    db.add(image)
    await db.flush()
    await UserService.deduct_credits(db, current_user, 1)
    await db.commit()

    try:
        image.status = ProcessingStatus.PROCESSING
        await db.commit()

        edited_bytes = run_ai_edit(raw, prompt)

        nparr = __import__("numpy").frombuffer(edited_bytes, __import__("numpy").uint8)
        out_img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
        out_h, out_w = (out_img.shape[:2] if out_img is not None else (orig_h, orig_w))

        s3_out_key = generate_s3_key(str(current_user.id), str(image.id), "edited", "jpg")
        upload_file_to_s3(edited_bytes, s3_out_key, settings.S3_BUCKET_OUTPUT, "image/jpeg")

        image.status = ProcessingStatus.COMPLETED
        image.enhanced_s3_key = s3_out_key
        image.enhanced_width = out_w
        image.enhanced_height = out_h
        image.enhanced_size_bytes = len(edited_bytes)
        await db.commit()

    except ConfigurationError as cfg_err:
        image.status = ProcessingStatus.FAILED
        image.error_message = str(cfg_err)
        await db.commit()
        current_user.credits_remaining += 1
        await db.commit()
        raise HTTPException(503, {
            "error": "no_provider",
            "message": str(cfg_err),
            "fix": "Add FAL_KEY or HF_TOKEN to .env.local",
            "providers": {
                "fal_ai": {"url": "https://fal.ai/dashboard/keys", "env": "FAL_KEY", "free": True},
                "huggingface": {"url": "https://huggingface.co/settings/tokens", "env": "HF_TOKEN", "free": True},
            },
        })
    except Exception as exc:
        logger.error("AI edit failed: %s", exc, exc_info=True)
        image.status = ProcessingStatus.FAILED
        image.error_message = str(exc)[:512]
        await db.commit()
        current_user.credits_remaining += 1
        await db.commit()
        raise HTTPException(500, f"Edit failed: {exc}")

    original_url = get_presigned_url(s3_orig_key, settings.S3_BUCKET_INPUT)
    edited_url = get_presigned_url(s3_out_key, settings.S3_BUCKET_OUTPUT)

    return {
        "image_id": str(image.id),
        "status": "completed",
        "prompt": prompt,
        "original_url": original_url,
        "edited_url": edited_url,
        "original_width": orig_w,
        "original_height": orig_h,
        "output_width": out_w,
        "output_height": out_h,
        "credits_used": 1,
        "message": "AI edit complete ✨",
    }


@router.post("/analyze")
async def analyze_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """
    Upload an image and get back:
    - Image quality analysis (brightness, sharpness, faces, etc.)
    - 6 personalised AI transformation suggestions
    """
    from app.workers.nano_banana import analyze_image as _analyze

    raw = await file.read()
    if len(raw) > settings.MAX_IMAGE_SIZE_MB * 1024 * 1024:
        raise HTTPException(413, f"File too large (max {settings.MAX_IMAGE_SIZE_MB}MB)")

    # Quick format check
    try:
        with PILImage.open(io.BytesIO(raw)) as img:
            img.verify()
    except Exception:
        raise HTTPException(400, "Invalid or corrupted image file")

    try:
        analysis = _analyze(raw)
    except Exception as e:
        logger.error("Image analysis failed: %s", e, exc_info=True)
        raise HTTPException(500, "Image analysis failed")

    return analysis


@router.post("/nano-banana")
async def nano_banana_transform(
    file: UploadFile = File(...),
    style: str = Form(default="nano_banana"),
    prompt: str = Form(default=""),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Apply Nano Banana style (or any preset style) to an uploaded image.

    **style** options:
    - `nano_banana`     — Classic Nano Banana figurine (warm, toy, plastic)
    - `nano_banana_2`   — Nano Banana 2 (pastel, vibrant)
    - `nano_banana_pro` — Nano Banana PRO (metallic, luxury)
    - `product_pro`     — E-commerce product shot (white bg, studio)
    - `vintage`         — Vintage film aesthetic
    - `cyberpunk`       — Neon cyberpunk grade

    **prompt** (optional): free-text guidance e.g. "make it brighter and sharper"
    """
    from app.workers.nano_banana import run_nano_banana

    if style not in ALLOWED_STYLES:
        raise HTTPException(422, f"Unknown style '{style}'. Choose from: {sorted(ALLOWED_STYLES)}")

    # Credit check (1 credit per transform)
    credits_needed = 1
    if current_user.credits_remaining < credits_needed:
        raise HTTPException(402, "Not enough credits")

    raw = await file.read()
    if len(raw) > settings.MAX_IMAGE_SIZE_MB * 1024 * 1024:
        raise HTTPException(413, f"File too large (max {settings.MAX_IMAGE_SIZE_MB}MB)")

    try:
        with PILImage.open(io.BytesIO(raw)) as pil_img:
            orig_w, orig_h = pil_img.size
            orig_fmt = (pil_img.format or "jpg").lower()
    except Exception:
        raise HTTPException(400, "Invalid image file")

    from app.models.image import Image as ImageModel

    image_id = str(uuid.uuid4())
    s3_orig_key = generate_s3_key(str(current_user.id), image_id, "original", orig_fmt)
    upload_file_to_s3(raw, s3_orig_key, settings.S3_BUCKET_INPUT, file.content_type or "image/jpeg")

    # Create DB record directly (options are a plain dict for style transforms)
    image = ImageModel(
        id=uuid.UUID(image_id),
        user_id=current_user.id,
        original_filename=file.filename or f"transform_{image_id}.jpg",
        original_s3_key=s3_orig_key,
        original_size_bytes=len(raw),
        original_width=orig_w,
        original_height=orig_h,
        original_format=orig_fmt,
        enhancement_options={"style": style, "prompt": prompt, "transform": "nano_banana"},
        credits_consumed=credits_needed,
    )
    db.add(image)
    await db.flush()
    await UserService.deduct_credits(db, current_user, credits_needed)
    await db.commit()

    # Run transform (synchronous — fast enough for local engine)
    try:
        image.status = ProcessingStatus.PROCESSING
        await db.commit()

        transformed_bytes = run_nano_banana(raw, style=style, prompt=prompt)

        # Get output dimensions
        nparr_out = __import__("numpy").frombuffer(transformed_bytes, __import__("numpy").uint8)
        import cv2
        out_img = cv2.imdecode(nparr_out, cv2.IMREAD_UNCHANGED)
        out_h, out_w = (out_img.shape[:2] if out_img is not None else (orig_h, orig_w))

        s3_out_key = generate_s3_key(str(current_user.id), str(image.id), "transformed", "png")
        upload_file_to_s3(transformed_bytes, s3_out_key, settings.S3_BUCKET_OUTPUT, "image/png")

        image.status = ProcessingStatus.COMPLETED
        image.enhanced_s3_key = s3_out_key
        image.enhanced_width = out_w
        image.enhanced_height = out_h
        image.enhanced_size_bytes = len(transformed_bytes)
        await db.commit()

    except Exception as exc:
        logger.error("Nano Banana transform failed: %s", exc, exc_info=True)
        image.status = ProcessingStatus.FAILED
        image.error_message = str(exc)[:512]
        await db.commit()
        # Refund credits
        current_user.credits_remaining += credits_needed
        await db.commit()
        raise HTTPException(500, f"Transform failed: {exc}")

    original_url = get_presigned_url(s3_orig_key, settings.S3_BUCKET_INPUT)
    transformed_url = get_presigned_url(s3_out_key, settings.S3_BUCKET_OUTPUT)

    return {
        "image_id": str(image.id),
        "status": "completed",
        "style": style,
        "prompt": prompt,
        "original_url": original_url,
        "transformed_url": transformed_url,
        "original_width": orig_w,
        "original_height": orig_h,
        "output_width": out_w,
        "output_height": out_h,
        "credits_used": credits_needed,
        "message": f"Nano Banana '{style}' transform complete ✨",
    }
