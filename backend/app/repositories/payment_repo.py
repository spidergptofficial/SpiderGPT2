"""SpiderGPT Payment & Webhook Idempotency Repository."""
from typing import Optional
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.payment import PaymentOrder, ProcessedWebhookEvent
from backend.app.utils.id_generator import generate_id
from backend.app.utils.timezone import get_utc_now


class PaymentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_order(self, order: PaymentOrder) -> PaymentOrder:
        self.db.add(order)
        await self.db.flush()
        return order

    async def get_order_by_order_id(self, order_id: str) -> Optional[PaymentOrder]:
        stmt = select(PaymentOrder).where(PaymentOrder.order_id == order_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def is_event_processed(self, event_id: str) -> bool:
        """Checks if a webhook event ID has already been recorded to enforce idempotency."""
        stmt = select(ProcessedWebhookEvent).where(ProcessedWebhookEvent.event_id == event_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def claim_webhook_event(
        self,
        event_id: str,
        provider: str,
        event_type: str,
        payload_summary: dict,
    ) -> bool:
        """Atomically claim an event ID; returns False for a concurrent/previous duplicate."""
        event = ProcessedWebhookEvent(
            id=generate_id("evt"),
            event_id=event_id,
            provider=provider,
            event_type=event_type,
            payload_summary=payload_summary,
            processed_at=get_utc_now(),
        )
        try:
            async with self.db.begin_nested():
                self.db.add(event)
                await self.db.flush()
            return True
        except IntegrityError:
            return False

    async def claim_webhook_event(
        self,
        event_id: str,
        provider: str,
        event_type: str,
        payload_summary: dict,
    ) -> bool:
        event = ProcessedWebhookEvent(
            id=generate_id("evt"),
            event_id=event_id,
            provider=provider,
            event_type=event_type,
            payload_summary=payload_summary,
            processed_at=get_utc_now(),
        )
        try:
            async with self.db.begin_nested():
                self.db.add(event)
                await self.db.flush()
            return True
        except IntegrityError:
            return False

    async def record_processed_event(
        self,
        event_id: str,
        provider: str,
        event_type: str,
        payload_summary: dict,
    ) -> ProcessedWebhookEvent:
        event = ProcessedWebhookEvent(
            id=generate_id("evt"),
            event_id=event_id,
            provider=provider,
            event_type=event_type,
            payload_summary=payload_summary,
            processed_at=get_utc_now(),
        )
        self.db.add(event)
        await self.db.flush()
        return event
