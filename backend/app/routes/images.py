"""SpiderGPT Image Generation Routes."""
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.security import get_current_user_from_token
from backend.app.models.user import User
from backend.app.schemas.image import (
    ImageGenerateRequest,
    ImageGenerateResponse,
    ImageResponse,
)
from backend.app.services.image_service import ImageService

router = APIRouter(prefix="/images", tags=["Images"])


@router.post("/generate", response_model=ImageGenerateResponse, status_code=status.HTTP_201_CREATED, summary="Generate image with AI")
async def generate_image(
    payload: ImageGenerateRequest,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    """Generates an image via the active ImageProvider, deducts quota only upon success, and stores metadata."""
    service = ImageService(db)
    return await service.generate_image(current_user, payload)


@router.get("", response_model=List[ImageResponse], summary="List all generated images for current user")
async def list_images(
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    service = ImageService(db)
    return await service.list_user_images(current_user)


@router.get("/{id}", response_model=ImageResponse, summary="Get generated image by ID")
async def get_image(
    id: str,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    service = ImageService(db)
    return await service.get_image(id, current_user)


@router.delete("/{id}", status_code=status.HTTP_200_OK, summary="Delete generated image")
async def delete_image(
    id: str,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    service = ImageService(db)
    await service.delete_image(id, current_user)
    return {"message": "Image deleted successfully."}
