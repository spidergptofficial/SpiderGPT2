"""SpiderGPT Database-Driven Subscription Plans & Features Model."""
from datetime import datetime, timezone
from typing import Dict, Any, List
from sqlalchemy import Boolean, DateTime, Integer, String, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # plan_free, plan_pro, plan_plus
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)  # FREE, PRO, PLUS
    name: Mapped[str] = mapped_column(String(64))  # Free, Pro, Plus
    description: Mapped[str] = mapped_column(String(255))

    # Pricing - Domestic (INR in paise for payment processors)
    monthly_price_inr: Mapped[int] = mapped_column(Integer, default=0)
    yearly_price_inr: Mapped[int] = mapped_column(Integer, default=0)

    # Pricing - International (USD in cents)
    monthly_price_usd: Mapped[int] = mapped_column(Integer, default=0)
    yearly_price_usd: Mapped[int] = mapped_column(Integer, default=0)

    # Regional currency overrides dictionary e.g. {"EUR": {"monthly": 499, "yearly": 4999}}
    regional_pricing: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    # Quota Limits (Database-Driven, not scattered in code!)
    daily_response_limit: Mapped[int] = mapped_column(Integer, default=30)
    daily_image_limit: Mapped[int] = mapped_column(Integer, default=3)
    monthly_name_change_limit: Mapped[int] = mapped_column(Integer, default=1)  # -1 for unlimited
    monthly_appearance_change_limit: Mapped[int] = mapped_column(Integer, default=2)  # -1 for unlimited
    custom_appearance_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    allowed_modes: Mapped[List[str]] = mapped_column(JSON, default=list)
    deep_research_allowed: Mapped[bool] = mapped_column(Boolean, default=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    subscriptions = relationship("Subscription", back_populates="plan")
    features = relationship("PlanFeature", back_populates="plan", cascade="all, delete-orphan")


class PlanFeature(Base):
    __tablename__ = "plan_features"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    plan_id: Mapped[str] = mapped_column(String(64), ForeignKey("plans.id", ondelete="CASCADE"), index=True, nullable=False)
    feature_key: Mapped[str] = mapped_column(String(64))
    feature_value: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(String(255))

    plan = relationship("Plan", back_populates="features")
