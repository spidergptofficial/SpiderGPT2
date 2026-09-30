"""SpiderGPT Unified Payment Provider Base Interface.

Both Razorpay and Stripe implement this interface for seamless provider-independent billing.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class PaymentProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Returns 'razorpay' or 'stripe'."""
        pass

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """Returns True if live credentials exist for this provider."""
        pass

    @abstractmethod
    async def create_checkout(
        self,
        user_id: str,
        email: str,
        plan_code: str,
        billing_period: str,
        amount: int,
        currency: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Creates an order / checkout session.

        Returns:
            {
                "provider": str,
                "order_id": str,
                "amount": int,
                "currency": str,
                "key_id": Optional[str],        # public key for frontend checkout
                "client_secret": Optional[str], # client secret if Stripe
                "checkout_url": Optional[str],
                "metadata": dict
            }
        """
        pass

    @abstractmethod
    async def verify_payment(
        self,
        order_id: str,
        payment_id: Optional[str] = None,
        signature: Optional[str] = None,
    ) -> bool:
        """Verifies payment transaction authenticity."""
        pass

    @abstractmethod
    async def get_checkout_details(self, checkout_id: str) -> Dict[str, Any]:
        """Returns provider-authoritative checkout/subscription state and period metadata."""
        pass

    @abstractmethod
    async def cancel_subscription(self, provider_subscription_id: str) -> bool:
        """Cancels a recurring subscription."""
        pass

    @abstractmethod
    def verify_webhook_signature(self, payload_body: bytes, headers: Dict[str, str]) -> bool:
        """Cryptographically verifies webhook payload authenticity."""
        pass

    @abstractmethod
    def parse_webhook_event(self, payload_body: bytes, headers: Dict[str, str]) -> Dict[str, Any]:
        """Extracts normalized event data:

        {
            "event_id": str,
            "event_type": str,
            "user_id": Optional[str],
            "plan_code": Optional[str],
            "billing_period": Optional[str],
            "provider_subscription_id": Optional[str],
            "status": str,
            "raw": dict
        }
        """
        pass
