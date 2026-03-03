"""
Voice Router (Step 4)
Endpoints for AI outbound voice calls via Retell AI + Twilio.
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models import Lead, VoiceCall
from app.schemas import (
    VoiceCallDetailResponse,
    VoiceCallHistoryResponse,
    VoiceCallRequest,
    VoiceCallResponse,
)
from app.utils.sms_service import normalize_phone
from app.utils.voice_service import voice_service

settings = get_settings()
router = APIRouter()


@router.post("/call", response_model=VoiceCallResponse)
async def start_voice_call(
    payload: VoiceCallRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Start an outbound AI voice call to a lead.

    - Lead must exist and have a phone number.
    - Retell AI agent handles the conversation.
    - When Retell is not configured, call is logged (mock).
    - dynamic_variables are injected into the agent prompt
      (e.g. {"first_name": "James", "property_address": "120 Maple Drive"}).
    """
    result = await db.execute(select(Lead).where(Lead.id == payload.lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead {payload.lead_id} not found")
    if not lead.phone or not lead.phone.strip():
        raise HTTPException(
            status_code=400,
            detail="Lead has no phone number; add a phone before calling.",
        )

    dynamic_vars = payload.dynamic_variables or {}
    dynamic_vars.setdefault("first_name", lead.first_name or "")
    dynamic_vars.setdefault("last_name", lead.last_name or "")
    dynamic_vars.setdefault("company", lead.company or "")
    dynamic_vars.setdefault("address", lead.address or "")
    dynamic_vars.setdefault("property_type", lead.property_type or "")

    call_result = await voice_service.start_call(
        to_phone=lead.phone,
        lead_id=lead.id,
        dynamic_vars=dynamic_vars,
    )

    status = call_result.get("status", "failed")
    retell_call_id = call_result.get("call_id")
    error = call_result.get("error")
    success = status in ("calling", "mock")

    voice_record = VoiceCall(
        lead_id=lead.id,
        to_number=normalize_phone(lead.phone),
        retell_call_id=retell_call_id,
        retell_agent_id=settings.RETELL_AGENT_ID,
        status="calling" if success else "failed",
        started_at=datetime.utcnow() if success else None,
    )
    db.add(voice_record)
    await db.commit()
    await db.refresh(voice_record)

    return VoiceCallResponse(
        success=success,
        lead_id=lead.id,
        voice_call_id=voice_record.id,
        retell_call_id=retell_call_id,
        status=status,
        error=error,
        message="Call initiated" if success else (error or "Call failed"),
    )


@router.get("/history/{lead_id}", response_model=VoiceCallHistoryResponse)
async def get_voice_history(
    lead_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Return all voice calls for this lead, newest first."""
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Lead {lead_id} not found")

    result = await db.execute(
        select(VoiceCall).where(VoiceCall.lead_id == lead_id).order_by(VoiceCall.created_at.desc())
    )
    calls = result.scalars().all()

    return VoiceCallHistoryResponse(
        lead_id=lead_id,
        calls=[VoiceCallDetailResponse.model_validate(c) for c in calls],
    )


@router.get("/call/{call_id}", response_model=VoiceCallDetailResponse)
async def get_voice_call(
    call_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a single voice call record by DB id."""
    result = await db.execute(select(VoiceCall).where(VoiceCall.id == call_id))
    call = result.scalar_one_or_none()
    if not call:
        raise HTTPException(status_code=404, detail=f"Voice call {call_id} not found")
    return VoiceCallDetailResponse.model_validate(call)


# ============================================
# RETELL WEBHOOK — receives call events
# ============================================


@router.post("/webhook/retell")
async def retell_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Retell sends POST events here when a call ends or is analyzed.

    Event types handled:
      - call_ended: update status, duration, ended_at
      - call_analyzed: update transcript, summary, recording_url, outcome

    Set this URL in your Retell dashboard under Agent → Webhook.
    """
    try:
        body: dict[str, Any] = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event = body.get("event")
    call_data = body.get("call", body.get("data", body))
    retell_call_id = call_data.get("call_id")

    if not retell_call_id:
        return {"status": "ignored", "reason": "no call_id"}

    result = await db.execute(select(VoiceCall).where(VoiceCall.retell_call_id == retell_call_id))
    voice_call = result.scalar_one_or_none()
    if not voice_call:
        return {"status": "ignored", "reason": "call_id not found in DB"}

    if event == "call_ended":
        voice_call.status = _map_retell_status(call_data.get("call_status"))
        voice_call.ended_at = datetime.utcnow()
        duration_ms = call_data.get("duration_ms") or call_data.get("call_duration_ms")
        if duration_ms:
            voice_call.duration_seconds = int(duration_ms / 1000)

    if event in ("call_analyzed", "call_ended"):
        voice_call.transcript = call_data.get("transcript")
        voice_call.recording_url = call_data.get("recording_url")
        voice_call.call_summary = call_data.get("call_analysis", {}).get("call_summary") or call_data.get(
            "call_summary"
        )
        outcome = call_data.get("call_analysis", {}).get("custom_analysis_data", {}).get("outcome") or call_data.get(
            "call_analysis", {}
        ).get("user_sentiment")
        if outcome:
            voice_call.call_outcome = _map_outcome(outcome)

    await db.commit()
    return {"status": "ok", "event": event, "call_id": retell_call_id}


def _map_retell_status(retell_status: str | None) -> str:
    mapping = {
        "ended": "completed",
        "error": "failed",
        "busy": "busy",
        "no_answer": "no_answer",
        "voicemail": "voicemail",
        "in_progress": "in_progress",
    }
    return mapping.get(retell_status or "", "completed")


def _map_outcome(raw: str | None) -> str | None:
    if not raw:
        return None
    r = raw.lower()
    if any(w in r for w in ["book", "schedul", "demo", "meeting"]):
        return "booked"
    if any(w in r for w in ["interest", "positive"]):
        return "interested"
    if any(w in r for w in ["not interest", "negative", "no"]):
        return "not_interested"
    if any(w in r for w in ["callback", "call back", "later"]):
        return "callback"
    if "voicemail" in r:
        return "voicemail"
    return "no_outcome"
