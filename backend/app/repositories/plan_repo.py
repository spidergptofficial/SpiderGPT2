"""SpiderGPT Plan Repository & Seeding Engine."""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.plan import Plan, PlanFeature


DEFAULT_PLANS = [
    {
        "id": "plan_free",
        "code": "FREE",
        "name": "Free",
        "description": "Essential AI sidekick companion for casual everyday use.",
        "monthly_price_inr": 0,
        "yearly_price_inr": 0,
        "monthly_price_usd": 0,
        "yearly_price_usd": 0,
        "regional_pricing": {},
        "daily_response_limit": 30,
        "daily_image_limit": 3,
        "monthly_name_change_limit": 1,
        "monthly_appearance_change_limit": 2,
        "custom_appearance_allowed": False,
        "allowed_modes": ["Brain", "Chill", "Focus"],
        "deep_research_allowed": False,
    },
    {
        "id": "plan_pro",
        "code": "PRO",
        "name": "Pro",
        "description": "Supercharged personal companion with expanded modes and creative capabilities.",
        "monthly_price_inr": 39900,  # ₹399.00 in paise
        "yearly_price_inr": 418800,  # ₹4,188.00 annually (₹349/mo equivalent)
        "monthly_price_usd": 499,    # $4.99
        "yearly_price_usd": 4999,    # $49.99
        "regional_pricing": {},
        "daily_response_limit": 150,
        "daily_image_limit": 15,
        "monthly_name_change_limit": 5,
        "monthly_appearance_change_limit": 10,
        "custom_appearance_allowed": True,
        "allowed_modes": ["Brain", "Chill", "Chaos", "Create", "Focus"],
        "deep_research_allowed": True,
    },
    {
        "id": "plan_plus",
        "code": "PLUS",
        "name": "Plus",
        "description": "Ultimate intelligence tier with maximum quota, roast mode, and full customization.",
        "monthly_price_inr": 99900,   # ₹999.00 in paise
        "yearly_price_inr": 1078800,  # ₹10,788.00 annually (₹899/mo equivalent)
        "monthly_price_usd": 1299,    # $12.99
        "yearly_price_usd": 12999,    # $129.99
        "regional_pricing": {},
        "daily_response_limit": -1,
        "daily_image_limit": 35,
        "monthly_name_change_limit": -1,       # -1 indicates Unlimited
        "monthly_appearance_change_limit": -1,  # -1 indicates Unlimited
        "custom_appearance_allowed": True,
        "allowed_modes": ["Brain", "Chill", "Chaos", "Roast", "Create", "Focus"],
        "deep_research_allowed": True,
    },
]


class PlanRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_active(self) -> List[Plan]:
        stmt = select(Plan).where(Plan.is_active == True)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_code(self, code: str) -> Optional[Plan]:
        stmt = select(Plan).where(Plan.code == code.upper())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, plan_id: str) -> Optional[Plan]:
        stmt = select(Plan).where(Plan.id == plan_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def seed_plans_if_empty(self) -> None:
        """Seeds default database-driven plans if they do not exist yet."""
        for p_data in DEFAULT_PLANS:
            stmt = select(Plan).where(Plan.code == p_data["code"])
            res = await self.db.execute(stmt)
            existing = res.scalar_one_or_none()
            if not existing:
                plan = Plan(
                    id=p_data["id"],
                    code=p_data["code"],
                    name=p_data["name"],
                    description=p_data["description"],
                    monthly_price_inr=p_data["monthly_price_inr"],
                    yearly_price_inr=p_data["yearly_price_inr"],
                    monthly_price_usd=p_data["monthly_price_usd"],
                    yearly_price_usd=p_data["yearly_price_usd"],
                    regional_pricing=p_data["regional_pricing"],
                    daily_response_limit=p_data["daily_response_limit"],
                    daily_image_limit=p_data["daily_image_limit"],
                    monthly_name_change_limit=p_data["monthly_name_change_limit"],
                    monthly_appearance_change_limit=p_data["monthly_appearance_change_limit"],
                    custom_appearance_allowed=p_data["custom_appearance_allowed"],
                    allowed_modes=p_data["allowed_modes"],
                    deep_research_allowed=p_data["deep_research_allowed"],
                    is_active=True,
                )
                self.db.add(plan)
        await self.db.flush()
