"""
SMS Router (Step 3)
Endpoints for sending SMS to leads via Twilio.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Lead, SmsMessage
from app.schemas import (
    SmsHistoryResponse,
    SmsMessageResponse,
    SmsSendRequest,
    SmsSendResponse,
)
from app.utils.sms_service import personalize_body, sms_service

router = APIRouter()


@router.post("/send", response_model=SmsSendResponse)
async def send_sms_to_lead(
    payload: SmsSendRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Send an SMS to a lead's phone number.

    - Lead must exist and have a phone number.
    - If personalize=True, body can use {{first_name}}, {{lead_id}}, etc.
    - When Twilio is not configured, message is logged (mock) and stored as status=mock.
    """
    result = await db.execute(select(Lead).where(Lead.id == payload.lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead {payload.lead_id} not found")
    if not lead.phone or not lead.phone.strip():
        raise HTTPException(
            status_code=400,
            detail="Lead has no phone number; add a phone before sending SMS.",
        )

    body = payload.body
    if payload.personalize:
        lead_data = {
            "lead_id": lead.id,
            "first_name": lead.first_name or "",
            "last_name": lead.last_name or "",
            "email": lead.email or "",
            "phone": lead.phone or "",
            "address": lead.address or "",
            "property_type": lead.property_type or "",
            "estimated_value": lead.estimated_value or "",
        }
        body = personalize_body(body, lead_data)

    send_result = await sms_service.send_sms(
        to_phone=lead.phone,
        body=body,
        lead_id=lead.id,
    )

    status = send_result.get("status", "failed")
    twilio_sid = send_result.get("sid")
    error = send_result.get("error")
    success = status in ("sent", "mock")

    # Persist to DB for history and optional status callbacks
    sms_record = SmsMessage(
        lead_id=lead.id,
        to_number=lead.phone,
        body=body,
        status="sent" if success else "failed",
        twilio_sid=twilio_sid,
        sent_at=datetime.utcnow() if success else None,
    )
    db.add(sms_record)
    await db.commit()
    await db.refresh(sms_record)

    return SmsSendResponse(
        success=success,
        lead_id=lead.id,
        sms_message_id=sms_record.id,
        twilio_sid=twilio_sid,
        status=status,
        error=error,
        message="SMS sent" if success else (error or "SMS failed"),
    )


@router.get("/history/{lead_id}", response_model=SmsHistoryResponse)
async def get_sms_history(
    lead_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Return all SMS messages sent to this lead, oldest first."""
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead {lead_id} not found")

    result = await db.execute(
        select(SmsMessage).where(SmsMessage.lead_id == lead_id).order_by(SmsMessage.created_at.asc())
    )
    messages = result.scalars().all()

    return SmsHistoryResponse(
        lead_id=lead_id,
        messages=[SmsMessageResponse.model_validate(m) for m in messages],
    )
