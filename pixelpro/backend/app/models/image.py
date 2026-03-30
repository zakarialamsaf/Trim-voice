import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, Float, ForeignKey, JSON, Enum as SAEnum, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum

from app.core.database import Base


class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Image(Base):
    __tablename__ = "images"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    # Original file
    original_filename: Mapped[str] = mapped_column(String(255))
    original_s3_key: Mapped[str] = mapped_column(String(512))
    original_size_bytes: Mapped[int] = mapped_column(Integer, nullable=True)
    original_width: Mapped[int] = mapped_column(Integer, nullable=True)
    original_height: Mapped[int] = mapped_column(Integer, nullable=True)
    original_format: Mapped[str] = mapped_column(String(32), nullable=True)

    # Enhanced file
    enhanced_s3_key: Mapped[str] = mapped_column(String(512), nullable=True)
    enhanced_width: Mapped[int] = mapped_column(Integer, nullable=True)
    enhanced_height: Mapped[int] = mapped_column(Integer, nullable=True)
    enhanced_size_bytes: Mapped[int] = mapped_column(Integer, nullable=True)

    # Processing config
    enhancement_options: Mapped[dict] = mapped_column(JSON, default=dict)
    # e.g. {"upscale": 4, "denoise": true, "sharpen": true,
    #        "color_correct": true, "face_enhance": false, "remove_bg": true}

    # Status
    status: Mapped[ProcessingStatus] = mapped_column(
        SAEnum(ProcessingStatus), default=ProcessingStatus.PENDING, index=True
    )
    celery_task_id: Mapped[str] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str] = mapped_column(String(1024), nullable=True)
    processing_time_ms: Mapped[int] = mapped_column(Integer, nullable=True)

    # Credits
    credits_consumed: Mapped[int] = mapped_column(Integer, default=1)

    # Batch
    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("batches.id", ondelete="SET NULL"), nullable=True, index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="images")
    batch: Mapped["Batch"] = relationship("Batch", back_populates="images")


class Batch(Base):
    __tablename__ = "batches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    total_images: Mapped[int] = mapped_column(Integer, default=0)
    completed_images: Mapped[int] = mapped_column(Integer, default=0)
    failed_images: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[ProcessingStatus] = mapped_column(
        SAEnum(ProcessingStatus), default=ProcessingStatus.PENDING
    )
    enhancement_options: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    images: Mapped[list["Image"]] = relationship("Image", back_populates="batch")


class APIUsage(Base):
    __tablename__ = "api_usage"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    endpoint: Mapped[str] = mapped_column(String(128))
    method: Mapped[str] = mapped_column(String(8))
    status_code: Mapped[int] = mapped_column(Integer)
    response_time_ms: Mapped[int] = mapped_column(Integer, nullable=True)
    credits_used: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

    user: Mapped["User"] = relationship("User", back_populates="api_usage")
