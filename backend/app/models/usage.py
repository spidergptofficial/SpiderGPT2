"""SpiderGPT Usage Tracking Model.

Tracks AI queries, image creations, customization events server-side with atomic accuracy.
"""
from datetime import datetime, timezone
from typing import Dict, Any
from sqlalchemy import DateTime, ForeignKey, Integer, String, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.database import Base
from backend.app.utils.id_generator import generate_id


class UsageRecord(Base):
    __tablename__ = "usage_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: generate_id("usg"))
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    # Types: ai_response, image_generation, spider_name_change, appearance_change, custom_appearance_creation, deep_research, web_search
    usage_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    # Date string: YYYY-MM-DD for daily limits or YYYY-MM for monthly limits
    date: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("ix_usage_user_type_date", "user_id", "usage_type", "date"),
    )
