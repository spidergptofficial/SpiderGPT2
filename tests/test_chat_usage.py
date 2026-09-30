"""Tests for Chat, Streaming, Conversation Ownership, Saved Messages, and Usage Limits."""
import pytest


@pytest.mark.asyncio
async def test_chat_and_usage_tracking(client, test_user, test_user_token):
    # Check initial usage
    usage_res1 = await client.get("/api/v1/usage", headers=test_user_token)
    assert usage_res1.status_code == 200
    u1 = usage_res1.json()
    assert u1["responses_used"] == 0
    assert u1["responses_remaining"] == 30

    # Send chat message
    chat_res = await client.post(
        "/api/v1/chat",
        headers=test_user_token,
        json={"message": "Hello Spider!", "mode": "Brain"},
    )
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert "conversation_id" in chat_data
    assert "content" in chat_data["message"]
    assert chat_data["remaining_responses_today"] == 29

    # Verify usage counter incremented
    usage_res2 = await client.get("/api/v1/usage", headers=test_user_token)
    u2 = usage_res2.json()
    assert u2["responses_used"] == 1
    assert u2["responses_remaining"] == 29


@pytest.mark.asyncio
async def test_chat_sse_stream(client, test_user, test_user_token):
    res = await client.post(
        "/api/v1/chat/stream",
        headers=test_user_token,
        json={"message": "Tell me a short fact", "mode": "Brain"},
    )
    assert res.status_code == 200
    assert "text/event-stream" in res.headers.get("content-type", "")
    content = res.text
    assert "event: meta" in content
    assert "event: chunk" in content
    assert "event: done" in content


@pytest.mark.asyncio
async def test_conversation_ownership(client, test_user, test_user_token, test_pro_user, test_pro_user_token):
    # User A creates conversation
    conv_res = await client.post(
        "/api/v1/conversations",
        headers=test_user_token,
        json={"title": "Private Convo", "mode": "Brain"},
    )
    assert conv_res.status_code == 201
    conv_id = conv_res.json()["id"]

    # User A can read it
    res_a = await client.get(f"/api/v1/conversations/{conv_id}", headers=test_user_token)
    assert res_a.status_code == 200

    # User B attempting to read User A's conversation gets 404 (ownership enforced)
    res_b = await client.get(f"/api/v1/conversations/{conv_id}", headers=test_pro_user_token)
    assert res_b.status_code == 404
    assert res_b.json()["error"]["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_saved_messages_flow(client, test_user, test_user_token):
    # 1. Send chat message
    chat_res = await client.post(
        "/api/v1/chat",
        headers=test_user_token,
        json={"message": "Save this important advice", "mode": "Brain"},
    )
    conv_id = chat_res.json()["conversation_id"]
    msg_id = chat_res.json()["message"]["id"]

    # 2. Save message
    save_res = await client.post(
        "/api/v1/saved",
        headers=test_user_token,
        json={"conversation_id": conv_id, "message_id": msg_id, "note": "Crucial reminder"},
    )
    assert save_res.status_code == 201
    saved_id = save_res.json()["id"]

    # 3. List saved messages
    list_res = await client.get("/api/v1/saved", headers=test_user_token)
    assert list_res.status_code == 200
    items = list_res.json()
    assert len(items) >= 1
    assert items[0]["id"] == saved_id

    # 4. Delete saved message
    del_res = await client.delete(f"/api/v1/saved/{saved_id}", headers=test_user_token)
    assert del_res.status_code == 200


@pytest.mark.asyncio
async def test_daily_ai_response_quota_exhaustion(client, test_user, test_user_token, db_session):
    # Directly simulate 30 consumed responses for test_user today
    from backend.app.models.usage import UsageRecord
    from backend.app.utils.timezone import get_current_date_str
    from backend.app.utils.id_generator import generate_id

    today = get_current_date_str()
    record = UsageRecord(
        id=generate_id("usg"),
        user_id=test_user.id,
        usage_type="ai_response",
        quantity=30,
        date=today,
    )
    db_session.add(record)
    await db_session.commit()

    # 31st request should be blocked with 429 USAGE_LIMIT_REACHED
    res = await client.post(
        "/api/v1/chat",
        headers=test_user_token,
        json={"message": "Exceeded request", "mode": "Brain"},
    )
    assert res.status_code == 429
    err = res.json()
    assert err["error"]["code"] == "USAGE_LIMIT_REACHED"
    assert "daily limit of 30 AI responses" in err["error"]["message"]
