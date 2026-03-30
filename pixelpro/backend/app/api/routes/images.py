import uuid
import io
import math
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from PIL import Image as PILImage

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.models.user import User
from app.models.image import ProcessingStatus
from app.schemas.image import (
    EnhancementOptions,
    ImageUploadResponse,
    ImageStatusResponse,
    ImageResultResponse,
    ImageListResponse,
    BatchCreateRequest,
    BatchStatusResponse,
)
from app.services.user_service import UserService
from app.services.image_service import ImageService
from app.services.s3_service import (
    upload_file_to_s3,
    get_presigned_url,
    generate_s3_key,
)
from app.workers.tasks import enhance_image_task
from app.core.config import settings

router = APIRouter(prefix="/images", tags=["images"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/tiff"}


def _parse_options(
    upscale_factor: int = Form(4),
    denoise: bool = Form(True),
    sharpen: bool = Form(True),
    color_correct: bool = Form(True),
    face_enhance: bool = Form(False),
    remove_background: bool = Form(False),
    output_format: str = Form("png"),
    output_quality: int = Form(95),
) -> EnhancementOptions:
    return EnhancementOptions(
        upscale_factor=upscale_factor,
        denoise=denoise,
        sharpen=sharpen,
        color_correct=color_correct,
        face_enhance=face_enhance,
        remove_background=remove_background,
        output_format=output_format,
        output_quality=output_quality,
    )


@router.post("/upload", response_model=ImageUploadResponse, status_code=201)
async def upload_image(
    file: UploadFile = File(...),
    options: EnhancementOptions = Depends(_parse_options),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, f"Unsupported file type: {file.content_type}")

    # Read and validate size
    file_bytes = await file.read()
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > settings.MAX_IMAGE_SIZE_MB:
        raise HTTPException(400, f"File exceeds {settings.MAX_IMAGE_SIZE_MB}MB limit")

    # Calculate credits needed
    credits_needed = ImageService.calculate_credits(options)
    if current_user.credits_remaining < credits_needed:
        raise HTTPException(402, "Insufficient credits. Please upgrade your plan.")

    # Get image dimensions
    try:
        with PILImage.open(io.BytesIO(file_bytes)) as img:
            width, height = img.size
            fmt = img.format.lower() if img.format else "unknown"
    except Exception:
        raise HTTPException(400, "Invalid or corrupted image file")

    # Upload original to S3
    image_id = uuid.uuid4()
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "jpg"
    s3_key = generate_s3_key(str(current_user.id), str(image_id), "original", ext)
    upload_file_to_s3(file_bytes, s3_key, settings.S3_BUCKET_INPUT, file.content_type)

    # Create DB record
    image = await ImageService.create(
        db,
        user_id=current_user.id,
        original_filename=file.filename,
        original_s3_key=s3_key,
        original_size_bytes=len(file_bytes),
        width=width,
        height=height,
        fmt=fmt,
        options=options,
    )

    # Deduct credits
    await UserService.deduct_credits(db, current_user, credits_needed)

    # Commit now so the eager Celery task (which opens its own DB session) can see the image
    await db.commit()

    # Queue Celery task
    task = enhance_image_task.delay(str(image.id), options.model_dump())

    # Re-fetch image after task (eager mode may have updated it already)
    await db.refresh(image)
    if image.status not in (ProcessingStatus.COMPLETED, ProcessingStatus.FAILED):
        await ImageService.mark_queued(db, image, task.id)

    return ImageUploadResponse(
        image_id=image.id,
        task_id=task.id,
        status=ProcessingStatus.QUEUED,
        message="Image queued for enhancement",
    )


@router.get("/{image_id}/status", response_model=ImageStatusResponse)
async def get_status(
    image_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    image = await ImageService.get_user_image(db, image_id, current_user.id)
    if not image:
        raise HTTPException(404, "Image not found")

    progress = None
    if image.status == ProcessingStatus.PROCESSING:
        progress = 50
    elif image.status == ProcessingStatus.COMPLETED:
        progress = 100

    return ImageStatusResponse(
        image_id=image.id,  # type: ignore[arg-type]
        status=image.status,
        progress_pct=progress,
        error_message=image.error_message,
        created_at=image.created_at,
        completed_at=image.completed_at,
        processing_time_ms=image.processing_time_ms,
    )


def _image_to_response(img) -> ImageResultResponse:
    """Convert ORM Image to ImageResultResponse, resolving storage URLs."""
    original_url = get_presigned_url(img.original_s3_key, settings.S3_BUCKET_INPUT)
    enhanced_url = None
    if img.enhanced_s3_key:
        enhanced_url = get_presigned_url(img.enhanced_s3_key, settings.S3_BUCKET_OUTPUT)
    return ImageResultResponse(
        image_id=img.id,
        status=img.status,
        original_url=original_url,
        enhanced_url=enhanced_url,
        original_width=img.original_width,
        original_height=img.original_height,
        enhanced_width=img.enhanced_width,
        enhanced_height=img.enhanced_height,
        enhancement_options=img.enhancement_options or {},
        processing_time_ms=img.processing_time_ms,
        credits_consumed=img.credits_consumed,
        created_at=img.created_at,
        completed_at=img.completed_at,
    )


@router.get("/{image_id}", response_model=ImageResultResponse)
async def get_image(
    image_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    image = await ImageService.get_user_image(db, image_id, current_user.id)
    if not image:
        raise HTTPException(404, "Image not found")
    return _image_to_response(image)


@router.get("/", response_model=ImageListResponse)
async def list_images(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    images, total = await ImageService.list_user_images(db, current_user.id, page, per_page)
    items = [_image_to_response(img) for img in images]

    return ImageListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page),
    )


@router.post("/batch", response_model=BatchStatusResponse, status_code=201)
async def create_batch(
    files: list[UploadFile] = File(...),
    options_data: BatchCreateRequest = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if len(files) > settings.MAX_BATCH_SIZE:
        raise HTTPException(400, f"Max {settings.MAX_BATCH_SIZE} images per batch")

    options = options_data.enhancement_options
    credits_needed = ImageService.calculate_credits(options) * len(files)
    if current_user.credits_remaining < credits_needed:
        raise HTTPException(402, f"Need {credits_needed} credits, have {current_user.credits_remaining}")

    batch = await ImageService.create_batch(db, current_user.id, len(files), options)

    for file in files:
        file_bytes = await file.read()
        image_id = uuid.uuid4()
        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "jpg"
        s3_key = generate_s3_key(str(current_user.id), str(image_id), "original", ext)
        upload_file_to_s3(file_bytes, s3_key, settings.S3_BUCKET_INPUT, file.content_type)

        try:
            with PILImage.open(io.BytesIO(file_bytes)) as img:
                width, height = img.size
                fmt = img.format.lower() if img.format else "unknown"
        except Exception:
            width = height = None
            fmt = None

        image = await ImageService.create(
            db,
            user_id=current_user.id,
            original_filename=file.filename,
            original_s3_key=s3_key,
            original_size_bytes=len(file_bytes),
            width=width,
            height=height,
            fmt=fmt,
            options=options,
            batch_id=batch.id,
        )
        task = enhance_image_task.delay(str(image.id), options.model_dump())
        await ImageService.mark_queued(db, image, task.id)

    await UserService.deduct_credits(db, current_user, credits_needed)
    return batch
