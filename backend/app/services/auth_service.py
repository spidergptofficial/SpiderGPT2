"""SpiderGPT Google Authentication & Token Issuance Service."""
import uuid
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.exceptions import InvalidTokenException
from backend.app.core.logging import logger
from backend.app.core.security import create_access_token, create_refresh_token, verify_google_id_token, verify_supabase_access_token, decode_token
from backend.app.models.user import User
from backend.app.repositories.user_repo import UserRepository
from backend.app.repositories.plan_repo import PlanRepository
from backend.app.utils.id_generator import generate_id


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.plan_repo = PlanRepository(db)

    async def authenticate_google(
        self,
        id_token: Optional[str] = None,
        access_token: Optional[str] = None,
        fallback_email: Optional[str] = None,
        fallback_name: Optional[str] = None,
        fallback_picture: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Authenticates user via Google OAuth identity verification and creates or updates local profile."""
        google_info = None

        if access_token and settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY:
            google_info = await verify_supabase_access_token(access_token)
        elif id_token:
            try:
                google_info = await verify_google_id_token(id_token)
            except Exception as e:
                # If in test/dev and fallback email provided, use dev mock
                if (settings.DEBUG or settings.ENVIRONMENT == "development") and fallback_email:
                    logger.info("Using mock Google OAuth info in development mode: %s", fallback_email)
                    google_info = {
                        "sub": f"google_{uuid.uuid4().hex[:12]}",
                        "email": fallback_email,
                        "name": fallback_name or "Test User",
                        "picture": fallback_picture,
                    }
                else:
                    raise e
        elif fallback_email and (settings.DEBUG or settings.ENVIRONMENT == "development"):
            # Dev mode fallback
            google_info = {
                "sub": f"google_{uuid.uuid4().hex[:12]}",
                "email": fallback_email,
                "name": fallback_name or "Spider User",
                "picture": fallback_picture,
            }
        else:
            raise InvalidTokenException("A valid Supabase access token or Google ID token is required.")

        email = google_info["email"].lower().strip()
        auth_id = google_info["sub"]

        # Ensure plans are seeded
        await self.plan_repo.seed_plans_if_empty()

        # Find or create user
        user = await self.user_repo.get_by_email(email)
        if not user:
            is_admin = email in settings.ADMIN_EMAILS
            user = User(
                id=generate_id("usr"),
                auth_provider_id=auth_id,
                email=email,
                name=google_info.get("name"),
                display_name=google_info.get("name"),
                avatar_url=google_info.get("picture"),
                onboarding_completed=False,
                personality_mode="Brain",
                default_mode="Brain",
                role="admin" if is_admin else "user",
                is_admin=is_admin,
            )
            await self.user_repo.create(user)
            logger.info("New user registered via Google: %s (id: %s)", email, user.id)
        else:
            # Update profile info if present
            if google_info.get("picture") and not user.avatar_url:
                user.avatar_url = google_info["picture"]
            await self.user_repo.update(user)

        # Generate tokens
        token_payload = {
            "sub": user.id,
            "email": user.email,
            "role": user.role,
        }
        access = create_access_token(token_payload)
        refresh = create_refresh_token(token_payload)

        return {
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user_id": user.id,
            "email": user.email,
            "onboarding_completed": user.onboarding_completed,
        }

    async def refresh_tokens(self, refresh_token_str: str) -> Dict[str, Any]:
        """Issues new access token using a valid refresh token."""
        payload = decode_token(refresh_token_str)
        if payload.get("type") != "refresh":
            raise InvalidTokenException("Provided token is not a refresh token.")

        user_id = payload.get("sub")
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise InvalidTokenException("User not found.")

        new_access = create_access_token({"sub": user.id, "email": user.email, "role": user.role})
        new_refresh = create_refresh_token({"sub": user.id, "email": user.email, "role": user.role})

        return {
            "access_token": new_access,
            "refresh_token": new_refresh,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user_id": user.id,
            "email": user.email,
            "onboarding_completed": user.onboarding_completed,
        }
