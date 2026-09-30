"""SpiderGPT durable Deep Research worker with safe claiming and recovery."""
import asyncio
from datetime import timedelta
from sqlalchemy import select, update

from backend.app.core.database import async_session_factory
from backend.app.core.logging import logger
from backend.app.models.research import ResearchTask
from backend.app.services.research_service import execute_background_deep_research
from backend.app.utils.timezone import get_utc_now

POLL_SECONDS = 2
STALE_AFTER_MINUTES = 20
MAX_ATTEMPTS = 3


async def claim_next_task():
    async with async_session_factory() as session:
        async with session.begin():
            result = await session.execute(
                select(ResearchTask)
                .where(ResearchTask.status == "queued", ResearchTask.attempts < MAX_ATTEMPTS)
                .order_by(ResearchTask.created_at.asc())
                .with_for_update(skip_locked=True)
                .limit(1)
            )
            task = result.scalar_one_or_none()
            if not task:
                return None
            task.status = "running"
            task.started_at = get_utc_now()
            task.attempts += 1
            return task.id


async def recover_stale_tasks():
    cutoff = get_utc_now() - timedelta(minutes=STALE_AFTER_MINUTES)
    async with async_session_factory() as session:
        await session.execute(
            update(ResearchTask)
            .where(
                ResearchTask.status == "running",
                ResearchTask.started_at.is_not(None),
                ResearchTask.started_at < cutoff,
                ResearchTask.attempts < MAX_ATTEMPTS,
            )
            .values(status="queued", started_at=None)
        )
        await session.execute(
            update(ResearchTask)
            .where(
                ResearchTask.status == "running",
                ResearchTask.started_at.is_not(None),
                ResearchTask.started_at < cutoff,
                ResearchTask.attempts >= MAX_ATTEMPTS,
            )
            .values(status="failed", completed_at=get_utc_now(),
                    report="Deep research exceeded the maximum retry count. Please retry the task.")
        )
        await session.commit()


async def worker_loop():
    logger.info("SpiderGPT research worker started")
    while True:
        await recover_stale_tasks()
        task_id = await claim_next_task()
        if task_id:
            await execute_background_deep_research(task_id, already_claimed=True)
        else:
            await asyncio.sleep(POLL_SECONDS)


if __name__ == "__main__":
    asyncio.run(worker_loop())
