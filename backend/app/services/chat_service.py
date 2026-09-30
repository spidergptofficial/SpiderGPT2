"""SpiderGPT Chat Orchestrator & Context Memory Engine."""
import json
from typing import AsyncIterator, Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.exceptions import NotFoundException
from backend.app.models.user import User
from backend.app.models.spider import Spider
from backend.app.models.chat import Conversation, Message
from backend.app.schemas.chat import ChatRequest
from backend.app.repositories.chat_repo import ChatRepository
from backend.app.repositories.spider_repo import SpiderRepository
from backend.app.services.plan_service import PlanService
from backend.app.services.usage_service import UsageService
from backend.app.services.mode_service import ModeService
from backend.app.providers.ai.factory import AIFactory
from backend.app.providers.search.factory import SearchFactory
from backend.app.utils.id_generator import generate_id


class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.chat_repo = ChatRepository(db)
        self.spider_repo = SpiderRepository(db)
        self.plan_service = PlanService(db)
        self.usage_service = UsageService(db)

    async def _build_system_context(self, user: User, mode_name: str, spider: Optional[Spider]) -> str:
        """Constructs comprehensive prompt injecting Spider personality, mode rules, and user memory."""
        mode_instruction = ModeService.get_mode_instruction(mode_name)
        spider_name = spider.spider_name if spider else "Spider"

        memories = await self.chat_repo.get_user_memories(user.id, limit=5)
        memory_str = ""
        if memories:
            memory_str = "\nUser preferences and known facts:\n" + "\n".join(f"- {m.content}" for m in memories)

        prompt = (
            f"You are {spider_name}, the user's dedicated AI Sidekick.\n"
            f"Active Personality Mode: {mode_name}.\n"
            f"Mode Directives: {mode_instruction}\n"
            f"User's name: {user.display_name or user.name or 'friend'}.\n"
            f"{memory_str}\n"
            "Stay in character consistently. Provide engaging, intelligent, and accurate responses."
        )
        return prompt

    async def process_chat(self, user: User, request: ChatRequest) -> Dict[str, Any]:
        """Processes non-streaming chat with quota enforcement, context windowing, and provider dispatch."""
        # 1. Resolve Conversation
        remaining = None

        # 2. Resolve Conversation
        conversation = None
        if request.conversation_id:
            conversation = await self.chat_repo.get_conversation(request.conversation_id, user.id)
            if not conversation:
                raise NotFoundException("Conversation")
        else:
            # Create new conversation
            clean_title = request.message[:40] + ("..." if len(request.message) > 40 else "")
            conversation = Conversation(
                id=generate_id("conv"),
                user_id=user.id,
                title=clean_title,
                mode=request.mode or user.personality_mode,
            )
            await self.chat_repo.create_conversation(conversation)

        # 3. Mode validation
        plan = await self.plan_service.get_user_effective_plan(user)
        active_mode = ModeService.validate_mode_access(request.mode or conversation.mode, plan.allowed_modes)

        # 4. Reserve quota after conversation and mode validation.
        remaining = await self.usage_service.check_and_consume_ai_response(user)

        # 5. Save User Message
        user_msg = Message(
            id=generate_id("msg"),
            conversation_id=conversation.id,
            user_id=user.id,
            role="user",
            content=request.message,
            attachments=[a.model_dump() for a in (request.attachments or [])],
        )
        await self.chat_repo.add_message(user_msg)

        # 6. Optional Web Search Grounding
        search_context = ""
        if request.web_search:
            search_provider = SearchFactory.get_search_provider()
            search_results = await search_provider.search(request.message, max_results=3)
            if search_results:
                search_context = "\nWeb Search Results:\n" + "\n".join(
                    f"[{i+1}] {r['title']}: {r['snippet']} ({r['url']})" for i, r in enumerate(search_results)
                )

        # 7. Context Window Assembly
        spider = await self.spider_repo.get_by_user_id(user.id)
        system_prompt = await self._build_system_context(user, active_mode, spider)
        if search_context:
            system_prompt += f"\n{search_context}\nUse these search results to answer the query accurately."

        history_msgs = await self.chat_repo.get_recent_messages(conversation.id, limit=12)
        formatted_history = [{"role": m.role, "content": m.content} for m in history_msgs]

        # 8. AI Provider Execution with Fallback
        ai_result = await AIFactory.chat_with_fallback(
            messages=formatted_history,
            system_instruction=system_prompt,
        )

        # 9. Save Assistant Message
        assistant_msg = Message(
            id=generate_id("msg"),
            conversation_id=conversation.id,
            user_id=user.id,
            role="assistant",
            content=ai_result["content"],
            model=ai_result.get("model"),
            provider=ai_result.get("provider"),
            token_usage=ai_result.get("token_usage", {}),
        )
        await self.chat_repo.add_message(assistant_msg)

        return {
            "conversation_id": conversation.id,
            "message": assistant_msg,
            "remaining_responses_today": remaining,
        }

    async def stream_chat(self, user: User, request: ChatRequest) -> AsyncIterator[str]:
        """Streams response tokens through Server-Sent Events (SSE)."""
        # Conversation resolution and mode validation happen before quota consumption.

        # Conversation resolution
        if request.conversation_id:
            conversation = await self.chat_repo.get_conversation(request.conversation_id, user.id)
            if not conversation:
                raise NotFoundException("Conversation")
        else:
            clean_title = request.message[:40] + ("..." if len(request.message) > 40 else "")
            conversation = Conversation(
                id=generate_id("conv"),
                user_id=user.id,
                title=clean_title,
                mode=request.mode or user.personality_mode,
            )
            await self.chat_repo.create_conversation(conversation)

        # Mode validation
        plan = await self.plan_service.get_user_effective_plan(user)
        active_mode = ModeService.validate_mode_access(request.mode or conversation.mode, plan.allowed_modes)

        # Reserve quota after conversation and mode validation.
        await self.usage_service.check_and_consume_ai_response(user)

        # Save user message
        user_msg = Message(
            id=generate_id("msg"),
            conversation_id=conversation.id,
            user_id=user.id,
            role="user",
            content=request.message,
            attachments=[a.model_dump() for a in (request.attachments or [])],
        )
        await self.chat_repo.add_message(user_msg)

        # Assemble prompt
        spider = await self.spider_repo.get_by_user_id(user.id)
        system_prompt = await self._build_system_context(user, active_mode, spider)

        history_msgs = await self.chat_repo.get_recent_messages(conversation.id, limit=12)
        formatted_history = [{"role": m.role, "content": m.content} for m in history_msgs]

        full_content_chunks = []

        # Yield metadata event first
        yield f"event: meta\ndata: {json.dumps({'conversation_id': conversation.id})}\n\n"

        async for chunk in AIFactory.stream_chat_with_fallback(
            messages=formatted_history,
            system_instruction=system_prompt,
        ):
            full_content_chunks.append(chunk)
            yield f"event: chunk\ndata: {json.dumps({'delta': chunk})}\n\n"

        # Finalize and persist assistant message in database
        full_text = "".join(full_content_chunks)
        assistant_msg = Message(
            id=generate_id("msg"),
            conversation_id=conversation.id,
            user_id=user.id,
            role="assistant",
            content=full_text,
            model=None,
            provider=None,
        )
        await self.chat_repo.add_message(assistant_msg)

        yield f"event: done\ndata: {json.dumps({'message_id': assistant_msg.id})}\n\n"
