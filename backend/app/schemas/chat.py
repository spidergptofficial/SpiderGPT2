"""SpiderGPT Chat Schemas."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ChatAttachment(BaseModel):
    name: str
    url: str
    mime_type: str
    size: Optional[int] = None


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    user_id: str
    role: str
    content: str
    attachments: List[Dict[str, Any]]
    model: Optional[str] = None
    provider: Optional[str] = None
    token_usage: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    mode: str
    created_at: datetime
    updated_at: datetime
    last_message: Optional[str] = None
    message_count: Optional[int] = 0

    class Config:
        from_attributes = True


class ConversationDetailResponse(ConversationResponse):
    messages: List[MessageResponse] = []


class ConversationCreateRequest(BaseModel):
    title: Optional[str] = Field("New Conversation", max_length=255)
    mode: Optional[str] = Field("Brain", max_length=32)


class ConversationUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    mode: Optional[str] = Field(None, max_length=32)


class ChatRequest(BaseModel):
    conversation_id: Optional[str] = Field(None, description="Optional existing conversation ID. If omitted, a new conversation is created.")
    message: str = Field(..., min_length=1, max_length=32000)
    mode: Optional[str] = Field(None, description="Mode override (Brain, Chill, Chaos, Roast, Create, Focus)")
    attachments: Optional[List[ChatAttachment]] = Field(default_factory=list)
    stream: bool = Field(default=False)
    web_search: bool = Field(default=False, description="Whether to ground response with web search")


class ChatResponse(BaseModel):
    conversation_id: str
    message: MessageResponse
    remaining_responses_today: int
