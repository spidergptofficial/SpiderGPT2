"""SpiderGPT Stripe payment provider."""
import json
from typing import Dict, Any, Optional
import httpx

from backend.app.core.config import settings
from backend.app.core.exceptions import PaymentFailedException
from backend.app.core.logging import logger
from backend.app.providers.payments.base import PaymentProvider
from backend.app.utils.security import verify_stripe_signature


class StripePaymentProvider(PaymentProvider):
    def __init__(self):
        self.secret_key = settings.STRIPE_SECRET_KEY
        self.publishable_key = settings.STRIPE_PUBLISHABLE_KEY
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        self.base_url = "https://api.stripe.com/v1"

    @property
    def provider_name(self) -> str:
        return "stripe"

    @property
    def is_configured(self) -> bool:
        return bool(self.secret_key and self.publishable_key)

    def _require_configured(self) -> None:
        if not self.is_configured:
            raise PaymentFailedException("Stripe is not configured.")

    def _get_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.secret_key}", "Content-Type": "application/x-www-form-urlencoded"}

    async def create_checkout(self, user_id: str, email: str, plan_code: str, billing_period: str,
                              amount: int, currency: str = "USD",
                              metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self._require_configured()
        meta = {"user_id": user_id, "email": email, "plan_code": plan_code, "billing_period": billing_period}
        if metadata:
            meta.update({k: str(v) for k, v in metadata.items()})
        interval = "year" if billing_period == "yearly" else "month"
        form_data = [
            ("payment_method_types[]", "card"), ("mode", "subscription"),
            ("success_url", f"{settings.FRONTEND_BASE_URL}/#/payment-success?session_id={{CHECKOUT_SESSION_ID}}"),
            ("cancel_url", f"{settings.FRONTEND_BASE_URL}/#/pricing"),
            ("customer_email", email),
            ("line_items[0][price_data][currency]", currency.lower()),
            ("line_items[0][price_data][unit_amount]", str(amount)),
            ("line_items[0][price_data][product_data][name]", f"SpiderGPT {plan_code.title()} ({billing_period})"),
            ("line_items[0][price_data][recurring][interval]", interval),
            ("line_items[0][quantity]", "1"),
        ]
        for k, v in meta.items():
            form_data.append((f"metadata[{k}]", str(v)))
        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                resp = await client.post(f"{self.base_url}/checkout/sessions", headers=self._get_headers(), data=form_data)
                if resp.status_code not in (200, 201):
                    logger.error("Stripe checkout creation error (%d): %s", resp.status_code, resp.text[:200])
                    raise PaymentFailedException("Failed to initiate Stripe checkout session.")
                data = resp.json()
                return {"provider": self.provider_name, "order_id": data.get("id"), "amount": amount,
                        "currency": currency.lower(), "key_id": self.publishable_key,
                        "client_secret": data.get("client_secret"), "checkout_url": data.get("url"),
                        "provider_subscription_id": data.get("subscription"), "metadata": meta}
            except httpx.RequestError:
                logger.exception("Stripe network request error")
                raise PaymentFailedException("Could not connect to Stripe payment gateway.")

    async def get_checkout_details(self, checkout_id: str) -> Dict[str, Any]:
        self._require_configured()
        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                resp = await client.get(f"{self.base_url}/checkout/sessions/{checkout_id}", headers=self._get_headers())
                if resp.status_code != 200:
                    return {}
                data = resp.json()
                return {
                    "paid": data.get("payment_status") == "paid",
                    "mode": data.get("mode"),
                    "provider_subscription_id": data.get("subscription"),
                    "customer_id": data.get("customer"),
                    "current_period_start": None,
                    "current_period_end": None,
                }
            except httpx.RequestError:
                logger.exception("Stripe session retrieval error")
                return {}

    async def verify_payment(self, order_id: str, payment_id: Optional[str] = None,
                             signature: Optional[str] = None) -> bool:
        details = await self.get_checkout_details(order_id)
        return bool(details.get("paid") and details.get("mode") == "subscription" and details.get("provider_subscription_id"))

    async def cancel_subscription(self, provider_subscription_id: str, cancel_immediately: bool = False) -> bool:
        self._require_configured()
        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                if cancel_immediately:
                    resp = await client.delete(f"{self.base_url}/subscriptions/{provider_subscription_id}", headers=self._get_headers())
                else:
                    resp = await client.post(
                        f"{self.base_url}/subscriptions/{provider_subscription_id}",
                        headers=self._get_headers(),
                        data={"cancel_at_period_end": "true"},
                    )
                return resp.status_code in (200, 204)
            except httpx.RequestError:
                logger.exception("Stripe cancel subscription error")
                return False

    def verify_webhook_signature(self, payload_body: bytes, headers: Dict[str, str]) -> bool:
        if not self.webhook_secret:
            return False
        sig_header = headers.get("Stripe-Signature") or headers.get("stripe-signature", "")
        return verify_stripe_signature(payload_body, sig_header, self.webhook_secret)

    def parse_webhook_event(self, payload_body: bytes, headers: Dict[str, str]) -> Dict[str, Any]:
        data = json.loads(payload_body.decode("utf-8"))
        event_id = data.get("id")
        if not event_id:
            raise PaymentFailedException("Stripe webhook event ID is missing.")
        event_type = data.get("type", "")
        obj = data.get("data", {}).get("object", {})
        metadata = obj.get("metadata", {})
        subscription_id = obj.get("subscription") or (obj.get("id") if event_type.startswith("customer.subscription.") else None)
        status_map = {
            "checkout.session.completed": "active",
            "invoice.payment_succeeded": "active",
            "invoice.payment_failed": "past_due",
            "customer.subscription.deleted": "cancelled",
            "customer.subscription.paused": "paused",
        }
        normalized_status = status_map.get(event_type)
        if event_type == "customer.subscription.updated":
            normalized_status = {
                "active": "active", "trialing": "trialing", "past_due": "past_due",
                "paused": "paused", "canceled": "cancelled", "incomplete": "incomplete",
                "incomplete_expired": "expired", "unpaid": "past_due",
            }.get(obj.get("status"), "past_due")
        return {
            "event_id": event_id,
            "event_type": event_type,
            "user_id": metadata.get("user_id"),
            "plan_code": metadata.get("plan_code"),
            "billing_period": metadata.get("billing_period", "monthly"),
            "provider_subscription_id": subscription_id,
            "provider_customer_id": obj.get("customer"),
            "current_period_start": obj.get("current_period_start"),
            "current_period_end": obj.get("current_period_end"),
            "status": normalized_status or event_type,
            "raw": data,
        }
