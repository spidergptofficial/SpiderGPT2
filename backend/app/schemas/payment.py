"""SpiderGPT Payment Schemas."""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class PaymentProvidersAvailabilityResponse(BaseModel):
    razorpay: bool
    stripe: bool
    default_provider: str
    preferred_currency: str


class CreateCheckoutSessionRequest(BaseModel):
    plan_code: str = Field(..., description="PRO or PLUS")
    billing_period: str = Field(default="monthly", description="monthly or yearly")
    provider: Optional[str] = Field(None, description="Preferred provider: razorpay or stripe. If omitted, chosen based on currency/config.")
    currency: Optional[str] = Field(None, description="INR, USD, EUR, etc.")


class CheckoutSessionResponse(BaseModel):
    provider: str
    order_id: str
    amount: int
    currency: str
    key_id: Optional[str] = None  # Razorpay Key ID or Stripe Publishable Key (public keys only!)
    client_secret: Optional[str] = None  # Stripe client secret or payment session data
    checkout_url: Optional[str] = None
    metadata: Dict[str, Any] = {}


class VerifyPaymentRequest(BaseModel):
    provider: str = Field(..., description="razorpay or stripe")
    order_id: str
    payment_id: Optional[str] = None
    signature: Optional[str] = None


class VerifyPaymentResponse(BaseModel):
    success: bool
    message: str
    subscription_id: Optional[str] = None
    plan: str
    status: str
