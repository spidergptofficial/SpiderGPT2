"""SpiderGPT Spider Repository."""
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.spider import Spider, SpiderAppearance


class SpiderRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_id(self, user_id: str) -> Optional[Spider]:
        stmt = select(Spider).where(Spider.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, spider: Spider) -> Spider:
        self.db.add(spider)
        await self.db.flush()
        return spider

    async def record_appearance_change(self, record: SpiderAppearance) -> SpiderAppearance:
        self.db.add(record)
        await self.db.flush()
        return record

    async def get_appearance_history(self, user_id: str, limit: int = 20) -> List[SpiderAppearance]:
        stmt = (
            select(SpiderAppearance)
            .where(SpiderAppearance.user_id == user_id)
            .order_by(SpiderAppearance.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
