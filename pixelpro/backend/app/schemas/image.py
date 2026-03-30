from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.models.image import ProcessingStatus


class EnhancementOptions(BaseModel):
    upscale_factor: int = Field(default=4, ge=2, le=4, description="2x or 4x upscaling")
    denoise: bool = True
    sharpen: bool = True
    color_correct: bool = True
    face_enhance: bool = False
    remove_background: bool = False
    output_format: str = Field(default="png", pattern="^(png|jpg|webp)$")
    output_quality: int = Field(default=95, ge=70, le=100)


class ImageUploadResponse(BaseModel):
    image_id: UUID
    task_id: str
    status: ProcessingStatus
    message: str


class ImageStatusResponse(BaseModel):
    image_id: UUID
    status: ProcessingStatus
    progress_pct: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    processing_time_ms: Optional[int] = None


class ImageResultResponse(BaseModel):
    image_id: UUID
    status: ProcessingStatus
    original_url: Optional[str] = None
    enhanced_url: Optional[str] = None
    original_width: Optional[int] = None
    original_height: Optional[int] = None
    enhanced_width: Optional[int] = None
    enhanced_height: Optional[int] = None
    enhancement_options: dict = {}
    processing_time_ms: Optional[int] = None
    credits_consumed: int = 1
    created_at: datetime
    completed_at: Optional[datetime] = None


class ImageListResponse(BaseModel):
    items: list[ImageResultResponse]
    total: int
    page: int
    per_page: int
    pages: int


class BatchCreateRequest(BaseModel):
    enhancement_options: EnhancementOptions = EnhancementOptions()


class BatchStatusResponse(BaseModel):
    batch_id: UUID
    status: ProcessingStatus
    total_images: int
    completed_images: int
    failed_images: int
    created_at: datetime

    model_config = {"from_attributes": True}
