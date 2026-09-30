"""SpiderGPT AI Chat & Streaming Routes."""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.security import get_current_user_from_token
from backend.app.models.user import User
from backend.app.schemas.chat import ChatRequest, ChatResponse
from backend.app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse, summary="Send message to Spider AI Sidekick")
async def chat_message(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    """Sends a message to the user's Spider AI Sidekick, injecting active mode context and consuming quota."""
    service = ChatService(db)
    return await service.process_chat(current_user, payload)


@router.post("/stream", summary="Stream message response from Spider via Server-Sent Events (SSE)")
async def chat_stream(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    """Streams tokens in real-time as Server-Sent Events (SSE).

    Event structure:
    event: meta -> JSON { conversation_id }
    event: chunk -> JSON { delta: '...' }
    event: done -> JSON { message_id }
    """
    service = ChatService(db)
    generator = service.stream_chat(current_user, payload)
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
