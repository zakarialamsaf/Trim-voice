import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.models.image import Image, Batch, ProcessingStatus
from app.schemas.image import EnhancementOptions


class ImageService:

    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: uuid.UUID,
        original_filename: str,
        original_s3_key: str,
        original_size_bytes: int,
        width: Optional[int],
        height: Optional[int],
        fmt: Optional[str],
        options: EnhancementOptions,
        batch_id: Optional[uuid.UUID] = None,
    ) -> Image:
        credits = ImageService.calculate_credits(options)
        image = Image(
            user_id=user_id,
            original_filename=original_filename,
            original_s3_key=original_s3_key,
            original_size_bytes=original_size_bytes,
            original_width=width,
            original_height=height,
            original_format=fmt,
            enhancement_options=options.model_dump(),
            credits_consumed=credits,
            batch_id=batch_id,
        )
        db.add(image)
        await db.flush()
        return image

    @staticmethod
    def calculate_credits(options: EnhancementOptions) -> int:
        """1 base credit + 1 for face enhance + 1 for bg removal."""
        cost = 1
        if options.face_enhance:
            cost += 1
        if options.remove_background:
            cost += 1
        return cost

    @staticmethod
    async def get(db: AsyncSession, image_id: uuid.UUID) -> Optional[Image]:
        result = await db.execute(select(Image).where(Image.id == image_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_image(
        db: AsyncSession, image_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[Image]:
        result = await db.execute(
            select(Image).where(Image.id == image_id, Image.user_id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_user_images(
        db: AsyncSession, user_id: uuid.UUID, page: int = 1, per_page: int = 20
    ) -> tuple[list[Image], int]:
        offset = (page - 1) * per_page
        total_result = await db.execute(
            select(func.count()).where(Image.user_id == user_id)
        )
        total = total_result.scalar()
        images_result = await db.execute(
            select(Image)
            .where(Image.user_id == user_id)
            .order_by(desc(Image.created_at))
            .offset(offset)
            .limit(per_page)
        )
        return images_result.scalars().all(), total

    @staticmethod
    async def mark_queued(db: AsyncSession, image: Image, task_id: str) -> None:
        image.status = ProcessingStatus.QUEUED
        image.celery_task_id = task_id
        await db.flush()

    @staticmethod
    async def mark_completed(
        db: AsyncSession,
        image: Image,
        enhanced_s3_key: str,
        enhanced_width: int,
        enhanced_height: int,
        enhanced_size_bytes: int,
        processing_time_ms: int,
    ) -> None:
        image.status = ProcessingStatus.COMPLETED
        image.enhanced_s3_key = enhanced_s3_key
        image.enhanced_width = enhanced_width
        image.enhanced_height = enhanced_height
        image.enhanced_size_bytes = enhanced_size_bytes
        image.processing_time_ms = processing_time_ms
        image.completed_at = datetime.now(timezone.utc)
        await db.flush()

    @staticmethod
    async def mark_failed(db: AsyncSession, image: Image, error: str) -> None:
        image.status = ProcessingStatus.FAILED
        image.error_message = error[:1024]
        image.completed_at = datetime.now(timezone.utc)
        await db.flush()

    @staticmethod
    async def create_batch(
        db: AsyncSession,
        user_id: uuid.UUID,
        total: int,
        options: EnhancementOptions,
    ) -> Batch:
        batch = Batch(
            user_id=user_id,
            total_images=total,
            enhancement_options=options.model_dump(),
        )
        db.add(batch)
        await db.flush()
        return batch
