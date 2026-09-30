"""SpiderGPT Payment Orders & Webhook Idempotency Models."""
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import DateTime, ForeignKey, Integer, String, JSON
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.database import Base
from backend.app.utils.id_generator import generate_id


class PaymentOrder(Base):
    __tablename__ = "payment_orders"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: generate_id("ord"))
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    plan_id: Mapped[str] = mapped_column(String(64), ForeignKey("plans.id"), index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)  # razorpay, stripe
    order_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="INR")
    status: Mapped[str] = mapped_column(String(32), default="created")  # created, paid, failed, refunded
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class ProcessedWebhookEvent(Base):
    """Enforces strict idempotency for Stripe and Razorpay webhook events."""
    __tablename__ = "processed_webhook_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: generate_id("evt"))
    event_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    payload_summary: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
