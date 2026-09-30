"""Synchronize production plan entitlements and seed missing plans.

Revision ID: 002_plan_entitlements
Revises: 001_initial_schema
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "002_plan_entitlements"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    plans = sa.table(
        "plans",
        sa.column("id", sa.String()),
        sa.column("code", sa.String()),
        sa.column("name", sa.String()),
        sa.column("description", sa.String()),
        sa.column("monthly_price_inr", sa.Integer()),
        sa.column("yearly_price_inr", sa.Integer()),
        sa.column("monthly_price_usd", sa.Integer()),
        sa.column("yearly_price_usd", sa.Integer()),
        sa.column("regional_pricing", sa.JSON()),
        sa.column("daily_response_limit", sa.Integer()),
        sa.column("daily_image_limit", sa.Integer()),
        sa.column("monthly_name_change_limit", sa.Integer()),
        sa.column("monthly_appearance_change_limit", sa.Integer()),
        sa.column("custom_appearance_allowed", sa.Boolean()),
        sa.column("allowed_modes", sa.JSON()),
        sa.column("deep_research_allowed", sa.Boolean()),
        sa.column("is_active", sa.Boolean()),
    )
    conn = op.get_bind()

    defaults = [
        {
            "id": "plan_free", "code": "FREE", "name": "Free",
            "description": "Essential AI sidekick companion for casual everyday use.",
            "monthly_price_inr": 0, "yearly_price_inr": 0,
            "monthly_price_usd": 0, "yearly_price_usd": 0,
            "regional_pricing": {}, "daily_response_limit": 30, "daily_image_limit": 3,
            "monthly_name_change_limit": 1, "monthly_appearance_change_limit": 2,
            "custom_appearance_allowed": False,
            "allowed_modes": ["Brain", "Chill", "Focus"], "deep_research_allowed": False,
            "is_active": True,
        },
        {
            "id": "plan_pro", "code": "PRO", "name": "Pro",
            "description": "Supercharged personal companion with expanded modes and creative capabilities.",
            "monthly_price_inr": 39900, "yearly_price_inr": 418800,
            "monthly_price_usd": 499, "yearly_price_usd": 4999,
            "regional_pricing": {}, "daily_response_limit": 150, "daily_image_limit": 15,
            "monthly_name_change_limit": 5, "monthly_appearance_change_limit": 10,
            "custom_appearance_allowed": True,
            "allowed_modes": ["Brain", "Chill", "Chaos", "Create", "Focus"], "deep_research_allowed": True,
            "is_active": True,
        },
        {
            "id": "plan_plus", "code": "PLUS", "name": "Plus",
            "description": "Ultimate intelligence tier with maximum quota, roast mode, and full customization.",
            "monthly_price_inr": 99900, "yearly_price_inr": 1078800,
            "monthly_price_usd": 1299, "yearly_price_usd": 12999,
            "regional_pricing": {}, "daily_response_limit": -1, "daily_image_limit": 35,
            "monthly_name_change_limit": -1, "monthly_appearance_change_limit": -1,
            "custom_appearance_allowed": True,
            "allowed_modes": ["Brain", "Chill", "Chaos", "Roast", "Create", "Focus"], "deep_research_allowed": True,
            "is_active": True,
        },
    ]

    existing = {row[0] for row in conn.execute(sa.select(plans.c.code)).fetchall()}
    missing = [p for p in defaults if p["code"] not in existing]
    if missing:
        conn.execute(plans.insert(), missing)

    for p in defaults:
        conn.execute(
            plans.update().where(plans.c.code == p["code"]).values(
                name=p["name"],
                description=p["description"],
                daily_response_limit=p["daily_response_limit"],
                monthly_name_change_limit=p["monthly_name_change_limit"],
                monthly_appearance_change_limit=p["monthly_appearance_change_limit"],
                custom_appearance_allowed=p["custom_appearance_allowed"],
                allowed_modes=p["allowed_modes"],
                deep_research_allowed=p["deep_research_allowed"],
                is_active=True,
            )
        )


def downgrade() -> None:
    # Entitlement synchronization is intentionally not reversed: rolling back
    # code should not silently restore obsolete production limits.
    pass
