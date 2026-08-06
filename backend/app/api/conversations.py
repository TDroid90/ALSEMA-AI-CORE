import asyncio
import json
from collections.abc import AsyncIterator
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_permission
from app.config.settings import get_settings
from app.modules.conversations.models import Conversation, Message
from app.modules.identity.models import User
from app.shared.database import get_session

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])


class CreateConversation(BaseModel):
    model: str
    title: str = Field(default="Nueva conversación", max_length=240)


class SendMessage(BaseModel):
    content: str = Field(min_length=1, max_length=100000)


def can_access(conversation: Conversation, user: User) -> bool:
    return conversation.owner_user_id == user.id or user.is_system_admin


@router.get("")
async def list_conversations(session: AsyncSession = Depends(get_session), user: User = Depends(require_permission("conversations:read"))) -> dict[str, object]:
    statement = select(Conversation).order_by(Conversation.updated_at.desc())
    if not user.is_system_admin:
        statement = statement.where(Conversation.owner_user_id == user.id)
    conversations = (await session.scalars(statement)).all()
    return {
        "items": [
            {"id": str(item.id), "title": item.title, "model": item.model, "updated_at": item.updated_at.isoformat()}
            for item in conversations
        ]
    }


@router.post("")
async def create_conversation(payload: CreateConversation, session: AsyncSession = Depends(get_session), user: User = Depends(require_permission("conversations:write"))) -> dict[str, str]:
    conversation = Conversation(model=payload.model, title=payload.title, owner_user_id=user.id)
    session.add(conversation)
    await session.commit()
    return {"id": str(conversation.id), "model": conversation.model}


@router.get("/{conversation_id}/messages")
async def list_messages(conversation_id: UUID, session: AsyncSession = Depends(get_session), user: User = Depends(require_permission("conversations:read"))) -> dict[str, object]:
    conversation = await session.get(Conversation, conversation_id)
    if conversation is None or not can_access(conversation, user):
        raise HTTPException(status_code=404, detail="Conversación no encontrada.")
    messages = (await session.scalars(select(Message).where(Message.conversation_id == conversation_id).order_by(Message.sequence))).all()
    return {"items": [{"id": str(message.id), "role": message.role, "content": message.content, "status": message.status} for message in messages]}


@router.post("/{conversation_id}/messages")
async def send_message(
    conversation_id: UUID,
    payload: SendMessage,
    request: Request,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("conversations:write")),
) -> StreamingResponse:
    conversation = await session.get(Conversation, conversation_id)
    if conversation is None or not can_access(conversation, user):
        raise HTTPException(status_code=404, detail="Conversación no encontrada.")
    sequence = (await session.scalar(select(func.coalesce(func.max(Message.sequence), 0)).where(Message.conversation_id == conversation_id))) or 0
    user_message = Message(conversation_id=conversation_id, role="user", content=payload.content, sequence=sequence + 1)
    assistant_message = Message(conversation_id=conversation_id, role="assistant", content="", sequence=sequence + 2, status="streaming")
    session.add_all([user_message, assistant_message])
    await session.commit()

    async def events() -> AsyncIterator[str]:
        history = (await session.scalars(select(Message).where(Message.conversation_id == conversation_id).order_by(Message.sequence))).all()
        request_body = {"model": conversation.model, "messages": [{"role": item.role, "content": item.content} for item in history if item.role == "user"], "stream": True}
        text = ""
        cancelled = False
        try:
            yield f"event: message.started\ndata: {json.dumps({'message_id': str(assistant_message.id)})}\n\n"
            async with httpx.AsyncClient(timeout=300.0) as client:
                async with client.stream("POST", f"{str(get_settings().ollama_base_url).rstrip('/')}/api/chat", json=request_body) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if await request.is_disconnected():
                            cancelled = True
                            break
                        await session.refresh(assistant_message)
                        if assistant_message.status == "cancelled":
                            cancelled = True
                            break
                        if not line:
                            continue
                        data = json.loads(line)
                        delta = data.get("message", {}).get("content", "")
                        if delta:
                            text += delta
                            yield f"event: message.delta\ndata: {json.dumps({'message_id': str(assistant_message.id), 'delta': delta})}\n\n"
                        if data.get("done"):
                            break
            assistant_message.content = text
            assistant_message.status = "cancelled" if cancelled else "complete"
            await session.commit()
            event = "message.cancelled" if cancelled else "message.completed"
            yield f"event: {event}\ndata: {json.dumps({'message_id': str(assistant_message.id)})}\n\n"
        except asyncio.CancelledError:
            assistant_message.content = text
            assistant_message.status = "cancelled"
            await session.commit()
            raise
        except httpx.HTTPError:
            assistant_message.status = "failed"
            await session.commit()
            yield "event: message.failed\ndata: {\"code\": \"provider_unavailable\"}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")


@router.post("/{conversation_id}/messages/{message_id}/cancel")
async def cancel_message(
    conversation_id: UUID,
    message_id: UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("conversations:write")),
) -> dict[str, str]:
    conversation = await session.get(Conversation, conversation_id)
    if conversation is None or not can_access(conversation, user):
        raise HTTPException(status_code=404, detail="Conversación no encontrada.")
    message = await session.get(Message, message_id)
    if message is None or message.conversation_id != conversation_id or message.role != "assistant":
        raise HTTPException(status_code=404, detail="Mensaje no encontrado.")
    if message.status != "streaming":
        raise HTTPException(status_code=409, detail="El mensaje ya no está generándose.")
    message.status = "cancelled"
    await session.commit()
    return {"message_id": str(message.id), "status": message.status}


@router.delete("/{conversation_id}", status_code=204)
async def delete_conversation(conversation_id: UUID, session: AsyncSession = Depends(get_session), user: User = Depends(require_permission("conversations:write"))) -> None:
    conversation = await session.get(Conversation, conversation_id)
    if conversation is None or not can_access(conversation, user):
        raise HTTPException(status_code=404, detail="Conversación no encontrada.")
    await session.delete(conversation)
    await session.commit()
