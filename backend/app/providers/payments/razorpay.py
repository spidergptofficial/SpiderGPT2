"""SpiderGPT Razorpay payment provider."""
import base64
import json
import uuid
from typing import Dict, Any, Optional
import httpx

from backend.app.core.config import settings
from backend.app.core.exceptions import PaymentFailedException
from backend.app.core.logging import logger
from backend.app.providers.payments.base import PaymentProvider
from backend.app.utils.security import verify_razorpay_signature


class RazorpayPaymentProvider(PaymentProvider):
    def __init__(self):
        self.key_id = settings.RAZORPAY_KEY_ID
        self.key_secret = settings.RAZORPAY_KEY_SECRET
        self.webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET
        self.base_url = "https://api.razorpay.com/v1"

    @property
    def provider_name(self) -> str:
        return "razorpay"

    @property
    def is_configured(self) -> bool:
        return bool(self.key_id and self.key_secret)

    def _get_auth_header(self) -> Dict[str, str]:
        encoded = base64.b64encode(f"{self.key_id}:{self.key_secret}".encode()).decode()
        return {"Authorization": f"Basic {encoded}"}

    def _require_configured(self) -> None:
        if not self.is_configured:
            if settings.ENVIRONMENT == "production":
                raise PaymentFailedException("Razorpay is not configured.")
            raise PaymentFailedException("Razorpay is not configured.")

    async def create_checkout(self, user_id: str, email: str, plan_code: str, billing_period: str,
                              amount: int, currency: str = "INR",
                              metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self._require_configured()
        notes = {"user_id": user_id, "email": email, "plan_code": plan_code, "billing_period": billing_period}
        if metadata:
            notes.update({k: str(v) for k, v in metadata.items()})
        plan_key = f"RAZORPAY_PLAN_{plan_code.upper()}_{billing_period.upper()}"
        plan_id = getattr(settings, plan_key, None)
        if not plan_id:
            raise PaymentFailedException(f"Razorpay recurring plan is not configured for {plan_code}/{billing_period}.")
        payload = {
            "plan_id": plan_id,
            "total_count": 12 if billing_period == "monthly" else 1,
            "quantity": 1,
            "customer_notify": 1,
            "notes": notes,
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                resp = await client.post(f"{self.base_url}/subscriptions", headers=self._get_auth_header(), json=payload)
                if resp.status_code not in (200, 201):
                    logger.error("Razorpay order creation error (%d): %s", resp.status_code, resp.text[:200])
                    raise PaymentFailedException("Failed to initiate Razorpay subscription checkout.")
                data = resp.json()
                return {"provider": self.provider_name, "order_id": data.get("id"), "amount": amount,
                        "currency": currency, "key_id": self.key_id, "client_secret": None,
                        "checkout_url": None, "provider_subscription_id": data.get("id"), "metadata": notes}
            except httpx.RequestError:
                logger.exception("Razorpay network request error")
                raise PaymentFailedException("Could not connect to payment gateway.")

    async def verify_payment(self, order_id: str, payment_id: Optional[str] = None,
                             signature: Optional[str] = None) -> bool:
        if not self.is_configured:
            return False
        if not payment_id or not signature or not self.key_secret:
            return False
        # For Razorpay subscriptions the checkout identifier is the subscription ID.
        return verify_razorpay_signature(f"{payment_id}|{order_id}".encode(), signature, self.key_secret)

    async def get_checkout_details(self, checkout_id: str) -> Dict[str, Any]:
        self._require_configured()
        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                resp = await client.get(f"{self.base_url}/subscriptions/{checkout_id}", headers=self._get_auth_header())
                if resp.status_code != 200:
                    return {}
                data = resp.json()
                return {
                    "paid": data.get("status") in {"active", "authenticated", "completed"},
                    "provider_subscription_id": data.get("id"),
                    "customer_id": data.get("customer_id"),
                    "status": data.get("status"),
                    "current_period_start": data.get("current_start"),
                    "current_period_end": data.get("current_end"),
                }
            except httpx.RequestError:
                logger.exception("Razorpay subscription retrieval error")
                return {}

    async def cancel_subscription(self, provider_subscription_id: str, cancel_immediately: bool = False) -> bool:
        self._require_configured()
        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                resp = await client.post(
                    f"{self.base_url}/subscriptions/{provider_subscription_id}/cancel",
                    headers=self._get_auth_header(), json={"cancel_at_cycle_end": 0 if cancel_immediately else 1},
                )
                return resp.status_code in (200, 204)
            except httpx.RequestError:
                logger.exception("Razorpay cancel subscription error")
                return False

    def verify_webhook_signature(self, payload_body: bytes, headers: Dict[str, str]) -> bool:
        if not self.webhook_secret:
            return False
        sig = headers.get("X-Razorpay-Signature") or headers.get("x-razorpay-signature", "")
        return verify_razorpay_signature(payload_body, sig, self.webhook_secret)

    def parse_webhook_event(self, payload_body: bytes, headers: Dict[str, str]) -> Dict[str, Any]:
        data = json.loads(payload_body.decode("utf-8"))
        event_type = data.get("event", "")
        payment_entity = data.get("payload", {}).get("payment", {}).get("entity", {})
        subscription_entity = data.get("payload", {}).get("subscription", {}).get("entity", {})
        entity = subscription_entity or payment_entity
        event_id = data.get("event_id") or payment_entity.get("id") or subscription_entity.get("id")
        if not event_id:
            raise PaymentFailedException("Razorpay webhook event ID is missing.")
        notes = entity.get("notes", {})
        return {
            "event_id": event_id,
            "event_type": event_type,
            "user_id": notes.get("user_id"),
            "plan_code": notes.get("plan_code"),
            "billing_period": notes.get("billing_period", "monthly"),
            "provider_subscription_id": subscription_entity.get("id") or payment_entity.get("subscription_id"),
            "status": {"subscription.activated": "active", "subscription.charged": "active", "subscription.completed": "expired", "subscription.cancelled": "cancelled", "subscription.paused": "paused", "subscription.halted": "past_due", "payment.failed": "past_due"}.get(event_type, event_type),
            "current_period_start": subscription_entity.get("current_start"),
            "current_period_end": subscription_entity.get("current_end"),
            "raw": data,
        }
