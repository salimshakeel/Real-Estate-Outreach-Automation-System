"""
Chatbot Router
Endpoints for the AI-powered sales assistant (chatbot)
"""

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ChatbotMessage, Lead
from app.schemas import (
    ChatbotHistoryResponse,
    ChatbotNextAction,
    ChatbotRequest,
    ChatbotResponse,
    ChatMessage,
)
from app.utils.ai_service import ai_service

router = APIRouter()


@router.options("/message")
async def chatbot_message_options() -> Response:
    """Handle CORS preflight for chatbot message endpoint."""
    return Response(status_code=200)


@router.post("/message", response_model=ChatbotResponse)
async def chatbot_message(
    payload: ChatbotRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Main entrypoint for the chatbot.

    - Validates the lead exists
    - Builds minimal lead context
    - Delegates to AI service to generate reply + next action
    """
    # Ensure lead exists
    result = await db.execute(select(Lead).where(Lead.id == payload.lead_id))
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead {payload.lead_id} not found")

    # Build lead context for AI layer
    lead_context = {
        "id": lead.id,
        "first_name": lead.first_name,
        "last_name": lead.last_name,
        "email": lead.email,
        "company": lead.company,
        "status": lead.status,
        "lead_score": payload.lead_score,
        "industry": payload.industry,
        "source": payload.source,
        "last_email_summary": payload.last_email_summary,
    }

    # Delegate to AI service
    ai_result = await ai_service.generate_chatbot_reply(
        lead_context=lead_context,
        messages=[m.model_dump() for m in payload.messages],
    )

    # Map AI result into Pydantic response
    next_action = ChatbotNextAction(
        type=ai_result.get("next_action", {}).get("type", "continue"),
        reason=ai_result.get("next_action", {}).get("reason"),
    )

    response = ChatbotResponse(
        reply=ai_result.get("reply", "Sorry, I couldn't process that. Please try again."),
        next_action=next_action,
        updated_lead_score=ai_result.get("updated_lead_score"),
    )

    # Persist latest user + assistant messages for history (optional, best-effort)
    try:
        # Last user message from payload
        last_user_message = None
        for msg in reversed(payload.messages):
            if msg.role == "user":
                last_user_message = msg
                break

        if last_user_message:
            db.add(
                ChatbotMessage(
                    lead_id=lead.id,
                    role="user",
                    content=last_user_message.content,
                )
            )

        # Assistant reply
        db.add(
            ChatbotMessage(
                lead_id=lead.id,
                role="assistant",
                content=response.reply,
            )
        )

        await db.commit()
    except Exception:
        # We don't want history persistence failures to break the chat flow
        await db.rollback()

    return response


@router.get("/history/{lead_id}", response_model=ChatbotHistoryResponse)
async def get_chatbot_history(
    lead_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get chatbot message history for a specific lead.

    Returns messages ordered from oldest to newest.
    """
    # Ensure lead exists
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead {lead_id} not found")

    # Fetch messages
    msg_result = await db.execute(
        select(ChatbotMessage).where(ChatbotMessage.lead_id == lead_id).order_by(ChatbotMessage.created_at.asc())
    )
    rows = msg_result.scalars().all()

    messages = [ChatMessage(role=row.role, content=row.content) for row in rows]

    return ChatbotHistoryResponse(lead_id=lead_id, messages=messages)
