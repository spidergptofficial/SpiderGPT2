"""SpiderGPT Atomic Usage Repository."""
from typing import Dict, Any, Optional
from sqlalchemy import select, func
from backend.app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.usage import UsageRecord
from backend.app.utils.id_generator import generate_id
from backend.app.utils.timezone import get_current_date_str, get_current_month_str


class UsageRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def lock_user(self, user_id: str) -> None:
        """Serialize quota checks for the same user on PostgreSQL."""
        await self.db.execute(select(User.id).where(User.id == user_id).with_for_update())

    async def get_usage_sum(self, user_id: str, usage_type: str, date_str: str) -> int:
        """Calculates total consumed units for a given user, usage type, and date/month string."""
        stmt = (
            select(func.coalesce(func.sum(UsageRecord.quantity), 0))
            .where(
                UsageRecord.user_id == user_id,
                UsageRecord.usage_type == usage_type,
                UsageRecord.date == date_str,
            )
        )
        result = await self.db.execute(stmt)
        return int(result.scalar_one())

    async def record_usage(
        self,
        user_id: str,
        usage_type: str,
        quantity: int = 1,
        date_str: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UsageRecord:
        """Records a usage increment; callers enforcing limits lock the user first."""
        if not date_str:
            # Monthly vs Daily convention
            if "change" in usage_type or "custom_appearance" in usage_type:
                date_str = get_current_month_str()
            else:
                date_str = get_current_date_str()

        rec = UsageRecord(
            id=generate_id("usg"),
            user_id=user_id,
            usage_type=usage_type,
            quantity=quantity,
            date=date_str,
            metadata_json=metadata or {},
        )
        self.db.add(rec)
        await self.db.flush()
        return rec

    async def get_daily_usage(self, user_id: str, date_str: Optional[str] = None) -> Dict[str, int]:
        d = date_str or get_current_date_str()
        ai_responses = await self.get_usage_sum(user_id, "ai_response", d)
        images = await self.get_usage_sum(user_id, "image_generation", d)
        searches = await self.get_usage_sum(user_id, "web_search", d)
        research = await self.get_usage_sum(user_id, "deep_research", d)
        return {
            "ai_responses": ai_responses,
            "images": images,
            "searches": searches,
            "research": research,
        }

    async def get_monthly_customization_usage(self, user_id: str, month_str: Optional[str] = None) -> Dict[str, int]:
        m = month_str or get_current_month_str()
        name_changes = await self.get_usage_sum(user_id, "spider_name_change", m)
        appearance_changes = await self.get_usage_sum(user_id, "appearance_change", m)
        custom_creations = await self.get_usage_sum(user_id, "custom_appearance_creation", m)
        return {
            "name_changes": name_changes,
            "appearance_changes": appearance_changes,
            "custom_appearances": custom_creations,
        }
