"""SpiderGPT Payment Orchestration, Verification, and Webhook Service."""
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.exceptions import (
    NotFoundException,
    PaymentFailedException,
    ProviderUnavailableException,
)
from backend.app.core.logging import logger
from backend.app.models.user import User
from backend.app.models.plan import Plan
from backend.app.models.subscription import Subscription
from backend.app.models.payment import PaymentOrder
from backend.app.schemas.payment import CreateCheckoutSessionRequest, VerifyPaymentRequest
from backend.app.repositories.plan_repo import PlanRepository
from backend.app.repositories.subscription_repo import SubscriptionRepository
from backend.app.repositories.payment_repo import PaymentRepository
from backend.app.providers.payments.factory import PaymentFactory
from backend.app.utils.id_generator import generate_id
from backend.app.utils.timezone import get_utc_now


class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.plan_repo = PlanRepository(db)
        self.sub_repo = SubscriptionRepository(db)
        self.payment_repo = PaymentRepository(db)

    async def get_providers_status(self) -> Dict[str, Any]:
        avail = PaymentFactory.get_availability()
        return {
            "razorpay": avail["razorpay"],
            "stripe": avail["stripe"],
            "default_provider": "razorpay" if avail["razorpay"] else ("stripe" if avail["stripe"] else "none"),
            "preferred_currency": settings.DEFAULT_CURRENCY,
        }

    async def create_checkout_session(
        self,
        user: User,
        request: CreateCheckoutSessionRequest,
    ) -> Dict[str, Any]:
        """Creates checkout order on resolved payment provider and persists order in DB."""
        plan = await self.plan_repo.get_by_code(request.plan_code)
        if not plan:
            raise NotFoundException("Plan", f"Plan '{request.plan_code}' not found.")

        currency = (request.currency or settings.DEFAULT_CURRENCY or "INR").upper()
        billing_period = request.billing_period.lower()

        # Calculate price based on currency & billing period
        if currency == "INR":
            amount = plan.yearly_price_inr if billing_period == "yearly" else plan.monthly_price_inr
        else:
            amount = plan.yearly_price_usd if billing_period == "yearly" else plan.monthly_price_usd

        # Resolve provider
        provider = PaymentFactory.resolve_provider(
            requested_provider=request.provider,
            currency=currency,
        )

        checkout_data = await provider.create_checkout(
            user_id=user.id,
            email=user.email,
            plan_code=plan.code,
            billing_period=billing_period,
            amount=amount,
            currency=currency,
        )

        # Store order
        provider_subscription_id = checkout_data.get("provider_subscription_id")
        order = PaymentOrder(
            id=generate_id("ord"),
            user_id=user.id,
            plan_id=plan.id,
            provider=provider.provider_name,
            order_id=checkout_data["order_id"],
            amount=amount,
            currency=currency,
            status="created",
            metadata_json={"billing_period": billing_period, "plan_code": plan.code, "provider_subscription_id": provider_subscription_id},
        )
        await self.payment_repo.create_order(order)

        return checkout_data

    async def verify_payment(self, user: User, request: VerifyPaymentRequest) -> Dict[str, Any]:
        """Verifies payment transaction and activates user subscription."""
        order = await self.payment_repo.get_order_by_order_id(request.order_id)
        if not order or order.user_id != user.id:
            raise NotFoundException("Order", f"Order {request.order_id} not found.")

        if request.provider and request.provider.lower() != order.provider.lower():
            raise PaymentFailedException("Payment provider does not match the order.")
        provider = PaymentFactory.resolve_provider(requested_provider=order.provider)
        is_valid = await provider.verify_payment(
            order_id=request.order_id,
            payment_id=request.payment_id,
            signature=request.signature,
        )

        if not is_valid:
            order.status = "failed"
            raise PaymentFailedException("Payment signature verification failed.")

        order.status = "paid"
        plan = await self.plan_repo.get_by_id(order.plan_id)
        if not plan:
            raise NotFoundException("Plan", "The plan attached to this order no longer exists.")

        provider_details = await provider.get_checkout_details(order.order_id)
        if not provider_details.get("paid"):
            raise PaymentFailedException("Payment is not confirmed by the payment provider.")

        provider_subscription_id = provider_details.get("provider_subscription_id") or order.metadata_json.get("provider_subscription_id")
        if not provider_subscription_id:
            raise PaymentFailedException("Provider did not return a recurring subscription identifier.")

        billing_period = order.metadata_json.get("billing_period", "monthly")
        now = get_utc_now()
        period_start = provider_details.get("current_period_start") or now
        period_end = provider_details.get("current_period_end")
        if not period_end:
            duration_days = 365 if billing_period == "yearly" else 30
            period_end = now + timedelta(days=duration_days)

        existing_sub = await self.sub_repo.get_by_provider_sub_id(provider_subscription_id)
        if not existing_sub:
            existing_sub = await self.sub_repo.get_active_by_user_id(user.id)

        if existing_sub:
            existing_sub.plan_id = plan.id
            existing_sub.provider = order.provider
            existing_sub.provider_customer_id = provider_details.get("customer_id")
            existing_sub.provider_subscription_id = provider_subscription_id
            existing_sub.billing_period = billing_period
            existing_sub.amount = order.amount
            existing_sub.currency = order.currency
            existing_sub.status = "active"
            existing_sub.cancel_at_period_end = False
            existing_sub.current_period_start = period_start
            existing_sub.current_period_end = period_end
            sub_id = existing_sub.id
        else:
            new_sub = Subscription(
                id=generate_id("sub"),
                user_id=user.id,
                plan_id=plan.id,
                provider=order.provider,
                provider_customer_id=provider_details.get("customer_id"),
                provider_subscription_id=provider_subscription_id,
                billing_period=billing_period,
                amount=order.amount,
                currency=order.currency,
                status="active",
                current_period_start=period_start,
                current_period_end=period_end,
            )
            await self.sub_repo.create(new_sub)
            sub_id = new_sub.id

        return {
            "success": True,
            "message": f"Successfully activated SpiderGPT {plan.name} plan.",
            "subscription_id": sub_id,
            "plan": plan.code,
            "status": "active",
        }

    async def handle_webhook(
        self,
        provider_name: str,
        payload_body: bytes,
        headers: Dict[str, str],
    ) -> Dict[str, Any]:
        """Handles incoming webhook with strict signature verification and idempotency enforcement."""
        provider = PaymentFactory.resolve_provider(requested_provider=provider_name)

        # 1. Verify Signature
        if not provider.verify_webhook_signature(payload_body, headers):
            logger.warning("Rejected unverified %s webhook signature.", provider_name)
            raise PaymentFailedException("Invalid webhook signature.")

        # 2. Parse Normalized Event
        event = provider.parse_webhook_event(payload_body, headers)
        event_id = event["event_id"]

        # 3. Atomically claim the event before applying side effects.
        if not await self.payment_repo.claim_webhook_event(
            event_id=event_id,
            provider=provider_name,
            event_type=event["event_type"],
            payload_summary={"user_id": event.get("user_id"), "status": event["status"]},
        ):
            logger.info("Webhook event %s already processed. Skipping duplicate.", event_id)
            return {"status": "duplicate_skipped", "event_id": event_id}

        # 4. Process event
        logger.info("Processing %s webhook event: %s (%s)", provider_name, event_id, event["event_type"])

        user_id = event.get("user_id")
        plan_code = event.get("plan_code")
        provider_subscription_id = event.get("provider_subscription_id")
        sub = await self.sub_repo.get_by_provider_sub_id(provider_subscription_id) if provider_subscription_id else None

        if not sub and user_id:
            sub = await self.sub_repo.get_active_by_user_id(user_id)

        plan = await self.plan_repo.get_by_code(plan_code) if plan_code else (sub.plan if sub else None)
        if sub:
            sub.status = event["status"]
            if provider_subscription_id:
                sub.provider_subscription_id = provider_subscription_id
            if plan:
                sub.plan_id = plan.id
            if event.get("billing_period"):
                sub.billing_period = event["billing_period"]
            if event.get("current_period_start"):
                sub.current_period_start = datetime.fromtimestamp(event["current_period_start"], tz=timezone.utc) if isinstance(event["current_period_start"], (int, float)) else event["current_period_start"]
            if event.get("current_period_end"):
                sub.current_period_end = datetime.fromtimestamp(event["current_period_end"], tz=timezone.utc) if isinstance(event["current_period_end"], (int, float)) else event["current_period_end"]
            if event["status"] in {"cancelled", "expired"}:
                sub.cancel_at_period_end = False
        elif user_id and plan:
            now = get_utc_now()
            duration = 365 if event.get("billing_period") == "yearly" else 30
            new_sub = Subscription(
                id=generate_id("sub"),
                user_id=user_id,
                plan_id=plan.id,
                provider=provider_name,
                provider_subscription_id=provider_subscription_id,
                billing_period=event.get("billing_period", "monthly"),
                status=event["status"],
                current_period_start=now,
                current_period_end=now + timedelta(days=duration),
            )
            await self.sub_repo.create(new_sub)

        # The event claim is in the same transaction as subscription changes.
        # Failures roll back the claim so the provider can safely retry.
        return {"status": "processed", "event_id": event_id}
