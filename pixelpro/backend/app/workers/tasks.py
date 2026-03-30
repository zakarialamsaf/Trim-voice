import uuid
import time
import logging
import threading
import asyncio
from datetime import datetime, timezone

from app.workers.celery_app import celery_app
from app.core.config import settings

logger = logging.getLogger(__name__)


def _run_async(coro):
    """
    Run an async coroutine safely regardless of whether there's already
    a running event loop (e.g. when Celery task_always_eager=True calls
    us from inside FastAPI's event loop).
    """
    result = [None]
    exc_holder = [None]

    def _thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result[0] = loop.run_until_complete(coro)
        except Exception as e:
            exc_holder[0] = e
        finally:
            loop.close()

    t = threading.Thread(target=_thread, daemon=True)
    t.start()
    t.join()

    if exc_holder[0]:
        raise exc_holder[0]
    return result[0]


@celery_app.task(
    name="app.workers.tasks.enhance_image_task",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    acks_late=True,
    queue="enhancement",
)
def enhance_image_task(self, image_id: str, options: dict):
    _run_async(_enhance_async(image_id, options))


async def _enhance_async(image_id: str, options: dict):
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal
    from app.models.image import Image, ProcessingStatus
    from app.models.user import User
    from app.services.s3_service import (
        download_file_from_s3,
        upload_file_to_s3,
        generate_s3_key,
    )
    from app.workers.ai_pipeline import run_pipeline
    import cv2
    import numpy as np

    logger.info(f"Starting enhancement for image {image_id}")

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Image).where(Image.id == uuid.UUID(image_id)))
        image = result.scalar_one_or_none()
        if not image:
            logger.error(f"Image {image_id} not found in DB")
            return

        image.status = ProcessingStatus.PROCESSING
        await db.commit()

        start_ms = int(time.time() * 1000)

        try:
            file_bytes = download_file_from_s3(image.original_s3_key, settings.S3_BUCKET_INPUT)
            enhanced_bytes = run_pipeline(file_bytes, options)

            # Get enhanced dimensions
            nparr = np.frombuffer(enhanced_bytes, np.uint8)
            enhanced_img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
            if enhanced_img is not None:
                eh, ew = enhanced_img.shape[:2]
            else:
                ew = (image.original_width or 0) * options.get("upscale_factor", 1)
                eh = (image.original_height or 0) * options.get("upscale_factor", 1)

            out_fmt = options.get("output_format", "png")
            enhanced_key = generate_s3_key(str(image.user_id), image_id, "enhanced", out_fmt)
            content_type_map = {"png": "image/png", "jpg": "image/jpeg", "webp": "image/webp"}
            upload_file_to_s3(enhanced_bytes, enhanced_key, settings.S3_BUCKET_OUTPUT,
                              content_type_map.get(out_fmt, "image/png"))

            elapsed = int(time.time() * 1000) - start_ms
            image.status = ProcessingStatus.COMPLETED
            image.enhanced_s3_key = enhanced_key
            image.enhanced_width = ew
            image.enhanced_height = eh
            image.enhanced_size_bytes = len(enhanced_bytes)
            image.processing_time_ms = elapsed
            image.completed_at = datetime.now(timezone.utc)
            logger.info(f"Image {image_id} enhanced in {elapsed}ms")

        except Exception as exc:
            logger.error(f"Enhancement failed for {image_id}: {exc}", exc_info=True)
            image.status = ProcessingStatus.FAILED
            image.error_message = str(exc)[:1024]
            image.completed_at = datetime.now(timezone.utc)

            # Refund credits
            user_result = await db.execute(select(User).where(User.id == image.user_id))
            user = user_result.scalar_one_or_none()
            if user:
                user.credits_remaining += image.credits_consumed
                user.credits_used_total -= image.credits_consumed

        await db.commit()

        if image.batch_id:
            await _update_batch(db, image.batch_id)


async def _update_batch(db, batch_id):
    from sqlalchemy import select, func
    from app.models.image import Batch, Image, ProcessingStatus

    result = await db.execute(select(Batch).where(Batch.id == batch_id))
    batch = result.scalar_one_or_none()
    if not batch:
        return

    counts = await db.execute(
        select(Image.status, func.count())
        .where(Image.batch_id == batch_id)
        .group_by(Image.status)
    )
    status_map = {row[0]: row[1] for row in counts.all()}
    batch.completed_images = status_map.get(ProcessingStatus.COMPLETED, 0)
    batch.failed_images = status_map.get(ProcessingStatus.FAILED, 0)
    total_done = batch.completed_images + batch.failed_images
    if total_done >= batch.total_images:
        batch.status = (ProcessingStatus.COMPLETED if batch.failed_images == 0
                        else ProcessingStatus.FAILED)
    await db.flush()


@celery_app.task(name="app.workers.tasks.reset_all_monthly_credits")
def reset_all_monthly_credits():
    _run_async(_reset_credits_async())


async def _reset_credits_async():
    from datetime import timedelta
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal
    from app.models.user import User
    from app.core.config import settings

    credit_map = {
        "free": settings.FREE_MONTHLY_CREDITS,
        "starter": settings.STARTER_MONTHLY_CREDITS,
        "pro": settings.PRO_MONTHLY_CREDITS,
        "business": settings.BUSINESS_MONTHLY_CREDITS,
    }

    now = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.credits_reset_at <= now, User.is_active == True)
        )
        users = result.scalars().all()
        for user in users:
            user.credits_remaining = credit_map.get(user.plan, settings.FREE_MONTHLY_CREDITS)
            user.credits_reset_at = now + timedelta(days=30)
        await db.commit()
        logger.info(f"Reset credits for {len(users)} users")
