import uuid
import secrets
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User, PlanType
from app.core.security import hash_password, verify_password
from app.core.config import settings


class UserService:

    @staticmethod
    async def create(db: AsyncSession, email: str, password: str, full_name: Optional[str] = None) -> User:
        user = User(
            email=email.lower(),
            hashed_password=hash_password(password),
            full_name=full_name,
            credits_remaining=settings.FREE_MONTHLY_CREDITS,
            api_key=secrets.token_urlsafe(32),
        )
        db.add(user)
        await db.flush()
        return user

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.email == email.lower()))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_api_key(db: AsyncSession, api_key: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.api_key == api_key))
        return result.scalar_one_or_none()

    @staticmethod
    async def authenticate(db: AsyncSession, email: str, password: str) -> Optional[User]:
        user = await UserService.get_by_email(db, email)
        if not user or not verify_password(password, user.hashed_password):
            return None
        return user

    @staticmethod
    async def deduct_credits(db: AsyncSession, user: User, amount: int = 1) -> bool:
        if user.credits_remaining < amount:
            return False
        user.credits_remaining -= amount
        user.credits_used_total += amount
        await db.flush()
        return True

    @staticmethod
    async def reset_monthly_credits(db: AsyncSession, user: User) -> None:
        credit_map = {
            PlanType.FREE: settings.FREE_MONTHLY_CREDITS,
            PlanType.STARTER: settings.STARTER_MONTHLY_CREDITS,
            PlanType.PRO: settings.PRO_MONTHLY_CREDITS,
            PlanType.BUSINESS: settings.BUSINESS_MONTHLY_CREDITS,
        }
        user.credits_remaining = credit_map.get(user.plan, settings.FREE_MONTHLY_CREDITS)
        await db.flush()

    @staticmethod
    async def regenerate_api_key(db: AsyncSession, user: User) -> str:
        user.api_key = secrets.token_urlsafe(32)
        await db.flush()
        return user.api_key
