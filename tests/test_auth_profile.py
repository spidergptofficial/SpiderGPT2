"""Tests for Authentication, Google Sign-in, and Profile Management."""
import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    res = await client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "SpiderGPT" in data["app"]


@pytest.mark.asyncio
async def test_system_providers_status(client):
    res = await client.get("/api/v1/system/providers")
    assert res.status_code == 200
    data = res.json()
    assert "ai" in data
    assert "payments" in data
    assert "search" in data
    assert "gemini" in data["ai"]
    # Secrets should not be exposed
    assert "api_key" not in str(data)
    assert "secret" not in str(data)


@pytest.mark.asyncio
async def test_google_auth_flow(client, monkeypatch):
    async def fake_verify_google_id_token(_token):
        return {"sub": "google_gwen_test", "email": "gwen.stacy@spidergpt.com", "name": "Gwen Stacy", "picture": "https://example.com/gwen.png"}

    monkeypatch.setattr("backend.app.services.auth_service.verify_google_id_token", fake_verify_google_id_token)
    res = await client.post("/api/v1/auth/google", json={
        "id_token": "test-google-id-token",
        "email": "gwen.stacy@spidergpt.com",
        "name": "Gwen Stacy",
        "picture": "https://example.com/gwen.png",
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["email"] == "gwen.stacy@spidergpt.com"
    assert data["onboarding_completed"] is False

    # Test refresh token
    refresh_res = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": data["refresh_token"],
    })
    assert refresh_res.status_code == 200
    refresh_data = refresh_res.json()
    assert "access_token" in refresh_data


@pytest.mark.asyncio
async def test_profile_read_and_update(client, test_user, test_user_token):
    # Read profile
    res = await client.get("/api/v1/profile/me", headers=test_user_token)
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == test_user.email
    assert data["display_name"] == "Peter"

    # Update permitted profile field
    update_res = await client.put(
        "/api/v1/profile/me",
        headers=test_user_token,
        json={"display_name": "Spidey Hero", "age": 22},
    )
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["display_name"] == "Spidey Hero"
    assert updated_data["age"] == 22


@pytest.mark.asyncio
async def test_unauthorized_access_blocked(client):
    res = await client.get("/api/v1/profile/me")
    assert res.status_code == 401
    err = res.json()
    assert err["error"]["code"] == "AUTH_REQUIRED"
