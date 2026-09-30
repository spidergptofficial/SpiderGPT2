"""SpiderGPT Payment Webhook Ingestion Routes."""
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.services.payment_service import PaymentService

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/razorpay", status_code=status.HTTP_200_OK, summary="Razorpay webhook listener")
async def razorpay_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Processes verified Razorpay webhook events with strict idempotency."""
    body_bytes = await request.body()
    headers_dict = dict(request.headers)
    service = PaymentService(db)
    return await service.handle_webhook("razorpay", body_bytes, headers_dict)


@router.post("/stripe", status_code=status.HTTP_200_OK, summary="Stripe webhook listener")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Processes verified Stripe webhook events with strict idempotency."""
    body_bytes = await request.body()
    headers_dict = dict(request.headers)
    service = PaymentService(db)
    return await service.handle_webhook("stripe", body_bytes, headers_dict)
