"""Tests for Onboarding, Spider Creation, and Single-Spider Enforcement."""
import pytest


@pytest.mark.asyncio
async def test_onboarding_status_initial(client, test_user, test_user_token):
    res = await client.get("/api/v1/onboarding/status", headers=test_user_token)
    assert res.status_code == 200
    data = res.json()
    assert data["spider_created"] is False
    assert data["onboarding_completed"] is False


@pytest.mark.asyncio
async def test_create_spider_and_enforce_single_spider(client, test_user, test_user_token):
    # 1. Create first Spider
    res = await client.post(
        "/api/v1/spider",
        headers=test_user_token,
        json={
            "spider_name": "WebSlinger",
            "personality_mode": "Brain",
            "appearance_id": "preset_classic_red",
        },
    )
    assert res.status_code == 201
    spider_data = res.json()
    assert spider_data["spider_name"] == "WebSlinger"
    assert spider_data["personality_mode"] == "Brain"

    # Verify onboarding status updated to completed
    ob_res = await client.get("/api/v1/onboarding/status", headers=test_user_token)
    assert ob_res.json()["spider_created"] is True
    assert ob_res.json()["onboarding_completed"] is True

    # 2. Attempt to create a second Spider (MUST FAIL with 409 Conflict)
    duplicate_res = await client.post(
        "/api/v1/spider",
        headers=test_user_token,
        json={
            "spider_name": "SecondSpider",
            "personality_mode": "Chill",
            "appearance_id": "preset_stealth",
        },
    )
    assert duplicate_res.status_code == 409
    err = duplicate_res.json()
    assert err["error"]["code"] == "SPIDER_ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_spider_name_update_quota(client, test_user, test_user_token):
    # Create initial spider
    await client.post(
        "/api/v1/spider",
        headers=test_user_token,
        json={"spider_name": "InitialSpider", "personality_mode": "Brain", "appearance_id": "preset_blue"},
    )

    # 1st name change: Allowed (Free plan allows 1/month)
    res1 = await client.patch(
        "/api/v1/spider/name",
        headers=test_user_token,
        json={"spider_name": "ChangedSpider1"},
    )
    assert res1.status_code == 200
    assert res1.json()["spider_name"] == "ChangedSpider1"

    # 2nd name change in same month: Blocked with 429
    res2 = await client.patch(
        "/api/v1/spider/name",
        headers=test_user_token,
        json={"spider_name": "ChangedSpider2"},
    )
    assert res2.status_code == 429
    err = res2.json()
    assert err["error"]["code"] == "USAGE_LIMIT_REACHED"


@pytest.mark.asyncio
async def test_custom_appearance_tier_restrictions(client, test_user, test_user_token, test_pro_user, test_pro_user_token):
    # Free user attempting custom appearance: Blocked with 403
    free_spider_res = await client.post(
        "/api/v1/spider",
        headers=test_user_token,
        json={
            "spider_name": "FreeSpider",
            "appearance_id": "custom_1",
            "custom_appearance_data": {"color": "neon_green", "eyes": 8},
        },
    )
    assert free_spider_res.status_code == 403
    assert free_spider_res.json()["error"]["code"] == "FEATURE_NOT_AVAILABLE"

    # Pro user attempting custom appearance: Allowed!
    pro_spider_res = await client.post(
        "/api/v1/spider",
        headers=test_pro_user_token,
        json={
            "spider_name": "ProSpider",
            "appearance_id": "custom_pro_1",
            "custom_appearance_data": {"color": "gold_black", "cyberpunk": True},
        },
    )
    assert pro_spider_res.status_code == 201
    assert pro_spider_res.json()["appearance_id"] == "custom_pro_1"
