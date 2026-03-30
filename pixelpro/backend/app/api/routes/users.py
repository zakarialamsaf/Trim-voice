from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime, timezone, timedelta

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.image import Image, ProcessingStatus
from app.schemas.user import UserPublic, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserPublic)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserPublic)
async def update_me(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if payload.full_name is not None:
        current_user.full_name = payload.full_name
    if payload.password is not None:
        from app.core.security import hash_password
        current_user.hashed_password = hash_password(payload.password)
    await db.flush()
    return current_user


@router.post("/me/regenerate-api-key")
async def regenerate_api_key(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    new_key = await UserService.regenerate_api_key(db, current_user)
    return {"api_key": new_key}


@router.get("/me/dashboard")
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Total images
    total_result = await db.execute(
        select(func.count()).select_from(Image).where(Image.user_id == current_user.id)
    )
    total_images = total_result.scalar()

    # Images this month
    month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_result = await db.execute(
        select(func.count()).select_from(Image).where(
            Image.user_id == current_user.id,
            Image.created_at >= month_start,
        )
    )
    monthly_images = monthly_result.scalar()

    # Completed vs failed
    stats_result = await db.execute(
        select(Image.status, func.count()).select_from(Image)
        .where(Image.user_id == current_user.id)
        .group_by(Image.status)
    )
    status_counts = {row[0]: row[1] for row in stats_result.all()}

    # Recent images (last 5)
    recent_result = await db.execute(
        select(Image)
        .where(Image.user_id == current_user.id)
        .order_by(desc(Image.created_at))
        .limit(5)
    )
    recent_images = recent_result.scalars().all()

    return {
        "user": {
            "plan": current_user.plan,
            "credits_remaining": current_user.credits_remaining,
            "credits_used_total": current_user.credits_used_total,
        },
        "stats": {
            "total_images": total_images,
            "monthly_images": monthly_images,
            "completed": status_counts.get(ProcessingStatus.COMPLETED, 0),
            "failed": status_counts.get(ProcessingStatus.FAILED, 0),
            "processing": status_counts.get(ProcessingStatus.PROCESSING, 0),
        },
        "recent_images": [
            {
                "id": str(img.id),
                "filename": img.original_filename,
                "status": img.status,
                "created_at": img.created_at.isoformat(),
            }
            for img in recent_images
        ],
    }
