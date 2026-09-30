"""SpiderGPT Standalone Plan Seeding Script."""
import asyncio
from backend.app.core.database import async_session_factory, init_db
from backend.app.repositories.plan_repo import PlanRepository
from backend.app.core.logging import logger


async def main():
    logger.info("Initializing database and seeding default plans...")
    await init_db()
    async with async_session_factory() as session:
        repo = PlanRepository(session)
        await repo.seed_plans_if_empty()
        await session.commit()
    logger.info("Plans seeded successfully!")


if __name__ == "__main__":
    asyncio.run(main())
