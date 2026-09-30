"""SpiderGPT Subscriptions & Plans Routes."""
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.exceptions import NotFoundException
from backend.app.core.security import get_current_user_from_token
from backend.app.models.user import User
from backend.app.schemas.plan import PlanResponse
from backend.app.schemas.subscription import SubscriptionResponse, CancelSubscriptionRequest
from backend.app.repositories.plan_repo import PlanRepository
from backend.app.repositories.subscription_repo import SubscriptionRepository
from backend.app.providers.payments.factory import PaymentFactory

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.get("/plans", response_model=List[PlanResponse], summary="List all subscription plans and pricing")
async def list_plans(
    db: AsyncSession = Depends(get_db),
):
    repo = PlanRepository(db)
    await repo.seed_plans_if_empty()
    plans = await repo.get_all_active()
    res = []
    for p in plans:
        annual_equiv = 349 if p.code == "PRO" else (899 if p.code == "PLUS" else 0)
        res.append({
            "id": p.id,
            "code": p.code,
            "name": p.name,
            "description": p.description,
            "monthly_price_inr": p.monthly_price_inr // 100,
            "yearly_price_inr": p.yearly_price_inr // 100,
            "monthly_price_usd": p.monthly_price_usd // 100,
            "yearly_price_usd": p.yearly_price_usd // 100,
            "regional_pricing": p.regional_pricing,
            "daily_response_limit": p.daily_response_limit,
            "daily_image_limit": p.daily_image_limit,
            "monthly_name_change_limit": p.monthly_name_change_limit,
            "monthly_appearance_change_limit": p.monthly_appearance_change_limit,
            "custom_appearance_allowed": p.custom_appearance_allowed,
            "allowed_modes": p.allowed_modes,
            "deep_research_allowed": p.deep_research_allowed,
            "annual_monthly_equivalent_inr": annual_equiv,
            "billing_notes": {
                "inr_billing": f"Charged ₹{p.yearly_price_inr // 100} annually (₹{annual_equiv}/mo equivalent)" if p.yearly_price_inr > 0 else "Free",
            },
        })
    return res


@router.get("/me", response_model=Optional[SubscriptionResponse], summary="Get current active user subscription")
async def get_my_subscription(
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    repo = SubscriptionRepository(db)
    sub = await repo.get_active_by_user_id(current_user.id)
    if not sub:
        return None
    return {
        "id": sub.id,
        "user_id": sub.user_id,
        "plan_id": sub.plan_id,
        "plan_code": sub.plan.code if sub.plan else "FREE",
        "plan_name": sub.plan.name if sub.plan else "Free",
        "provider": sub.provider,
        "provider_customer_id": sub.provider_customer_id,
        "provider_subscription_id": sub.provider_subscription_id,
        "billing_period": sub.billing_period,
        "currency": sub.currency,
        "amount": sub.amount,
        "status": sub.status,
        "current_period_start": sub.current_period_start,
        "current_period_end": sub.current_period_end,
        "cancel_at_period_end": sub.cancel_at_period_end,
        "created_at": sub.created_at,
        "updated_at": sub.updated_at,
    }


@router.post("/cancel", status_code=status.HTTP_200_OK, summary="Cancel active subscription")
async def cancel_subscription(
    payload: CancelSubscriptionRequest,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    repo = SubscriptionRepository(db)
    sub = await repo.get_active_by_user_id(current_user.id)
    if not sub:
        raise NotFoundException("Active Subscription")

    if sub.provider_subscription_id and sub.provider != "manual":
        provider = PaymentFactory.resolve_provider(requested_provider=sub.provider)
        provider_ok = await provider.cancel_subscription(sub.provider_subscription_id, cancel_immediately=payload.cancel_immediately)
        if not provider_ok:
            raise NotFoundException("Subscription", "The payment provider could not update the subscription.")

    if payload.cancel_immediately:
        sub.status = "cancelled"
    else:
        sub.cancel_at_period_end = True

    await db.flush()
    return {"message": "Subscription cancellation scheduled successfully."}
