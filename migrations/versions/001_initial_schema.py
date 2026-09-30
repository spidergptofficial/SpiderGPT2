"""Initial schema for SpiderGPT

Revision ID: 001_initial_schema
Revises: None
Create Date: 2026-09-30 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Users
    op.create_table(
        "users",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("auth_provider_id", sa.String(128), unique=True, index=True, nullable=False),
        sa.Column("email", sa.String(255), unique=True, index=True, nullable=False),
        sa.Column("display_name", sa.String(128), nullable=True),
        sa.Column("name", sa.String(128), nullable=True),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("avatar_url", sa.String(512), nullable=True),
        sa.Column("onboarding_completed", sa.Boolean(), default=False, nullable=False),
        sa.Column("personality_mode", sa.String(32), default="Brain", nullable=False),
        sa.Column("default_mode", sa.String(32), default="Brain", nullable=False),
        sa.Column("role", sa.String(32), default="user", nullable=False),
        sa.Column("is_admin", sa.Boolean(), default=False, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 2. Spiders (Enforces ONE Spider per user via unique constraint on user_id)
    op.create_table(
        "spiders",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False),
        sa.Column("spider_name", sa.String(64), default="Spider", nullable=False),
        sa.Column("personality_mode", sa.String(32), default="Brain", nullable=False),
        sa.Column("appearance_id", sa.String(64), default="preset_default", nullable=False),
        sa.Column("custom_appearance_data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 3. Spider Appearances
    op.create_table(
        "spider_appearances",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False),
        sa.Column("spider_id", sa.String(64), sa.ForeignKey("spiders.id", ondelete="CASCADE"), index=True, nullable=False),
        sa.Column("appearance_type", sa.String(16), default="PRESET", nullable=False),
        sa.Column("preset_id", sa.String(64), nullable=True),
        sa.Column("image_url", sa.String(512), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 4. Plans
    op.create_table(
        "plans",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("code", sa.String(32), unique=True, index=True, nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("monthly_price_inr", sa.Integer(), default=0, nullable=False),
        sa.Column("yearly_price_inr", sa.Integer(), default=0, nullable=False),
        sa.Column("monthly_price_usd", sa.Integer(), default=0, nullable=False),
        sa.Column("yearly_price_usd", sa.Integer(), default=0, nullable=False),
        sa.Column("regional_pricing", sa.JSON(), nullable=False),
        sa.Column("daily_response_limit", sa.Integer(), default=30, nullable=False),
        sa.Column("daily_image_limit", sa.Integer(), default=3, nullable=False),
        sa.Column("monthly_name_change_limit", sa.Integer(), default=1, nullable=False),
        sa.Column("monthly_appearance_change_limit", sa.Integer(), default=2, nullable=False),
        sa.Column("custom_appearance_allowed", sa.Boolean(), default=False, nullable=False),
        sa.Column("allowed_modes", sa.JSON(), nullable=False),
        sa.Column("deep_research_allowed", sa.Boolean(), default=False, nullable=False),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 5. Plan Features
    op.create_table(
        "plan_features",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("plan_id", sa.String(64), sa.ForeignKey("plans.id"), index=True, nullable=False),
        sa.Column("feature_key", sa.String(64), nullable=False),
        sa.Column("feature_value", sa.String(128), nullable=False),
        sa.Column("description", sa.String(255), nullable=False),
    )

    # 6. Subscriptions
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False),
        sa.Column("plan_id", sa.String(64), sa.ForeignKey("plans.id"), index=True, nullable=False),
        sa.Column("provider", sa.String(32), default="manual", nullable=False),
        sa.Column("provider_customer_id", sa.String(128), nullable=True),
        sa.Column("provider_subscription_id", sa.String(128), unique=True, index=True, nullable=True),
        sa.Column("billing_period", sa.String(16), default="monthly", nullable=False),
        sa.Column("currency", sa.String(8), default="INR", nullable=False),
        sa.Column("amount", sa.Integer(), default=0, nullable=False),
        sa.Column("status", sa.String(32), default="active", index=True, nullable=False),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_at_period_end", sa.Boolean(), default=False, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 7. Usage Records
    op.create_table(
        "usage_records",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False),
        sa.Column("usage_type", sa.String(64), index=True, nullable=False),
        sa.Column("quantity", sa.Integer(), default=1, nullable=False),
        sa.Column("date", sa.String(16), index=True, nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_usage_user_type_date", "usage_records", ["user_id", "usage_type", "date"])

    # 8. Conversations
    op.create_table(
        "conversations",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False),
        sa.Column("title", sa.String(255), default="New Conversation", nullable=False),
        sa.Column("mode", sa.String(32), default="Brain", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 9. Messages
    op.create_table(
        "messages",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("conversation_id", sa.String(64), sa.ForeignKey("conversations.id", ondelete="CASCADE"), index=True, nullable=False),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("attachments", sa.JSON(), nullable=False),
        sa.Column("model", sa.String(128), nullable=True),
        sa.Column("provider", sa.String(64), nullable=True),
        sa.Column("token_usage", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), index=True, nullable=False),
    )

    # 10. User Memories
    op.create_table(
        "user_memories",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False),
        sa.Column("category", sa.String(64), default="preference", nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("importance", sa.Integer(), default=1, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 11. Saved Messages
    op.create_table(
        "saved_messages",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False),
        sa.Column("message_id", sa.String(64), sa.ForeignKey("messages.id", ondelete="CASCADE"), index=True, nullable=False),
        sa.Column("conversation_id", sa.String(64), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 12. Generated Images
    op.create_table(
        "generated_images",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("image_url", sa.String(1024), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("model", sa.String(64), nullable=True),
        sa.Column("status", sa.String(32), default="completed", nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), index=True, nullable=False),
    )

    # 13. Research Tasks
    op.create_table(
        "research_tasks",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), default="queued", index=True, nullable=False),
        sa.Column("report", sa.Text(), nullable=True),
        sa.Column("sources", sa.JSON(), nullable=False),
        sa.Column("provider", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), index=True, nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 14. Payment Orders
    op.create_table(
        "payment_orders",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False),
        sa.Column("plan_id", sa.String(64), sa.ForeignKey("plans.id"), index=True, nullable=False),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("order_id", sa.String(128), unique=True, index=True, nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(8), default="INR", nullable=False),
        sa.Column("status", sa.String(32), default="created", nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 15. Processed Webhook Events (Enforces idempotency across Razorpay and Stripe)
    op.create_table(
        "processed_webhook_events",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("event_id", sa.String(128), unique=True, index=True, nullable=False),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("payload_summary", sa.JSON(), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("processed_webhook_events")
    op.drop_table("payment_orders")
    op.drop_table("research_tasks")
    op.drop_table("generated_images")
    op.drop_table("saved_messages")
    op.drop_table("user_memories")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("usage_records")
    op.drop_table("subscriptions")
    op.drop_table("plan_features")
    op.drop_table("plans")
    op.drop_table("spider_appearances")
    op.drop_table("spiders")
    op.drop_table("users")
