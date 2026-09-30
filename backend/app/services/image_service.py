"""SpiderGPT Image Generation & Storage Service."""
from typing import List, Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.exceptions import NotFoundException
from backend.app.models.user import User
from backend.app.models.image import GeneratedImage
from backend.app.schemas.image import ImageGenerateRequest
from backend.app.services.usage_service import UsageService
from backend.app.providers.image.factory import ImageFactory
from backend.app.utils.id_generator import generate_id


class ImageService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.usage_service = UsageService(db)

    async def generate_image(self, user: User, request: ImageGenerateRequest) -> Dict[str, Any]:
        """Generates image, checks and consumes quota ONLY upon success, and records metadata."""
        # Check quota availability without consuming yet
        plan_overview = await self.usage_service.get_usage_overview(user)
        if plan_overview["images_remaining"] <= 0:
            from backend.app.core.exceptions import UsageLimitReachedException
            raise UsageLimitReachedException("daily image generations", plan_overview["daily_image_limit"])

        # Execute generation
        provider = ImageFactory.get_image_provider()
        gen_result = await provider.generate_image(
            prompt=request.prompt,
            size=request.size,
            quality=request.quality,
            aspect_ratio=request.aspect_ratio,
        )

        # Quota consumption strictly on success
        remaining = await self.usage_service.check_and_consume_image_generation(user)

        # Persist record
        image_record = GeneratedImage(
            id=generate_id("img"),
            user_id=user.id,
            prompt=request.prompt,
            image_url=gen_result["image_url"],
            provider=gen_result.get("provider", "openai"),
            model=gen_result.get("model"),
            status="completed",
            metadata_json=gen_result.get("metadata", {}),
        )
        self.db.add(image_record)
        await self.db.flush()

        return {
            "image": image_record,
            "images_remaining_today": remaining,
        }

    async def list_user_images(self, user: User, limit: int = 50) -> List[GeneratedImage]:
        stmt = (
            select(GeneratedImage)
            .where(GeneratedImage.user_id == user.id)
            .order_by(GeneratedImage.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_image(self, image_id: str, user: User) -> GeneratedImage:
        stmt = select(GeneratedImage).where(GeneratedImage.id == image_id, GeneratedImage.user_id == user.id)
        result = await self.db.execute(stmt)
        img = result.scalar_one_or_none()
        if not img:
            raise NotFoundException("Image")
        return img

    async def delete_image(self, image_id: str, user: User) -> None:
        img = await self.get_image(image_id, user)
        await self.db.delete(img)
        await self.db.flush()
