"""Payment orchestration tests using a fake provider.

Live gateway credentials and payment simulations are never used by tests.
"""
import json
import pytest

from backend.app.providers.payments.factory import PaymentFactory


class FakePaymentProvider:
    provider_name = "razorpay"
    is_configured = True

    async def create_checkout(self, user_id, email, plan_code, billing_period, amount, currency, metadata=None):
        return {
            "provider": "razorpay",
            "order_id": f"sub_test_{plan_code}_{billing_period}",
            "amount": amount,
            "currency": currency,
            "key_id": "test_public_key",
            "client_secret": None,
            "checkout_url": None,
            "provider_subscription_id": f"sub_test_{plan_code}_{billing_period}",
            "metadata": metadata or {},
        }

    async def get_checkout_details(self, checkout_id):
        return {
            "paid": True,
            "mode": "subscription",
            "provider_subscription_id": checkout_id,
            "customer_id": "cust_test",
            "current_period_start": None,
            "current_period_end": None,
        }

    async def verify_payment(self, order_id, payment_id=None, signature=None):
        return True

    async def cancel_subscription(self, provider_subscription_id, cancel_immediately=False):
        return True

    def verify_webhook_signature(self, payload_body, headers):
        return True

    def parse_webhook_event(self, payload_body, headers):
        data = json.loads(payload_body.decode("utf-8"))
        entity = data["payload"]["payment"]["entity"]
        return {
            "event_id": data["event_id"],
            "event_type": data["event"],
            "user_id": entity["notes"]["user_id"],
            "plan_code": entity["notes"]["plan_code"],
            "billing_period": entity["notes"].get("billing_period", "monthly"),
            "provider_subscription_id": entity["subscription_id"],
            "provider_customer_id": None,
            "current_period_start": None,
            "current_period_end": None,
            "status": "active",
            "raw": data,
        }


@pytest.fixture
def fake_payment_provider(monkeypatch):
    provider = FakePaymentProvider()
    monkeypatch.setattr(
        PaymentFactory,
        "resolve_provider",
        classmethod(lambda cls, requested_provider=None, currency=None: provider),
    )
    monkeypatch.setattr(
        PaymentFactory,
        "get_availability",
        classmethod(lambda cls: {"razorpay": True, "stripe": False}),
    )
    return provider


@pytest.mark.asyncio
async def test_payment_providers_availability(client, fake_payment_provider):
    res = await client.get("/api/v1/payments/providers")
    assert res.status_code == 200
    data = res.json()
    assert data["razorpay"] is True
    assert data["stripe"] is False


@pytest.mark.asyncio
async def test_create_checkout_session(client, test_user, test_user_token, fake_payment_provider):
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
    assert data["amount"] == 39900
    assert data["provider_subscription_id"].startswith("sub_test_")


@pytest.mark.asyncio
async def test_payment_verification_and_subscription_activation(client, test_user, test_user_token, fake_payment_provider):
    checkout_res = await client.post(
        "/api/v1/payments/checkout",
        headers=test_user_token,
        json={"plan_code": "PLUS", "billing_period": "yearly", "currency": "INR"},
    )
    assert checkout_res.status_code == 201
    order_id = checkout_res.json()["order_id"]

    verify_res = await client.post(
        "/api/v1/payments/verify",
        headers=test_user_token,
        json={
            "provider": "razorpay",
            "order_id": order_id,
            "payment_id": "pay_test",
            "signature": "test_signature",
        },
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["plan"] == "PLUS"

    sub_res = await client.get("/api/v1/subscriptions/me", headers=test_user_token)
    assert sub_res.status_code == 200
    assert sub_res.json()["plan_code"] == "PLUS"

    usage_res = await client.get("/api/v1/usage", headers=test_user_token)
    assert usage_res.json()["daily_response_limit"] == -1


@pytest.mark.asyncio
async def test_webhook_idempotency_enforcement(client, test_user, fake_payment_provider):
    payload = {
        "event": "payment.captured",
        "event_id": "evt_unique_12345678",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_id_999",
                    "subscription_id": "sub_test_webhook",
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
    body = json.dumps(payload).encode("utf-8")

    res1 = await client.post(
        "/api/v1/webhooks/razorpay",
        content=body,
        headers={"Content-Type": "application/json", "X-Razorpay-Signature": "test_sig"},
    )
    assert res1.status_code == 200
    assert res1.json()["status"] == "processed"

    res2 = await client.post(
        "/api/v1/webhooks/razorpay",
        content=body,
        headers={"Content-Type": "application/json", "X-Razorpay-Signature": "test_sig"},
    )
    assert res2.status_code == 200
    assert res2.json()["status"] == "duplicate_skipped"
