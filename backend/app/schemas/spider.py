"""SpiderGPT Personal Spider Schemas."""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class SpiderCreateRequest(BaseModel):
    spider_name: str = Field(default="Spider", min_length=1, max_length=64)
    personality_mode: str = Field(default="Brain", max_length=32)
    appearance_id: str = Field(default="preset_classic", max_length=64)
    custom_appearance_data: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SpiderUpdateRequest(BaseModel):
    spider_name: Optional[str] = Field(None, min_length=1, max_length=64)
    personality_mode: Optional[str] = Field(None, max_length=32)
    appearance_id: Optional[str] = Field(None, max_length=64)
    custom_appearance_data: Optional[Dict[str, Any]] = None


class SpiderNameUpdateRequest(BaseModel):
    spider_name: str = Field(..., min_length=1, max_length=64)


class SpiderPersonalityUpdateRequest(BaseModel):
    personality_mode: str = Field(..., min_length=1, max_length=32)


class SpiderAppearanceUpdateRequest(BaseModel):
    appearance_type: str = Field(default="PRESET", description="PRESET or CUSTOM")
    appearance_id: str = Field(..., description="Preset ID or generated custom ID")
    custom_appearance_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    prompt: Optional[str] = Field(None, description="Prompt if generating custom AI appearance")


class SpiderResponse(BaseModel):
    id: str
    user_id: str
    spider_name: str
    personality_mode: str
    appearance_id: str
    custom_appearance_data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SpiderAppearanceHistoryItem(BaseModel):
    id: str
    appearance_type: str
    preset_id: Optional[str] = None
    image_url: Optional[str] = None
    metadata_json: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True
