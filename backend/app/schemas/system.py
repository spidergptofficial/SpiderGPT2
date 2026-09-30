"""SpiderGPT System Status & Admin Schemas."""
from typing import Dict, Any, Optional
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    environment: str
    timestamp: str


class ProvidersStatusResponse(BaseModel):
    ai: Dict[str, bool]
    payments: Dict[str, bool]
    search: Dict[str, bool]
    image: Dict[str, bool]
    active_ai_provider: str
    fallback_ai_provider: Optional[str]
    active_search_provider: str
    active_image_provider: str


class AdminConfigUpdateRequest(BaseModel):
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None
    fallback_ai_provider: Optional[str] = None
    image_provider: Optional[str] = None
    search_provider: Optional[str] = None
    timezone: Optional[str] = None
