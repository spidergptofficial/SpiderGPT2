"""SpiderGPT User Subscription Model."""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base
from backend.app.utils.id_generator import generate_id


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: generate_id("sub"))
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    plan_id: Mapped[str] = mapped_column(String(64), ForeignKey("plans.id"), index=True, nullable=False)

    provider: Mapped[str] = mapped_column(String(32), default="manual")  # razorpay, stripe, manual
    provider_customer_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    provider_subscription_id: Mapped[Optional[str]] = mapped_column(String(128), unique=True, index=True, nullable=True)

    billing_period: Mapped[str] = mapped_column(String(16), default="monthly")  # monthly, yearly
    currency: Mapped[str] = mapped_column(String(8), default="INR")
    amount: Mapped[int] = mapped_column(Integer, default=0)

    # Status: trialing, active, past_due, paused, cancelled, expired, incomplete
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)

    current_period_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    current_period_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = relationship("User", back_populates="subscriptions")
    plan = relationship("Plan", back_populates="subscriptions")
