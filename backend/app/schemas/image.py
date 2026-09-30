"""SpiderGPT Image Generation Schemas."""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ImageGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=2, max_length=2000)
    size: str = Field(default="1024x1024")
    quality: str = Field(default="standard")
    aspect_ratio: Optional[str] = Field("1:1")


class ImageResponse(BaseModel):
    id: str
    user_id: str
    prompt: str
    image_url: str
    provider: str
    model: Optional[str] = None
    status: str
    metadata_json: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class ImageGenerateResponse(BaseModel):
    image: ImageResponse
    images_remaining_today: int
