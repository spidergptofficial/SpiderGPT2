"""SpiderGPT Deep Research Repository."""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.research import ResearchTask


class ResearchRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_task(self, task: ResearchTask) -> ResearchTask:
        self.db.add(task)
        await self.db.flush()
        return task

    async def get_task(self, task_id: str, user_id: str) -> Optional[ResearchTask]:
        stmt = select(ResearchTask).where(ResearchTask.id == task_id, ResearchTask.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_tasks(self, user_id: str, limit: int = 20) -> List[ResearchTask]:
        stmt = (
            select(ResearchTask)
            .where(ResearchTask.user_id == user_id)
            .order_by(ResearchTask.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
