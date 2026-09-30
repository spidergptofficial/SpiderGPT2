"""Tests for Image Generation, Web Search, and Deep Research Workflows."""
import pytest


@pytest.mark.asyncio
async def test_image_generation_and_quota(client, test_user, test_user_token):
    # Initial image quota
    usage_res = await client.get("/api/v1/usage", headers=test_user_token)
    assert usage_res.json()["images_remaining"] == 3

    # 1. Generate image
    gen_res = await client.post(
        "/api/v1/images/generate",
        headers=test_user_token,
        json={"prompt": "A friendly red robotic spider perched on a neon skyscraper"},
    )
    assert gen_res.status_code == 201
    data = gen_res.json()
    assert "image" in data
    assert "image_url" in data["image"]
    assert data["images_remaining_today"] == 2
    image_id = data["image"]["id"]

    # 2. Get image by ID
    get_res = await client.get(f"/api/v1/images/{image_id}", headers=test_user_token)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == image_id

    # 3. List images
    list_res = await client.get("/api/v1/images", headers=test_user_token)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # 4. Delete image
    del_res = await client.delete(f"/api/v1/images/{image_id}", headers=test_user_token)
    assert del_res.status_code == 200


@pytest.mark.asyncio
async def test_image_quota_exhaustion(client, test_user, test_user_token, db_session):
    from backend.app.models.usage import UsageRecord
    from backend.app.utils.timezone import get_current_date_str
    from backend.app.utils.id_generator import generate_id

    today = get_current_date_str()
    record = UsageRecord(
        id=generate_id("usg"),
        user_id=test_user.id,
        usage_type="image_generation",
        quantity=3,  # Free tier limit is 3
        date=today,
    )
    db_session.add(record)
    await db_session.commit()

    # 4th image attempt blocked with 429
    res = await client.post(
        "/api/v1/images/generate",
        headers=test_user_token,
        json={"prompt": "One too many images"},
    )
    assert res.status_code == 429
    assert res.json()["error"]["code"] == "USAGE_LIMIT_REACHED"


@pytest.mark.asyncio
async def test_web_search(client, test_user, test_user_token, monkeypatch):
    class FakeSearchProvider:
        provider_name = "test"
        async def search(self, query, max_results=5):
            return [{"title": "Test result", "url": "https://example.com/result", "snippet": "Deterministic test result.", "score": 1.0}]

    from backend.app.providers.search.factory import SearchFactory
    monkeypatch.setattr(SearchFactory, "get_search_provider", staticmethod(lambda override_name=None: FakeSearchProvider()))
    res = await client.post(
        "/api/v1/search",
        headers=test_user_token,
        json={"query": "quantum computing breakthroughs", "max_results": 3},
    )
    assert res.status_code == 200
    data = res.json()
    assert "results" in data
    assert len(data["results"]) >= 1
    assert data["provider"] == "test"


@pytest.mark.asyncio
async def test_deep_research_plan_restriction_and_execution(
    client, test_user, test_user_token, test_pro_user, test_pro_user_token
):
    # Free user attempting deep research: Blocked with 403
    res_free = await client.post(
        "/api/v1/research",
        headers=test_user_token,
        json={"query": "Comprehensive analysis of fusion energy in 2026"},
    )
    assert res_free.status_code == 403
    assert res_free.json()["error"]["code"] == "FEATURE_NOT_AVAILABLE"

    # Pro user attempting deep research: Accepted with 202
    res_pro = await client.post(
        "/api/v1/research",
        headers=test_pro_user_token,
        json={"query": "Comprehensive analysis of fusion energy in 2026"},
    )
    assert res_pro.status_code == 202
    task = res_pro.json()
    assert task["status"] in ["queued", "running", "completed"]
    task_id = task["id"]

    # Retrieve task
    task_res = await client.get(f"/api/v1/research/{task_id}", headers=test_pro_user_token)
    assert task_res.status_code == 200
    assert task_res.json()["id"] == task_id
