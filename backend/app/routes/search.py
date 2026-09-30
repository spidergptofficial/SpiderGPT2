"""SpiderGPT Web Search Routes."""
from fastapi import APIRouter, Depends
from backend.app.core.security import get_current_user_from_token
from backend.app.models.user import User
from backend.app.schemas.search import SearchRequest, SearchResponse
from backend.app.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["Search"])


@router.post("", response_model=SearchResponse, summary="Perform web search")
async def web_search(
    payload: SearchRequest,
    current_user: User = Depends(get_current_user_from_token),
):
    """Executes search across configured search provider (Tavily/Serper/DuckDuckGo)."""
    return await SearchService.perform_search(payload.query, max_results=payload.max_results)
