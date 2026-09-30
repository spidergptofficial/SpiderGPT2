"""SpiderGPT Subscription Repository."""
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.subscription import Subscription


class SubscriptionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active_by_user_id(self, user_id: str) -> Optional[Subscription]:
        """Returns the user's currently active or trialing subscription, if any."""
        stmt = (
            select(Subscription)
            .options(selectinload(Subscription.plan))
            .where(
                Subscription.user_id == user_id,
                Subscription.status.in_(["active", "trialing"]),
            )
            .order_by(Subscription.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_by_provider_sub_id(self, provider_sub_id: str) -> Optional[Subscription]:
        stmt = (
            select(Subscription)
            .options(selectinload(Subscription.plan))
            .where(Subscription.provider_subscription_id == provider_sub_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, sub: Subscription) -> Subscription:
        self.db.add(sub)
        await self.db.flush()
        return sub

    async def list_user_history(self, user_id: str) -> List[Subscription]:
        stmt = (
            select(Subscription)
            .options(selectinload(Subscription.plan))
            .where(Subscription.user_id == user_id)
            .order_by(Subscription.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
