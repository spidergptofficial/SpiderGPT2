"""SpiderGPT Chat, Messages, and Saved Content Repository."""
from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.chat import Conversation, Message, UserMemory
from backend.app.models.saved import SavedMessage


class ChatRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # Conversations
    async def list_conversations(self, user_id: str, limit: int = 50) -> List[Conversation]:
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_conversation(self, conversation_id: str, user_id: str) -> Optional[Conversation]:
        """Gets conversation strictly enforcing user ownership!"""
        stmt = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_conversation(self, conversation: Conversation) -> Conversation:
        self.db.add(conversation)
        await self.db.flush()
        return conversation

    async def delete_conversation(self, conversation: Conversation) -> None:
        await self.db.delete(conversation)
        await self.db.flush()

    # Messages
    async def list_messages(self, conversation_id: str, user_id: str, limit: int = 50) -> List[Message]:
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id, Message.user_id == user_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_recent_messages(self, conversation_id: str, limit: int = 15) -> List[Message]:
        """Loads recent conversation messages for context window management."""
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        messages = list(result.scalars().all())
        messages.reverse()
        return messages

    async def add_message(self, message: Message) -> Message:
        self.db.add(message)
        await self.db.flush()
        return message

    # Saved Messages
    async def save_message(self, saved: SavedMessage) -> SavedMessage:
        self.db.add(saved)
        await self.db.flush()
        return saved

    async def list_saved_messages(self, user_id: str) -> List[SavedMessage]:
        stmt = (
            select(SavedMessage)
            .options(selectinload(SavedMessage.message))
            .where(SavedMessage.user_id == user_id)
            .order_by(SavedMessage.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_saved_message(self, saved_id: str, user_id: str) -> Optional[SavedMessage]:
        stmt = select(SavedMessage).where(SavedMessage.id == saved_id, SavedMessage.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_saved_message(self, saved: SavedMessage) -> None:
        await self.db.delete(saved)
        await self.db.flush()

    # User Memories
    async def get_user_memories(self, user_id: str, limit: int = 10) -> List[UserMemory]:
        stmt = (
            select(UserMemory)
            .where(UserMemory.user_id == user_id)
            .order_by(UserMemory.importance.desc(), UserMemory.updated_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
