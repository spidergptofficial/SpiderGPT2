"""SpiderGPT Personal Spider Model.

Enforces ONE Spider per user at the database level with a unique constraint on user_id.
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import DateTime, ForeignKey, String, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base
from backend.app.utils.id_generator import generate_id


class Spider(Base):
    __tablename__ = "spiders"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: generate_id("spd"))
    # Database level unique constraint enforces exactly one Spider per user!
    user_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    spider_name: Mapped[str] = mapped_column(String(64), default="Spider")
    personality_mode: Mapped[str] = mapped_column(String(32), default="Brain")
    appearance_id: Mapped[str] = mapped_column(String(64), default="preset_default")
    custom_appearance_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = relationship("User", back_populates="spider")
    appearances = relationship("SpiderAppearance", back_populates="spider", cascade="all, delete-orphan")


class SpiderAppearance(Base):
    __tablename__ = "spider_appearances"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: generate_id("appr"))
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    spider_id: Mapped[str] = mapped_column(String(64), ForeignKey("spiders.id", ondelete="CASCADE"), index=True, nullable=False)
    appearance_type: Mapped[str] = mapped_column(String(16), default="PRESET")  # PRESET or CUSTOM
    preset_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    spider = relationship("Spider", back_populates="appearances")
