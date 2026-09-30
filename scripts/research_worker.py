"""SpiderGPT durable Deep Research worker.

Run this as a separate deployment process. Research jobs are persisted in the
database, so API restarts do not discard queued work.
"""
import asyncio
from sqlalchemy import select

from backend.app.core.database import async_session_factory
from backend.app.core.logging import logger
from backend.app.models.research import ResearchTask
from backend.app.services.research_service import execute_background_deep_research

POLL_SECONDS = 2


async def next_task_id():
    async with async_session_factory() as session:
        result = await session.execute(
            select(ResearchTask.id)
            .where(ResearchTask.status == "queued")
            .order_by(ResearchTask.created_at.asc())
            .limit(1)
        )
        row = result.first()
        return row[0] if row else None


async def worker_loop():
    logger.info("SpiderGPT research worker started")
    while True:
        task_id = await next_task_id()
        if task_id:
            await execute_background_deep_research(task_id, "")
        else:
            await asyncio.sleep(POLL_SECONDS)


if __name__ == "__main__":
    asyncio.run(worker_loop())
