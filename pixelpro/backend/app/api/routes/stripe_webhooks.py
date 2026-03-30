import stripe
from fastapi import APIRouter, Request, HTTPException, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User, PlanType

router = APIRouter(prefix="/stripe", tags=["stripe"])
logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY

PRICE_TO_PLAN = {
    settings.STRIPE_PRICE_STARTER: PlanType.STARTER,
    settings.STRIPE_PRICE_PRO: PlanType.PRO,
    settings.STRIPE_PRICE_BUSINESS: PlanType.BUSINESS,
}

CREDIT_MAP = {
    PlanType.STARTER: settings.STARTER_MONTHLY_CREDITS,
    PlanType.PRO: settings.PRO_MONTHLY_CREDITS,
    PlanType.BUSINESS: settings.BUSINESS_MONTHLY_CREDITS,
}


@router.post("/checkout-session")
async def create_checkout_session(
    price_id: str,
    current_user: User = Depends(lambda: None),  # inject via actual auth
    db: AsyncSession = Depends(get_db),
):
    if price_id not in PRICE_TO_PLAN:
        raise HTTPException(400, "Invalid price ID")

    session = stripe.checkout.Session.create(
        customer_email=current_user.email,
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        mode="subscription",
        success_url="https://pixelpro.app/dashboard?upgraded=true",
        cancel_url="https://pixelpro.app/pricing",
        metadata={"user_id": str(current_user.id)},
    )
    return {"checkout_url": session.url}


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
    db: AsyncSession = Depends(get_db),
):
    payload = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(400, "Invalid signature")

    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        await _handle_checkout_completed(db, data)

    elif event_type == "customer.subscription.updated":
        await _handle_subscription_updated(db, data)

    elif event_type == "customer.subscription.deleted":
        await _handle_subscription_deleted(db, data)

    elif event_type == "invoice.payment_failed":
        logger.warning(f"Payment failed for customer {data.get('customer')}")

    return {"status": "ok"}


async def _handle_checkout_completed(db: AsyncSession, session: dict):
    user_id = session.get("metadata", {}).get("user_id")
    customer_id = session.get("customer")
    subscription_id = session.get("subscription")

    if not user_id:
        return

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return

    # Fetch subscription to get price
    sub = stripe.Subscription.retrieve(subscription_id)
    price_id = sub["items"]["data"][0]["price"]["id"]
    new_plan = PRICE_TO_PLAN.get(price_id, PlanType.FREE)

    user.stripe_customer_id = customer_id
    user.stripe_subscription_id = subscription_id
    user.plan = new_plan
    user.credits_remaining = CREDIT_MAP.get(new_plan, settings.FREE_MONTHLY_CREDITS)
    await db.commit()
    logger.info(f"User {user_id} upgraded to {new_plan}")


async def _handle_subscription_updated(db: AsyncSession, subscription: dict):
    customer_id = subscription.get("customer")
    price_id = subscription["items"]["data"][0]["price"]["id"]
    new_plan = PRICE_TO_PLAN.get(price_id, PlanType.FREE)

    result = await db.execute(select(User).where(User.stripe_customer_id == customer_id))
    user = result.scalar_one_or_none()
    if not user:
        return

    user.plan = new_plan
    user.credits_remaining = CREDIT_MAP.get(new_plan, settings.FREE_MONTHLY_CREDITS)
    await db.commit()


async def _handle_subscription_deleted(db: AsyncSession, subscription: dict):
    customer_id = subscription.get("customer")

    result = await db.execute(select(User).where(User.stripe_customer_id == customer_id))
    user = result.scalar_one_or_none()
    if not user:
        return

    user.plan = PlanType.FREE
    user.stripe_subscription_id = None
    user.credits_remaining = settings.FREE_MONTHLY_CREDITS
    await db.commit()
    logger.info(f"User {user.id} downgraded to free")
