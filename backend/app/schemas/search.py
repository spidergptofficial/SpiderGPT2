"""SpiderGPT Web Search Schemas."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500)
    max_results: int = Field(default=5, ge=1, le=20)


class SearchResultItem(BaseModel):
    title: str
    url: str
    snippet: str
    score: Optional[float] = None


class SearchResponse(BaseModel):
    query: str
    provider: str
    results: List[SearchResultItem]
    total_results: int
