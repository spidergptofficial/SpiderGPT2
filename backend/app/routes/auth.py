"""SpiderGPT Google Authentication Routes."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.security import get_current_user_from_token
from backend.app.models.user import User
from backend.app.schemas.auth import GoogleAuthRequest, TokenResponse, RefreshTokenRequest
from backend.app.schemas.user import UserProfileResponse
from backend.app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/google", response_model=TokenResponse, summary="Sign in or register with Google OAuth")
async def google_auth(
    payload: GoogleAuthRequest,
    db: AsyncSession = Depends(get_db),
):
    """Verifies Google ID token, provisions profile if first-time signin, and issues internal JWT session tokens."""
    service = AuthService(db)
    return await service.authenticate_google(
        id_token=payload.id_token,
        access_token=payload.access_token,
        fallback_email=payload.email,
        fallback_name=payload.name,
        fallback_picture=payload.picture,
    )


@router.post("/refresh", response_model=TokenResponse, summary="Refresh access token")
async def refresh_token(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    return await service.refresh_tokens(payload.refresh_token)


@router.post("/logout", status_code=status.HTTP_200_OK, summary="Logout authenticated session")
async def logout(
    current_user: User = Depends(get_current_user_from_token),
):
    return {"message": "Successfully logged out."}


@router.get("/me", response_model=UserProfileResponse, summary="Get authenticated session user")
async def get_auth_me(
    current_user: User = Depends(get_current_user_from_token),
):
    return current_user
