"""SpiderGPT Test Fixtures & Configurations."""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from backend.app.core.database import Base, get_db
from backend.app.core.security import create_access_token
from backend.app.main import app
from backend.app.models.user import User
from backend.app.models.spider import Spider
from backend.app.repositories.plan_repo import PlanRepository
from backend.app.providers.ai.factory import AIFactory
from backend.app.providers.image.factory import ImageFactory
from backend.app.utils.id_generator import generate_id

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(autouse=True)
def mock_external_providers(monkeypatch):
    """Mocks external AI and Image providers for deterministic, fast, offline tests."""
    async def mock_chat(messages, system_instruction=None, temperature=0.7, max_tokens=2048, provider_override=None):
        return {
            "content": "Spider AI: Test response successfully generated.",
            "model": "gemini-3.8-flash",
            "provider": "gemini",
            "token_usage": {"prompt_tokens": 15, "completion_tokens": 10, "total_tokens": 25},
        }

    async def mock_stream(messages, system_instruction=None, temperature=0.7, max_tokens=2048, provider_override=None):
        yield "Spider "
        yield "AI: "
        yield "Streaming "
        yield "test."

    monkeypatch.setattr(AIFactory, "chat_with_fallback", mock_chat)
    monkeypatch.setattr(AIFactory, "stream_chat_with_fallback", mock_stream)



@pytest_asyncio.fixture(scope="function")
async def db_session():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        # Seed default plans
        plan_repo = PlanRepository(session)
        await plan_repo.seed_plans_if_empty()
        await session.commit()
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session):
    user = User(
        id=generate_id("usr"),
        auth_provider_id="google_test_12345",
        email="peter.parker@spidergpt.com",
        name="Peter Parker",
        display_name="Peter",
        onboarding_completed=False,
        personality_mode="Brain",
        default_mode="Brain",
        role="user",
        is_admin=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_pro_user(db_session):
    user = User(
        id=generate_id("usr"),
        auth_provider_id="google_pro_12345",
        email="miles.morales@spidergpt.com",
        name="Miles Morales",
        display_name="Miles",
        onboarding_completed=True,
        personality_mode="Chill",
        default_mode="Chill",
        role="user",
        is_admin=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Attach Pro subscription
    from backend.app.models.subscription import Subscription
    sub = Subscription(
        id=generate_id("sub"),
        user_id=user.id,
        plan_id="plan_pro",
        provider="manual",
        status="active",
        billing_period="monthly",
    )
    db_session.add(sub)
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def test_user_token(test_user):
    token = create_access_token({"sub": test_user.id, "email": test_user.email, "role": test_user.role})
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def test_pro_user_token(test_pro_user):
    token = create_access_token({"sub": test_pro_user.id, "email": test_pro_user.email, "role": test_pro_user.role})
    return {"Authorization": f"Bearer {token}"}
