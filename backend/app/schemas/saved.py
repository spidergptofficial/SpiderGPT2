"""SpiderGPT Saved Messages Schemas."""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class SavedMessageCreateRequest(BaseModel):
    message_id: str
    conversation_id: str
    note: Optional[str] = Field(None, max_length=1000)


class SavedMessageResponse(BaseModel):
    id: str
    user_id: str
    message_id: str
    conversation_id: str
    note: Optional[str] = None
    created_at: datetime
    message_content: Optional[str] = None
    message_role: Optional[str] = None

    class Config:
        from_attributes = True
