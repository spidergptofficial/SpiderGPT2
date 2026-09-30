"""SpiderGPT Razorpay Payment Provider Implementation."""
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
        auth_str = f"{self.key_id}:{self.key_secret}"
        encoded = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
        return {"Authorization": f"Basic {encoded}"}

    async def create_checkout(
        self,
        user_id: str,
        email: str,
        plan_code: str,
        billing_period: str,
        amount: int,
        currency: str = "INR",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        notes = {
            "user_id": user_id,
            "email": email,
            "plan_code": plan_code,
            "billing_period": billing_period,
        }
        if metadata:
            notes.update({k: str(v) for k, v in metadata.items()})

        if not self.is_configured:
            # Simulated order for development/testing
            simulated_order_id = f"order_sim_rzp_{uuid.uuid4().hex[:12]}"
            return {
                "provider": self.provider_name,
                "order_id": simulated_order_id,
                "amount": amount,
                "currency": currency,
                "key_id": "rzp_test_simulated_key",
                "client_secret": None,
                "checkout_url": None,
                "metadata": notes,
            }

        url = f"{self.base_url}/orders"
        payload = {
            "amount": amount,
            "currency": currency,
            "receipt": f"rcpt_{uuid.uuid4().hex[:10]}",
            "notes": notes,
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                resp = await client.post(url, headers=self._get_auth_header(), json=payload)
                if resp.status_code not in [200, 201]:
                    logger.error("Razorpay order creation error (%d): %s", resp.status_code, resp.text[:200])
                    raise PaymentFailedException("Failed to initiate Razorpay checkout order.")
                data = resp.json()
                return {
                    "provider": self.provider_name,
                    "order_id": data.get("id"),
                    "amount": data.get("amount"),
                    "currency": data.get("currency"),
                    "key_id": self.key_id,
                    "client_secret": None,
                    "checkout_url": None,
                    "metadata": notes,
                }
            except httpx.RequestError as e:
                logger.error("Razorpay network request error: %s", str(e))
                raise PaymentFailedException("Could not connect to payment gateway.")

    async def verify_payment(
        self,
        order_id: str,
        payment_id: Optional[str] = None,
        signature: Optional[str] = None,
    ) -> bool:
        if not self.is_configured:
            # In test/dev simulation mode
            return True if order_id.startswith("order_sim_rzp_") or signature == "test_valid_sig" else False

        if not payment_id or not signature or not self.key_secret:
            return False

        payload_to_verify = f"{order_id}|{payment_id}".encode("utf-8")
        return verify_razorpay_signature(payload_to_verify, signature, self.key_secret)

    async def cancel_subscription(self, provider_subscription_id: str) -> bool:
        if not self.is_configured:
            return True
        url = f"{self.base_url}/subscriptions/{provider_subscription_id}/cancel"
        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                resp = await client.post(url, headers=self._get_auth_header(), json={"cancel_at_cycle_end": 1})
                return resp.status_code in [200, 204]
            except Exception as e:
                logger.error("Razorpay cancel subscription error: %s", str(e))
                return False

    def verify_webhook_signature(self, payload_body: bytes, headers: Dict[str, str]) -> bool:
        if not self.webhook_secret:
            # If webhook secret is not set, reject webhooks in production
            if settings.ENVIRONMENT == "production":
                return False
            return True
        sig = headers.get("X-Razorpay-Signature") or headers.get("x-razorpay-signature", "")
        return verify_razorpay_signature(payload_body, sig, self.webhook_secret)

    def parse_webhook_event(self, payload_body: bytes, headers: Dict[str, str]) -> Dict[str, Any]:
        data = json.loads(payload_body.decode("utf-8"))
        event_type = data.get("event", "")
        event_id = data.get("event_id") or data.get("payload", {}).get("payment", {}).get("entity", {}).get("id") or str(uuid.uuid4())

        payment_entity = data.get("payload", {}).get("payment", {}).get("entity", {})
        notes = payment_entity.get("notes", {})
        user_id = notes.get("user_id")
        plan_code = notes.get("plan_code")
        billing_period = notes.get("billing_period", "monthly")

        return {
            "event_id": event_id,
            "event_type": event_type,
            "user_id": user_id,
            "plan_code": plan_code,
            "billing_period": billing_period,
            "provider_subscription_id": payment_entity.get("id"),
            "status": "active" if event_type in ["payment.captured", "subscription.activated", "order.paid"] else event_type,
            "raw": data,
        }
