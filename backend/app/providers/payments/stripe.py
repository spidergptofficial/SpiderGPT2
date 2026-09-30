"""SpiderGPT Stripe Payment Provider Implementation."""
import json
import uuid
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

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

    async def create_checkout(
        self,
        user_id: str,
        email: str,
        plan_code: str,
        billing_period: str,
        amount: int,
        currency: str = "USD",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        meta = {
            "user_id": user_id,
            "email": email,
            "plan_code": plan_code,
            "billing_period": billing_period,
        }
        if metadata:
            meta.update({k: str(v) for k, v in metadata.items()})

        if not self.is_configured:
            # Simulated session for testing
            simulated_id = f"cs_sim_test_{uuid.uuid4().hex[:12]}"
            return {
                "provider": self.provider_name,
                "order_id": simulated_id,
                "amount": amount,
                "currency": currency.lower(),
                "key_id": self.publishable_key or "pk_test_simulated_key",
                "client_secret": f"pi_sim_secret_{uuid.uuid4().hex[:12]}",
                "checkout_url": f"https://checkout.stripe.com/c/pay/{simulated_id}",
                "metadata": meta,
            }

        url = f"{self.base_url}/checkout/sessions"
        form_data = [
            ("payment_method_types[]", "card"),
            ("mode", "payment"),
            ("success_url", f"{settings.FRONTEND_BASE_URL}/payment/success?session_id={{CHECKOUT_SESSION_ID}}"),
            ("cancel_url", f"{settings.FRONTEND_BASE_URL}/payment/cancel"),
            ("customer_email", email),
            ("line_items[0][price_data][currency]", currency.lower()),
            ("line_items[0][price_data][unit_amount]", str(amount)),
            ("line_items[0][price_data][product_data][name]", f"SpiderGPT {plan_code.title()} ({billing_period})"),
            ("line_items[0][quantity]", "1"),
        ]
        for k, v in meta.items():
            form_data.append((f"metadata[{k}]", str(v)))

        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                resp = await client.post(url, headers=self._get_headers(), data=form_data)
                if resp.status_code not in [200, 201]:
                    logger.error("Stripe session creation error (%d): %s", resp.status_code, resp.text[:200])
                    raise PaymentFailedException("Failed to initiate Stripe checkout session.")
                data = resp.json()
                return {
                    "provider": self.provider_name,
                    "order_id": data.get("id"),
                    "amount": amount,
                    "currency": currency.lower(),
                    "key_id": self.publishable_key,
                    "client_secret": data.get("client_secret"),
                    "checkout_url": data.get("url"),
                    "metadata": meta,
                }
            except httpx.RequestError as e:
                logger.error("Stripe network error: %s", str(e))
                raise PaymentFailedException("Could not connect to Stripe payment gateway.")

    async def verify_payment(
        self,
        order_id: str,
        payment_id: Optional[str] = None,
        signature: Optional[str] = None,
    ) -> bool:
        if not self.is_configured:
            return True if order_id.startswith("cs_sim_") or signature == "test_valid_sig" else False

        url = f"{self.base_url}/checkout/sessions/{order_id}"
        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                resp = await client.get(url, headers=self._get_headers())
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("payment_status") == "paid"
                return False
            except Exception as e:
                logger.error("Stripe session retrieval error: %s", str(e))
                return False

    async def cancel_subscription(self, provider_subscription_id: str) -> bool:
        if not self.is_configured:
            return True
        url = f"{self.base_url}/subscriptions/{provider_subscription_id}"
        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                resp = await client.delete(url, headers=self._get_headers())
                return resp.status_code in [200, 204]
            except Exception as e:
                logger.error("Stripe cancel subscription error: %s", str(e))
                return False

    def verify_webhook_signature(self, payload_body: bytes, headers: Dict[str, str]) -> bool:
        if not self.webhook_secret:
            if settings.ENVIRONMENT == "production":
                return False
            return True
        sig_header = headers.get("Stripe-Signature") or headers.get("stripe-signature", "")
        return verify_stripe_signature(payload_body, sig_header, self.webhook_secret)

    def parse_webhook_event(self, payload_body: bytes, headers: Dict[str, str]) -> Dict[str, Any]:
        data = json.loads(payload_body.decode("utf-8"))
        event_id = data.get("id", str(uuid.uuid4()))
        event_type = data.get("type", "")

        obj = data.get("data", {}).get("object", {})
        metadata = obj.get("metadata", {})
        user_id = metadata.get("user_id")
        plan_code = metadata.get("plan_code")
        billing_period = metadata.get("billing_period", "monthly")

        return {
            "event_id": event_id,
            "event_type": event_type,
            "user_id": user_id,
            "plan_code": plan_code,
            "billing_period": billing_period,
            "provider_subscription_id": obj.get("subscription") or obj.get("id"),
            "status": "active" if event_type in ["checkout.session.completed", "invoice.payment_succeeded"] else event_type,
            "raw": data,
        }
