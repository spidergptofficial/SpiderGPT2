"""SpiderGPT Payment Provider Factory & Availability Checker."""
from typing import Dict, Any, Optional
from backend.app.core.config import settings
from backend.app.core.exceptions import ProviderUnavailableException
from backend.app.providers.payments.base import PaymentProvider
from backend.app.providers.payments.razorpay import RazorpayPaymentProvider
from backend.app.providers.payments.stripe import StripePaymentProvider


class PaymentFactory:
    _razorpay = None
    _stripe = None

    @classmethod
    def get_razorpay(cls) -> RazorpayPaymentProvider:
        if cls._razorpay is None:
            cls._razorpay = RazorpayPaymentProvider()
        return cls._razorpay

    @classmethod
    def get_stripe(cls) -> StripePaymentProvider:
        if cls._stripe is None:
            cls._stripe = StripePaymentProvider()
        return cls._stripe

    @classmethod
    def get_availability(cls) -> Dict[str, bool]:
        """Returns availability status for configured payment gateways."""
        rzp = cls.get_razorpay().is_configured
        strp = cls.get_stripe().is_configured
        return {
            "razorpay": rzp,
            "stripe": strp,
        }

    @classmethod
    def resolve_provider(
        cls,
        requested_provider: Optional[str] = None,
        currency: Optional[str] = None,
    ) -> PaymentProvider:
        """Determines best payment provider based on explicit request or currency routing."""
        rzp = cls.get_razorpay()
        strp = cls.get_stripe()

        req = (requested_provider or "").lower().strip()
        curr = (currency or settings.DEFAULT_CURRENCY or "INR").upper().strip()

        is_dev = settings.DEBUG or settings.ENVIRONMENT != "production"

        if req == "razorpay":
            if not rzp.is_configured and not is_dev:
                raise ProviderUnavailableException("payment", "razorpay")
            return rzp
        elif req == "stripe":
            if not strp.is_configured and not is_dev:
                raise ProviderUnavailableException("payment", "stripe")
            return strp

        # Currency-based smart routing
        if curr == "INR":
            if rzp.is_configured or is_dev:
                return rzp
            elif strp.is_configured:
                return strp
        else:
            if strp.is_configured or is_dev:
                return strp
            elif rzp.is_configured:
                return rzp

        # Fallback
        if rzp.is_configured:
            return rzp
        if strp.is_configured:
            return strp

        return rzp
