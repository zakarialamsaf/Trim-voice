from fastapi import APIRouter
from app.api.routes import auth, images, users, stripe_webhooks
from app.api.routes import transform

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(images.router)
api_router.include_router(users.router)
api_router.include_router(stripe_webhooks.router)
api_router.include_router(transform.router)
