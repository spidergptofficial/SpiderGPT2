"""SpiderGPT User Profile & Onboarding Service."""
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.user import User
from backend.app.schemas.user import UserProfileUpdateRequest
from backend.app.repositories.user_repo import UserRepository
from backend.app.repositories.spider_repo import SpiderRepository
from backend.app.services.plan_service import PlanService


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.spider_repo = SpiderRepository(db)
        self.plan_service = PlanService(db)

    async def update_profile(self, user: User, update_data: UserProfileUpdateRequest) -> User:
        """Updates permitted profile fields only. Subscriptions, roles, and quotas are untouched."""
        data_dict = update_data.model_dump(exclude_unset=True)
        for field, value in data_dict.items():
            if hasattr(user, field):
                setattr(user, field, value)

        await self.user_repo.update(user)
        return user

    async def get_onboarding_status(self, user: User) -> Dict[str, Any]:
        spider = await self.spider_repo.get_by_user_id(user.id)
        plan = await self.plan_service.get_user_effective_plan(user)
        sub = await self.plan_service.get_user_subscription(user)

        spider_created = spider is not None
        profile_completed = bool(user.display_name or user.name)
        onboarding_done = user.onboarding_completed or (spider_created and profile_completed)

        return {
            "onboarding_completed": onboarding_done,
            "profile_completed": profile_completed,
            "spider_created": spider_created,
            "has_active_subscription": sub is not None,
            "current_plan": plan.code,
            "personality_mode": user.personality_mode,
        }
