"""SpiderGPT Personal Spider System Service.

Enforces single-Spider per user, quota limits for customization,
preset vs custom appearances, and personality modes.
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.exceptions import (
    SpiderAlreadyExistsException,
    NotFoundException,
    FeatureNotAvailableException,
)
from backend.app.models.user import User
from backend.app.models.spider import Spider, SpiderAppearance
from backend.app.schemas.spider import SpiderCreateRequest, SpiderUpdateRequest, SpiderAppearanceUpdateRequest
from backend.app.repositories.spider_repo import SpiderRepository
from backend.app.repositories.user_repo import UserRepository
from backend.app.services.plan_service import PlanService
from backend.app.services.usage_service import UsageService
from backend.app.services.mode_service import ModeService
from backend.app.providers.image.factory import ImageFactory
from backend.app.utils.id_generator import generate_id


class SpiderService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.spider_repo = SpiderRepository(db)
        self.user_repo = UserRepository(db)
        self.plan_service = PlanService(db)
        self.usage_service = UsageService(db)

    async def get_spider_for_user(self, user: User) -> Spider:
        spider = await self.spider_repo.get_by_user_id(user.id)
        if not spider:
            raise NotFoundException("Spider", "No Spider found for this user. Please complete onboarding first.")
        return spider

    async def create_spider(self, user: User, data: SpiderCreateRequest) -> Spider:
        """Creates the user's single Spider companion. Strictly blocks creating multiple."""
        existing = await self.spider_repo.get_by_user_id(user.id)
        if existing:
            raise SpiderAlreadyExistsException()

        # Validate mode against plan
        plan = await self.plan_service.get_user_effective_plan(user)
        mode = ModeService.validate_mode_access(data.personality_mode, plan.allowed_modes)

        # Check appearance type
        custom_data = data.custom_appearance_data or {}
        if custom_data and not plan.custom_appearance_allowed:
            raise FeatureNotAvailableException("Custom Spider Appearance Creation", required_plan="PRO")

        spider = Spider(
            id=generate_id("spd"),
            user_id=user.id,
            spider_name=data.spider_name,
            personality_mode=mode,
            appearance_id=data.appearance_id,
            custom_appearance_data=custom_data,
        )
        await self.spider_repo.create(spider)

        # Record initial appearance
        appearance_rec = SpiderAppearance(
            id=generate_id("appr"),
            user_id=user.id,
            spider_id=spider.id,
            appearance_type="CUSTOM" if custom_data else "PRESET",
            preset_id=data.appearance_id,
            image_url=custom_data.get("image_url"),
            metadata_json={"initial_creation": True},
        )
        await self.spider_repo.record_appearance_change(appearance_rec)

        # Mark onboarding completed
        user.onboarding_completed = True
        user.personality_mode = mode
        await self.user_repo.update(user)

        return spider

    async def update_spider_name(self, user: User, new_name: str) -> Spider:
        spider = await self.get_spider_for_user(user)
        if spider.spider_name == new_name:
            return spider

        # Check and consume monthly name change limit
        await self.usage_service.check_and_consume_name_change(user)
        spider.spider_name = new_name
        return spider

    async def update_spider_personality(self, user: User, new_mode: str) -> Spider:
        spider = await self.get_spider_for_user(user)
        plan = await self.plan_service.get_user_effective_plan(user)
        validated_mode = ModeService.validate_mode_access(new_mode, plan.allowed_modes)

        spider.personality_mode = validated_mode
        user.personality_mode = validated_mode
        await self.user_repo.update(user)
        return spider

    async def update_spider_appearance(self, user: User, data: SpiderAppearanceUpdateRequest) -> Spider:
        spider = await self.get_spider_for_user(user)
        plan = await self.plan_service.get_user_effective_plan(user)

        # Check and consume monthly appearance change quota
        await self.usage_service.check_and_consume_appearance_change(user)

        app_type = data.appearance_type.upper()
        custom_data = data.custom_appearance_data or {}
        image_url = custom_data.get("image_url")

        if app_type == "CUSTOM":
            # Verify plan allows custom appearance
            await self.usage_service.check_custom_appearance_permission(user)

            # If prompt provided for AI generation
            if data.prompt:
                img_provider = ImageFactory.get_image_provider()
                gen_result = await img_provider.generate_image(
                    prompt=f"A distinctive, stylized Spider character companion: {data.prompt}",
                    size="1024x1024",
                )
                image_url = gen_result["image_url"]
                custom_data["image_url"] = image_url
                custom_data["generated_prompt"] = data.prompt

        spider.appearance_id = data.appearance_id
        spider.custom_appearance_data = custom_data

        # Log to customization history
        appearance_rec = SpiderAppearance(
            id=generate_id("appr"),
            user_id=user.id,
            spider_id=spider.id,
            appearance_type=app_type,
            preset_id=data.appearance_id if app_type == "PRESET" else None,
            image_url=image_url,
            metadata_json=custom_data,
        )
        await self.spider_repo.record_appearance_change(appearance_rec)

        return spider

    async def get_appearance_history(self, user: User) -> List[SpiderAppearance]:
        return await self.spider_repo.get_appearance_history(user.id)
