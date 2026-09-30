"""SpiderGPT Deep Research Service & Autonomous Worker.

Executes asynchronous multi-step research:
1. Sub-question decomposition
2. Parallel web search queries
3. Source deduplication and analysis
4. Synthesis report generation with citations
"""
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import async_session_factory
from backend.app.core.exceptions import NotFoundException, FeatureNotAvailableException
from backend.app.core.logging import logger
from backend.app.models.user import User
from backend.app.models.research import ResearchTask
from backend.app.repositories.research_repo import ResearchRepository
from backend.app.services.plan_service import PlanService
from backend.app.providers.ai.factory import AIFactory
from backend.app.providers.search.factory import SearchFactory
from backend.app.utils.id_generator import generate_id
from backend.app.utils.timezone import get_utc_now


async def execute_background_deep_research(task_id: str, query: str) -> None:
    """Independent background worker coroutine for long-running research."""
    logger.info("Starting background Deep Research for task %s", task_id)
    async with async_session_factory() as session:
        stmt = select(ResearchTask).where(ResearchTask.id == task_id)
        res = await session.execute(stmt)
        task = res.scalar_one_or_none()
        if not task:
            logger.error("Research task %s not found in worker.", task_id)
            return

        try:
            # 1. Update status to running
            task.status = "running"
            await session.commit()

            # 2. Decompose question into sub-queries via AI
            decomp_prompt = (
                f"You are a research planning assistant. Decompose this research topic into 3 specific, targeted web search queries:\n"
                f"Topic: {query}\n"
                "Return exactly 3 search queries, one per line, without numbering or bullets."
            )
            decomp_res = await AIFactory.chat_with_fallback(
                messages=[{"role": "user", "content": decomp_prompt}],
                system_instruction="Be concise and focused on high-signal search queries.",
            )

            lines = [l.strip() for l in decomp_res["content"].split("\n") if l.strip()]
            sub_queries = lines[:3] if len(lines) >= 3 else [query, f"{query} overview", f"{query} latest developments"]

            # 3. Perform web searches
            search_provider = SearchFactory.get_search_provider()
            gathered_sources: List[Dict[str, Any]] = []

            for sq in sub_queries:
                try:
                    results = await search_provider.search(sq, max_results=3)
                    for r in results:
                        if not any(s.get("url") == r.get("url") for s in gathered_sources):
                            gathered_sources.append(r)
                except Exception as e:
                    logger.warning("Search query failed for '%s': %s", sq, str(e))

            # 4. Synthesize research report
            sources_summary = "\n".join(
                f"- [{i+1}] {s['title']}: {s['snippet']} (URL: {s['url']})"
                for i, s in enumerate(gathered_sources)
            )

            report_prompt = (
                f"You are SpiderGPT Deep Research AI. Produce a comprehensive, structured research report on:\n"
                f"# Topic: {query}\n\n"
                f"## Gathered Research Sources:\n{sources_summary}\n\n"
                f"Structure the report with the following markdown sections:\n"
                f"1. Executive Summary\n"
                f"2. Key Findings & Analysis\n"
                f"3. Practical Insights & Takeaways\n"
                f"4. Source Citations & References (cite URLs used)\n"
            )

            synthesis_res = await AIFactory.chat_with_fallback(
                messages=[{"role": "user", "content": report_prompt}],
                system_instruction="You are SpiderGPT's lead deep researcher. Produce thorough, analytical, structured reports.",
                max_tokens=4000,
            )

            # 5. Save completed report
            task.report = synthesis_res["content"]
            task.sources = gathered_sources
            task.provider = synthesis_res.get("provider", "gemini")
            task.status = "completed"
            task.completed_at = get_utc_now()
            await session.commit()
            logger.info("Deep Research completed successfully for task %s", task_id)

        except Exception as e:
            logger.error("Deep Research failed for task %s: %s", task_id, str(e))
            task.status = "failed"
            task.report = f"Deep research failed due to an internal error: {str(e)}"
            await session.commit()


class ResearchService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ResearchRepository(db)
        self.plan_service = PlanService(db)

    async def initiate_research(self, user: User, query: str) -> ResearchTask:
        """Validates entitlements and queues asynchronous research task."""
        plan = await self.plan_service.get_user_effective_plan(user)
        if not plan.deep_research_allowed:
            raise FeatureNotAvailableException("Deep Research", required_plan="PRO")

        task = ResearchTask(
            id=generate_id("res"),
            user_id=user.id,
            query=query,
            status="queued",
            sources=[],
        )
        await self.repo.create_task(task)

        # Dispatch background coroutine
        asyncio.create_task(execute_background_deep_research(task.id, query))
        return task

    async def get_task(self, task_id: str, user: User) -> ResearchTask:
        task = await self.repo.get_task(task_id, user.id)
        if not task:
            raise NotFoundException("Research Task")
        return task

    async def list_tasks(self, user: User) -> List[ResearchTask]:
        return await self.repo.list_tasks(user.id)
