"""Tests for Payment Gateways (Razorpay & Stripe), Webhooks, and Idempotency."""
import json
import pytest
from backend.app.core.config import settings


@pytest.mark.asyncio
async def test_payment_providers_availability(client):
    res = await client.get("/api/v1/payments/providers")
    assert res.status_code == 200
    data = res.json()
    assert "razorpay" in data
    assert "stripe" in data
    assert "preferred_currency" in data


@pytest.mark.asyncio
async def test_create_checkout_session(client, test_user, test_user_token):
    res = await client.post(
        "/api/v1/payments/checkout",
        headers=test_user_token,
        json={
            "plan_code": "PRO",
            "billing_period": "monthly",
            "provider": "razorpay",
            "currency": "INR",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["provider"] == "razorpay"
    assert "order_id" in data
    assert data["amount"] == 39900  # ₹399 in paise


@pytest.mark.asyncio
async def test_payment_verification_and_subscription_activation(client, test_user, test_user_token):
    # 1. Create order
    checkout_res = await client.post(
        "/api/v1/payments/checkout",
        headers=test_user_token,
        json={"plan_code": "PLUS", "billing_period": "yearly", "currency": "INR"},
    )
    order_id = checkout_res.json()["order_id"]

    # 2. Verify payment (in test simulation mode)
    verify_res = await client.post(
        "/api/v1/payments/verify",
        headers=test_user_token,
        json={
            "provider": "razorpay",
            "order_id": order_id,
            "payment_id": f"pay_test_{order_id}",
            "signature": "test_valid_sig",
        },
    )
    assert verify_res.status_code == 200
    v_data = verify_res.json()
    assert v_data["success"] is True
    assert v_data["plan"] == "PLUS"
    assert v_data["status"] == "active"

    # 3. Check that user's effective subscription and usage limits are now PLUS (300 responses)
    sub_res = await client.get("/api/v1/subscriptions/me", headers=test_user_token)
    assert sub_res.status_code == 200
    assert sub_res.json()["plan_code"] == "PLUS"

    usage_res = await client.get("/api/v1/usage", headers=test_user_token)
    assert usage_res.json()["daily_response_limit"] == 300


@pytest.mark.asyncio
async def test_webhook_idempotency_enforcement(client, test_user):
    payload = {
        "event": "payment.captured",
        "event_id": "evt_unique_12345678",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_id_999",
                    "amount": 39900,
                    "notes": {
                        "user_id": test_user.id,
                        "plan_code": "PRO",
                        "billing_period": "monthly",
                    },
                }
            }
        },
    }
    payload_bytes = json.dumps(payload).encode("utf-8")

    # 1. First webhook delivery: Processes successfully
    res1 = await client.post(
        "/api/v1/webhooks/razorpay",
        content=payload_bytes,
        headers={"Content-Type": "application/json", "X-Razorpay-Signature": "test_sig"},
    )
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["status"] == "processed"

    # 2. Duplicate webhook delivery (same event_id): Skips idempotently without duplicating
    res2 = await client.post(
        "/api/v1/webhooks/razorpay",
        content=payload_bytes,
        headers={"Content-Type": "application/json", "X-Razorpay-Signature": "test_sig"},
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["status"] == "duplicate_skipped"
    assert data2["event_id"] == "evt_unique_12345678"
