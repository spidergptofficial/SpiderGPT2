"""SpiderGPT Deep Research Routes."""
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.security import get_current_user_from_token
from backend.app.models.user import User
from backend.app.schemas.research import ResearchCreateRequest, ResearchTaskResponse
from backend.app.services.research_service import ResearchService

router = APIRouter(prefix="/research", tags=["Research"])


@router.post("", response_model=ResearchTaskResponse, status_code=status.HTTP_202_ACCEPTED, summary="Initiate asynchronous deep research")
async def start_research(
    payload: ResearchCreateRequest,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    """Initiates an asynchronous multi-step research operation. Returns queued task immediately."""
    service = ResearchService(db)
    return await service.initiate_research(current_user, payload.query)


@router.get("", response_model=List[ResearchTaskResponse], summary="List deep research history")
async def list_research(
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    service = ResearchService(db)
    return await service.list_tasks(current_user)


@router.get("/{id}", response_model=ResearchTaskResponse, summary="Get deep research task status and report")
async def get_research_task(
    id: str,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    service = ResearchService(db)
    return await service.get_task(id, current_user)
