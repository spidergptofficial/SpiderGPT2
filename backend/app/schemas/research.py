"""SpiderGPT Deep Research Schemas."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ResearchCreateRequest(BaseModel):
    query: str = Field(..., min_length=5, max_length=1000, description="The research question or topic")


class ResearchTaskResponse(BaseModel):
    id: str
    user_id: str
    query: str
    status: str  # queued, running, completed, failed, cancelled
    report: Optional[str] = None
    sources: List[Dict[str, Any]] = []
    provider: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
