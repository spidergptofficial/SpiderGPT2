"""SpiderGPT Payment Checkout & Verification Routes."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.security import get_current_user_from_token
from backend.app.models.user import User
from backend.app.schemas.payment import (
    PaymentProvidersAvailabilityResponse,
    CreateCheckoutSessionRequest,
    CheckoutSessionResponse,
    VerifyPaymentRequest,
    VerifyPaymentResponse,
)
from backend.app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.get("/providers", response_model=PaymentProvidersAvailabilityResponse, summary="Check configured payment gateways availability")
async def get_providers_availability(
    db: AsyncSession = Depends(get_db),
):
    """Allows frontend to detect available checkout providers (Razorpay, Stripe) and preferred currency."""
    service = PaymentService(db)
    return await service.get_providers_status()


@router.post("/checkout", response_model=CheckoutSessionResponse, status_code=status.HTTP_201_CREATED, summary="Create payment checkout session")
async def create_checkout(
    payload: CreateCheckoutSessionRequest,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    """Initializes checkout session on the appropriate provider (Razorpay/Stripe) without storing sensitive credentials."""
    service = PaymentService(db)
    return await service.create_checkout_session(current_user, payload)


@router.post("/verify", response_model=VerifyPaymentResponse, summary="Verify payment signature and activate subscription")
async def verify_payment(
    payload: VerifyPaymentRequest,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    """Validates payment completion signature and activates plan."""
    service = PaymentService(db)
    return await service.verify_payment(current_user, payload)
