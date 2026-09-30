"""SpiderGPT Plan & Entitlement Service.

Determines the effective subscription and plan limits for an authenticated user.
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.plan import Plan
from backend.app.models.subscription import Subscription
from backend.app.models.user import User
from backend.app.repositories.plan_repo import PlanRepository
from backend.app.repositories.subscription_repo import SubscriptionRepository


class PlanService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.plan_repo = PlanRepository(db)
        self.sub_repo = SubscriptionRepository(db)

    async def get_user_effective_plan(self, user: User) -> Plan:
        """Determines the user's effective plan based on active subscriptions or default FREE."""
        # Check active subscription
        sub = await self.sub_repo.get_active_by_user_id(user.id)
        if sub and sub.plan:
            return sub.plan

        # Default to FREE plan
        free_plan = await self.plan_repo.get_by_code("FREE")
        if not free_plan:
            # Seed plans if not seeded yet
            await self.plan_repo.seed_plans_if_empty()
            free_plan = await self.plan_repo.get_by_code("FREE")

        return free_plan

    async def get_user_subscription(self, user: User) -> Optional[Subscription]:
        return await self.sub_repo.get_active_by_user_id(user.id)
