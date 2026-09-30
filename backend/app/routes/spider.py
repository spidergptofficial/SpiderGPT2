"""SpiderGPT Personal Spider System Routes."""
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.security import get_current_user_from_token
from backend.app.models.user import User
from backend.app.schemas.spider import (
    SpiderCreateRequest,
    SpiderUpdateRequest,
    SpiderNameUpdateRequest,
    SpiderPersonalityUpdateRequest,
    SpiderAppearanceUpdateRequest,
    SpiderResponse,
    SpiderAppearanceHistoryItem,
)
from backend.app.services.spider_service import SpiderService

router = APIRouter(prefix="/spider", tags=["Spider"])


@router.get("/me", response_model=SpiderResponse, summary="Get user's personal Spider companion")
async def get_my_spider(
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    service = SpiderService(db)
    return await service.get_spider_for_user(current_user)


@router.post("", response_model=SpiderResponse, status_code=status.HTTP_201_CREATED, summary="Create user's personal Spider companion")
async def create_spider(
    payload: SpiderCreateRequest,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    """Creates the user's Spider companion during onboarding. Enforces exactly ONE Spider per user."""
    service = SpiderService(db)
    return await service.create_spider(current_user, payload)


@router.put("/me", response_model=SpiderResponse, summary="Update entire Spider configuration")
async def update_my_spider(
    payload: SpiderUpdateRequest,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    service = SpiderService(db)
    spider = await service.get_spider_for_user(current_user)
    if payload.spider_name and payload.spider_name != spider.spider_name:
        spider = await service.update_spider_name(current_user, payload.spider_name)
    if payload.personality_mode and payload.personality_mode != spider.personality_mode:
        spider = await service.update_spider_personality(current_user, payload.personality_mode)
    if payload.appearance_id and payload.appearance_id != spider.appearance_id:
        update_req = SpiderAppearanceUpdateRequest(
            appearance_type="CUSTOM" if payload.custom_appearance_data else "PRESET",
            appearance_id=payload.appearance_id,
            custom_appearance_data=payload.custom_appearance_data or {},
        )
        spider = await service.update_spider_appearance(current_user, update_req)
    return spider


@router.patch("/name", response_model=SpiderResponse, summary="Update Spider name (quota tracked)")
async def update_spider_name(
    payload: SpiderNameUpdateRequest,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    service = SpiderService(db)
    return await service.update_spider_name(current_user, payload.spider_name)


@router.patch("/personality", response_model=SpiderResponse, summary="Update Spider personality mode")
async def update_spider_personality(
    payload: SpiderPersonalityUpdateRequest,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    service = SpiderService(db)
    return await service.update_spider_personality(current_user, payload.personality_mode)


@router.patch("/appearance", response_model=SpiderResponse, summary="Update Spider appearance preset or custom")
async def update_spider_appearance(
    payload: SpiderAppearanceUpdateRequest,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    service = SpiderService(db)
    return await service.update_spider_appearance(current_user, payload)


@router.get("/appearances/history", response_model=List[SpiderAppearanceHistoryItem], summary="Get Spider customization history")
async def get_appearance_history(
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    service = SpiderService(db)
    return await service.get_appearance_history(current_user)
