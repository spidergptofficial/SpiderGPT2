"""SpiderGPT Saved Messages Routes."""
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.exceptions import NotFoundException
from backend.app.core.security import get_current_user_from_token
from backend.app.models.user import User
from backend.app.models.saved import SavedMessage
from backend.app.schemas.saved import SavedMessageCreateRequest, SavedMessageResponse
from backend.app.repositories.chat_repo import ChatRepository
from backend.app.utils.id_generator import generate_id

router = APIRouter(prefix="/saved", tags=["Saved"])


@router.post("", response_model=SavedMessageResponse, status_code=status.HTTP_201_CREATED, summary="Save a chat message")
async def save_message(
    payload: SavedMessageCreateRequest,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    repo = ChatRepository(db)
    # Check conversation ownership
    conv = await repo.get_conversation(payload.conversation_id, current_user.id)
    if not conv:
        raise NotFoundException("Conversation")

    saved = SavedMessage(
        id=generate_id("sav"),
        user_id=current_user.id,
        message_id=payload.message_id,
        conversation_id=payload.conversation_id,
        note=payload.note,
    )
    saved = await repo.save_message(saved)
    return saved


@router.get("", response_model=List[SavedMessageResponse], summary="List all saved messages for current user")
async def list_saved_messages(
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    repo = ChatRepository(db)
    saved_items = await repo.list_saved_messages(current_user.id)
    res = []
    for s in saved_items:
        res.append({
            "id": s.id,
            "user_id": s.user_id,
            "message_id": s.message_id,
            "conversation_id": s.conversation_id,
            "note": s.note,
            "created_at": s.created_at,
            "message_content": s.message.content if s.message else None,
            "message_role": s.message.role if s.message else None,
        })
    return res


@router.delete("/{id}", status_code=status.HTTP_200_OK, summary="Remove a saved message")
async def delete_saved_message(
    id: str,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    repo = ChatRepository(db)
    saved = await repo.get_saved_message(id, current_user.id)
    if not saved:
        raise NotFoundException("Saved Message")

    await repo.delete_saved_message(saved)
    return {"message": "Saved message deleted successfully."}
