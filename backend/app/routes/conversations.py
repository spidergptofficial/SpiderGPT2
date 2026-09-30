"""SpiderGPT Conversation Management Routes."""
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.exceptions import NotFoundException
from backend.app.core.security import get_current_user_from_token
from backend.app.models.user import User
from backend.app.models.chat import Conversation
from backend.app.schemas.chat import (
    ConversationResponse,
    ConversationDetailResponse,
    ConversationCreateRequest,
    ConversationUpdateRequest,
    MessageResponse,
)
from backend.app.repositories.chat_repo import ChatRepository
from backend.app.utils.id_generator import generate_id

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.get("", response_model=List[ConversationResponse], summary="List all conversations for current user")
async def list_conversations(
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    repo = ChatRepository(db)
    return await repo.list_conversations(current_user.id)


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED, summary="Create a new conversation")
async def create_conversation(
    payload: ConversationCreateRequest,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    repo = ChatRepository(db)
    conv = Conversation(
        id=generate_id("conv"),
        user_id=current_user.id,
        title=payload.title or "New Conversation",
        mode=payload.mode or current_user.personality_mode,
    )
    return await repo.create_conversation(conv)


@router.get("/{id}", response_model=ConversationDetailResponse, summary="Get conversation details by ID")
async def get_conversation(
    id: str,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    repo = ChatRepository(db)
    conv = await repo.get_conversation(id, current_user.id)
    if not conv:
        raise NotFoundException("Conversation")

    messages = await repo.list_messages(id, current_user.id)
    return {
        "id": conv.id,
        "user_id": conv.user_id,
        "title": conv.title,
        "mode": conv.mode,
        "created_at": conv.created_at,
        "updated_at": conv.updated_at,
        "messages": messages,
    }


@router.patch("/{id}", response_model=ConversationResponse, summary="Update conversation title or mode")
async def update_conversation(
    id: str,
    payload: ConversationUpdateRequest,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    repo = ChatRepository(db)
    conv = await repo.get_conversation(id, current_user.id)
    if not conv:
        raise NotFoundException("Conversation")

    if payload.title is not None:
        conv.title = payload.title
    if payload.mode is not None:
        conv.mode = payload.mode

    await db.flush()
    return conv


@router.delete("/{id}", status_code=status.HTTP_200_OK, summary="Delete conversation by ID")
async def delete_conversation(
    id: str,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    repo = ChatRepository(db)
    conv = await repo.get_conversation(id, current_user.id)
    if not conv:
        raise NotFoundException("Conversation")

    await repo.delete_conversation(conv)
    return {"message": "Conversation deleted successfully."}


@router.get("/{id}/messages", response_model=List[MessageResponse], summary="List all messages in a conversation")
async def get_conversation_messages(
    id: str,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    repo = ChatRepository(db)
    conv = await repo.get_conversation(id, current_user.id)
    if not conv:
        raise NotFoundException("Conversation")

    return await repo.list_messages(id, current_user.id)
