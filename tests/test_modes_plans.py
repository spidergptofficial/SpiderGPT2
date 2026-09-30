"""Tests for Personality Modes and Subscription Plans."""
import pytest


@pytest.mark.asyncio
async def test_personality_modes_list(client):
    res = await client.get("/api/v1/system/modes")
    assert res.status_code == 200
    modes = res.json()
    mode_names = [m["name"] for m in modes]
    assert "Brain" in mode_names
    assert "Chill" in mode_names
    assert "Focus" in mode_names
    assert "Chaos" in mode_names
    assert "Create" in mode_names
    assert "Roast" in mode_names


@pytest.mark.asyncio
async def test_mode_plan_entitlements(client, test_user, test_user_token, test_pro_user, test_pro_user_token):
    # Free user attempting Roast mode: Blocked (Requires Plus)
    res_free = await client.post(
        "/api/v1/chat",
        headers=test_user_token,
        json={"message": "Hey Spider", "mode": "Roast"},
    )
    assert res_free.status_code == 403
    assert res_free.json()["error"]["code"] == "FEATURE_NOT_AVAILABLE"

    # Pro user attempting Chaos mode: Allowed
    res_pro = await client.post(
        "/api/v1/chat",
        headers=test_pro_user_token,
        json={"message": "Brainstorm something crazy", "mode": "Chaos"},
    )
    assert res_pro.status_code == 200

    # Pro user attempting Roast mode: Blocked (Requires Plus)
    res_pro_roast = await client.post(
        "/api/v1/chat",
        headers=test_pro_user_token,
        json={"message": "Roast me", "mode": "Roast"},
    )
    assert res_pro_roast.status_code == 403
    assert res_pro_roast.json()["error"]["code"] == "FEATURE_NOT_AVAILABLE"


@pytest.mark.asyncio
async def test_plans_endpoint_pricing(client):
    res = await client.get("/api/v1/subscriptions/plans")
    assert res.status_code == 200
    plans = res.json()
    codes = {p["code"]: p for p in plans}

    assert "FREE" in codes
    assert "PRO" in codes
    assert "PLUS" in codes

    # Free plan verification
    assert codes["FREE"]["monthly_price_inr"] == 0
    assert codes["FREE"]["daily_response_limit"] == 30

    # Pro plan verification: ₹399/mo, ₹4,188/yr (₹349/mo equivalent)
    assert codes["PRO"]["monthly_price_inr"] == 399
    assert codes["PRO"]["yearly_price_inr"] == 4188
    assert codes["PRO"]["annual_monthly_equivalent_inr"] == 349
    assert codes["PRO"]["daily_response_limit"] == 150

    # Plus plan verification: ₹999/mo, ₹10,788/yr (₹899/mo equivalent)
    assert codes["PLUS"]["monthly_price_inr"] == 999
    assert codes["PLUS"]["yearly_price_inr"] == 10788
    assert codes["PLUS"]["annual_monthly_equivalent_inr"] == 899
    assert codes["PLUS"]["daily_response_limit"] == -1
