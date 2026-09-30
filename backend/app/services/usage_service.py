"""SpiderGPT Server-Side Usage Tracking & Quota Enforcement Service."""
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.exceptions import UsageLimitReachedException, FeatureNotAvailableException
from backend.app.models.user import User
from backend.app.models.plan import Plan
from backend.app.repositories.usage_repo import UsageRepository
from backend.app.services.plan_service import PlanService
from backend.app.utils.timezone import get_current_date_str, get_current_month_str


class UsageService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.usage_repo = UsageRepository(db)
        self.plan_service = PlanService(db)

    async def get_usage_overview(self, user: User) -> Dict[str, Any]:
        """Compiles full usage report for GET /api/v1/usage."""
        plan: Plan = await self.plan_service.get_user_effective_plan(user)
        today = get_current_date_str()
        current_month = get_current_month_str()

        # Daily counts
        responses_used = await self.usage_repo.get_usage_sum(user.id, "ai_response", today)
        images_used = await self.usage_repo.get_usage_sum(user.id, "image_generation", today)

        # Monthly counts
        name_changes_used = await self.usage_repo.get_usage_sum(user.id, "spider_name_change", current_month)
        appearance_changes_used = await self.usage_repo.get_usage_sum(user.id, "appearance_change", current_month)
        custom_appearances_used = await self.usage_repo.get_usage_sum(user.id, "custom_appearance_creation", current_month)

        # Daily remainders
        responses_remaining = -1 if plan.daily_response_limit == -1 else max(0, plan.daily_response_limit - responses_used)
        images_remaining = max(0, plan.daily_image_limit - images_used)

        # Monthly remainders (-1 indicates unlimited)
        if plan.monthly_name_change_limit == -1:
            name_remaining = 999999
        else:
            name_remaining = max(0, plan.monthly_name_change_limit - name_changes_used)

        if plan.monthly_appearance_change_limit == -1:
            appearance_remaining = 999999
        else:
            appearance_remaining = max(0, plan.monthly_appearance_change_limit - appearance_changes_used)

        return {
            "plan": plan.code,
            "plan_name": plan.name,
            "date": today,
            "month": current_month,
            "daily_response_limit": plan.daily_response_limit,
            "responses_used": responses_used,
            "responses_remaining": responses_remaining,
            "daily_image_limit": plan.daily_image_limit,
            "images_used": images_used,
            "images_remaining": images_remaining,
            "monthly_customization_limits": {
                "name_change_limit": plan.monthly_name_change_limit,
                "name_changes_used": name_changes_used,
                "name_changes_remaining": name_remaining,
                "appearance_change_limit": plan.monthly_appearance_change_limit,
                "appearance_changes_used": appearance_changes_used,
                "appearance_changes_remaining": appearance_remaining,
                "custom_appearance_allowed": plan.custom_appearance_allowed,
                "custom_appearances_created": custom_appearances_used,
            },
            "customization_usage": {
                "name_changes": name_changes_used,
                "appearance_changes": appearance_changes_used,
                "custom_appearances": custom_appearances_used,
            },
            "features": {
                "allowed_modes": plan.allowed_modes,
                "deep_research_allowed": plan.deep_research_allowed,
                "custom_appearance_allowed": plan.custom_appearance_allowed,
            },
        }

    async def check_and_consume_ai_response(self, user: User) -> int:
        """Atomically checks daily response limit and consumes 1 unit."""
        plan = await self.plan_service.get_user_effective_plan(user)
        today = get_current_date_str()
        await self.usage_repo.lock_user(user.id)
        used = await self.usage_repo.get_usage_sum(user.id, "ai_response", today)

        if used >= plan.daily_response_limit:
            raise UsageLimitReachedException(
                usage_type="daily AI responses",
                limit=plan.daily_response_limit,
                message=f"You have reached your daily limit of {plan.daily_response_limit} AI responses on the {plan.name} plan. Resets tomorrow at midnight {today}.",
            )

        await self.usage_repo.record_usage(user.id, "ai_response", quantity=1, date_str=today)
        return plan.daily_response_limit - (used + 1)

    async def check_and_consume_image_generation(self, user: User) -> int:
        """Atomically checks daily image limit and consumes 1 unit."""
        plan = await self.plan_service.get_user_effective_plan(user)
        today = get_current_date_str()
        await self.usage_repo.lock_user(user.id)
        used = await self.usage_repo.get_usage_sum(user.id, "image_generation", today)

        if used >= plan.daily_image_limit:
            raise UsageLimitReachedException(
                usage_type="daily image generations",
                limit=plan.daily_image_limit,
                message=f"You have reached your daily limit of {plan.daily_image_limit} images on the {plan.name} plan.",
            )

        await self.usage_repo.record_usage(user.id, "image_generation", quantity=1, date_str=today)
        return plan.daily_image_limit - (used + 1)

    async def check_and_consume_name_change(self, user: User) -> None:
        """Atomically checks and consumes monthly spider name change quota."""
        plan = await self.plan_service.get_user_effective_plan(user)
        if plan.monthly_name_change_limit == -1:
            # Unlimited
            await self.usage_repo.record_usage(user.id, "spider_name_change", quantity=1)
            return

        month = get_current_month_str()
        await self.usage_repo.lock_user(user.id)
        used = await self.usage_repo.get_usage_sum(user.id, "spider_name_change", month)
        if used >= plan.monthly_name_change_limit:
            raise UsageLimitReachedException(
                usage_type="monthly Spider name changes",
                limit=plan.monthly_name_change_limit,
                message=f"You have reached your monthly name change limit ({plan.monthly_name_change_limit}) on the {plan.name} plan.",
            )

        await self.usage_repo.record_usage(user.id, "spider_name_change", quantity=1, date_str=month)

    async def check_and_consume_appearance_change(self, user: User) -> None:
        """Atomically checks and consumes monthly appearance change quota."""
        plan = await self.plan_service.get_user_effective_plan(user)
        if plan.monthly_appearance_change_limit == -1:
            # Unlimited
            await self.usage_repo.record_usage(user.id, "appearance_change", quantity=1)
            return

        month = get_current_month_str()
        await self.usage_repo.lock_user(user.id)
        used = await self.usage_repo.get_usage_sum(user.id, "appearance_change", month)
        if used >= plan.monthly_appearance_change_limit:
            raise UsageLimitReachedException(
                usage_type="monthly Spider appearance changes",
                limit=plan.monthly_appearance_change_limit,
                message=f"You have reached your monthly appearance change limit ({plan.monthly_appearance_change_limit}) on the {plan.name} plan.",
            )

        await self.usage_repo.record_usage(user.id, "appearance_change", quantity=1, date_str=month)

    async def check_custom_appearance_permission(self, user: User) -> None:
        """Verifies plan permission for creating custom appearances."""
        plan = await self.plan_service.get_user_effective_plan(user)
        if not plan.custom_appearance_allowed:
            raise FeatureNotAvailableException("Custom Spider Appearance Creation", required_plan="PRO")

        # Record custom appearance event
        await self.usage_repo.lock_user(user.id)
        month = get_current_month_str()
        await self.usage_repo.record_usage(user.id, "custom_appearance_creation", quantity=1, date_str=month)
