"""
Leads Router
Endpoints for managing leads (contacts/sellers)
"""

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import AiLeadScore, Campaign, Lead
from app.schemas import (
    AiLeadScoreResponse,
    CSVUploadResponse,
    LeadCreate,
    LeadListResponse,
    LeadResponse,
    LeadScoreBulkRequest,
    LeadScoreBulkResponse,
    LeadScoreRequest,
    LeadScoreResponse,
    LeadScoreResult,
    LeadUpdate,
    MessageResponse,
)
from app.utils.ai_service import score_lead
from app.utils.csv_parser import CSVParser

router = APIRouter()


# ============================================
# STEP 1: CSV UPLOAD ENDPOINT
# ============================================
@router.post("/upload", response_model=CSVUploadResponse)
async def upload_leads_csv(
    file: UploadFile = File(..., description="CSV file with leads"), db: AsyncSession = Depends(get_db)
):
    """
    Upload CSV file to import leads.

    Expected CSV columns:
    - email (required)
    - first_name (required)
    - last_name (optional)
    - phone (optional)
    - address (optional)
    - property_type (optional)
    - estimated_value (optional)
    """
    # Validate file type
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV file")

    # Read file content
    content = await file.read()

    # Parse CSV
    valid_leads, errors = CSVParser.parse(content)

    if not valid_leads and errors:
        return CSVUploadResponse(
            filename=file.filename,
            total_rows=0,
            valid_rows=0,
            invalid_rows=len(errors),
            duplicates=0,
            created=0,
            errors=errors,
        )

    # Insert leads into database
    created = 0
    duplicates = 0

    for lead_data in valid_leads:
        # Check if email already exists
        existing = await db.execute(select(Lead).where(Lead.email == lead_data["email"]))
        if existing.scalar_one_or_none():
            duplicates += 1
            continue

        # Create new lead
        lead = Lead(
            email=lead_data.get("email"),
            first_name=lead_data.get("first_name"),
            last_name=lead_data.get("last_name"),
            company=lead_data.get("company"),
            phone=lead_data.get("phone"),
            address=lead_data.get("address"),
            property_type=lead_data.get("property_type"),
            estimated_value=lead_data.get("estimated_value"),
            status="uploaded",
        )
        db.add(lead)
        created += 1

    # Commit all changes
    await db.commit()

    return CSVUploadResponse(
        filename=file.filename,
        total_rows=len(valid_leads) + len(errors),
        valid_rows=len(valid_leads),
        invalid_rows=len(errors),
        duplicates=duplicates,
        created=created,
        errors=errors,
    )


# ============================================
# STEP 2: VIEW ALL LEADS ENDPOINT
# ============================================
@router.get("", response_model=LeadListResponse)
async def get_leads(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    status: str | None = Query(None, description="Filter by status"),
    search: str | None = Query(None, description="Search by email or name"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all leads with pagination and optional filtering.

    - **page**: Page number (default: 1)
    - **per_page**: Items per page (default: 20, max: 100)
    - **status**: Filter by lead status
    - **search**: Search in email, first_name, last_name
    """
    # Build query
    query = select(Lead)

    # Apply filters
    if status:
        query = query.where(Lead.status == status)

    if search:
        search_term = f"%{search}%"
        query = query.where(
            (Lead.email.ilike(search_term)) | (Lead.first_name.ilike(search_term)) | (Lead.last_name.ilike(search_term))
        )

    # Get total count
    count_query = select(func.count()).select_from(Lead)
    if status:
        count_query = count_query.where(Lead.status == status)
    if search:
        search_term = f"%{search}%"
        count_query = count_query.where(
            (Lead.email.ilike(search_term)) | (Lead.first_name.ilike(search_term)) | (Lead.last_name.ilike(search_term))
        )

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Calculate pagination
    total_pages = (total + per_page - 1) // per_page
    offset = (page - 1) * per_page

    # Apply pagination and ordering
    query = query.order_by(Lead.created_at.desc()).offset(offset).limit(per_page)

    # Execute query
    result = await db.execute(query)
    leads = result.scalars().all()

    return LeadListResponse(
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        items=[LeadResponse.model_validate(lead) for lead in leads],
    )


# ============================================
# STEP 3: GET SINGLE LEAD WITH HISTORY
# ============================================
@router.get("/{lead_id}", response_model=dict)
async def get_lead(lead_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get a single lead with complete history.

    Returns:
    - Lead details
    - Email sequences (emails sent)
    - Replies received
    - Bookings scheduled
    """
    # Get lead with relationships
    query = (
        select(Lead)
        .options(selectinload(Lead.email_sequences), selectinload(Lead.replies), selectinload(Lead.bookings))
        .where(Lead.id == lead_id)
    )

    result = await db.execute(query)
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead with ID {lead_id} not found")

    # Build response with history
    return {
        "lead": LeadResponse.model_validate(lead),
        "email_sequences": [
            {
                "id": es.id,
                "sequence_day": es.sequence_day,
                "email_subject": es.email_subject,
                "status": es.status,
                "sent_at": es.sent_at,
                "opened_at": es.opened_at,
                "clicked_at": es.clicked_at,
                "replied_at": es.replied_at,
            }
            for es in lead.email_sequences
        ],
        "replies": [
            {
                "id": r.id,
                "email_subject": r.email_subject,
                "email_body": r.email_body,
                "sentiment": r.sentiment,
                "confidence_score": float(r.confidence_score) if r.confidence_score else None,
                "received_at": r.received_at,
            }
            for r in lead.replies
        ],
        "bookings": [
            {
                "id": b.id,
                "scheduled_time": b.scheduled_time,
                "calendly_response_status": b.calendly_response_status,
                "created_at": b.created_at,
            }
            for b in lead.bookings
        ],
        "stats": {
            "total_emails_sent": len(lead.email_sequences),
            "total_replies": len(lead.replies),
            "total_bookings": len(lead.bookings),
        },
    }


# ============================================
# LEAD EMAIL HISTORY (for lead detail / communication history)
# ============================================
@router.get("/{lead_id}/emails", response_model=dict)
async def get_lead_email_history(lead_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get all emails sent to this lead (email_sequences) for the lead detail view.
    Returns { items: [...] } so the frontend can show full email history and
    back-and-forth visibility (replies are linked via replied_at on sequences).
    """
    from app.models import EmailSequence

    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead with ID {lead_id} not found")

    result = await db.execute(
        select(EmailSequence).where(EmailSequence.lead_id == lead_id).order_by(EmailSequence.sent_at.asc())
    )
    sequences = result.scalars().all()

    items = [
        {
            "id": es.id,
            "sequence_day": es.sequence_day,
            "email_subject": es.email_subject,
            "email_body": es.email_body,
            "status": es.status,
            "sent_at": es.sent_at,
            "opened_at": es.opened_at,
            "clicked_at": es.clicked_at,
            "replied_at": es.replied_at,
            "bounce_reason": es.bounce_reason,
        }
        for es in sequences
    ]

    return {"items": items}


# ============================================
# UNIFIED COMMUNICATION ACTIVITY (full visibility across channels)
# ============================================
@router.get("/{lead_id}/activity", response_model=dict)
async def get_lead_activity(lead_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get a single chronological timeline of all communication with this lead:
    email sent, email reply, SMS sent, voice call, chatbot message.
    Use this for a unified 'back-and-forth' view in the app.
    """
    from app.models import ChatbotMessage, EmailSequence, Reply, SmsMessage, VoiceCall

    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Lead with ID {lead_id} not found")

    events = []

    # Emails sent
    seq_result = await db.execute(
        select(EmailSequence).where(EmailSequence.lead_id == lead_id).order_by(EmailSequence.sent_at.asc())
    )
    for es in seq_result.scalars().all():
        at = es.sent_at or es.created_at
        if at:
            events.append(
                {
                    "type": "email_sent",
                    "at": at.isoformat(),
                    "id": es.id,
                    "subject": es.email_subject,
                    "body_preview": (es.email_body or "")[:200],
                    "status": es.status,
                }
            )

    # Email replies (inbound)
    reply_result = await db.execute(
        select(Reply).where(Reply.lead_id == lead_id).order_by(Reply.created_at.asc())
    )
    for r in reply_result.scalars().all():
        at = r.received_at or r.created_at
        if at:
            events.append(
                {
                    "type": "email_reply",
                    "at": at.isoformat(),
                    "id": r.id,
                    "subject": r.email_subject,
                    "body_preview": (r.email_body or "")[:200],
                    "sentiment": r.sentiment,
                }
            )

    # SMS sent
    sms_result = await db.execute(
        select(SmsMessage).where(SmsMessage.lead_id == lead_id).order_by(SmsMessage.created_at.asc())
    )
    for m in sms_result.scalars().all():
        at = m.sent_at or m.created_at
        if at:
            events.append(
                {
                    "type": "sms_sent",
                    "at": at.isoformat(),
                    "id": m.id,
                    "body": m.body,
                    "status": m.status,
                }
            )

    # Voice calls
    voice_result = await db.execute(
        select(VoiceCall).where(VoiceCall.lead_id == lead_id).order_by(VoiceCall.created_at.asc())
    )
    for c in voice_result.scalars().all():
        at = c.started_at or c.created_at
        if at:
            events.append(
                {
                    "type": "voice_call",
                    "at": at.isoformat(),
                    "id": c.id,
                    "status": c.status,
                    "duration_seconds": c.duration_seconds,
                    "call_summary": c.call_summary,
                }
            )

    # Chatbot messages (flatten: user + assistant as separate events or pairs)
    chat_result = await db.execute(
        select(ChatbotMessage).where(ChatbotMessage.lead_id == lead_id).order_by(ChatbotMessage.created_at.asc())
    )
    for msg in chat_result.scalars().all():
        events.append(
            {
                "type": "chatbot",
                "at": msg.created_at.isoformat() if msg.created_at else None,
                "id": msg.id,
                "role": msg.role,
                "content_preview": (msg.content or "")[:200],
            }
        )

    events.sort(key=lambda e: e.get("at") or "", reverse=False)

    return {"lead_id": lead_id, "events": events}


# ============================================
# ADDITIONAL ENDPOINTS
# ============================================


@router.post("", response_model=LeadResponse)
async def create_lead(lead_data: LeadCreate, db: AsyncSession = Depends(get_db)):
    """Create a single lead manually"""
    # Check if email already exists
    existing = await db.execute(select(Lead).where(Lead.email == lead_data.email.lower()))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Lead with email {lead_data.email} already exists")

    # Create lead
    lead = Lead(
        email=lead_data.email.lower(),
        first_name=lead_data.first_name,
        last_name=lead_data.last_name,
        company=lead_data.company,
        phone=lead_data.phone,
        address=lead_data.address,
        property_type=lead_data.property_type,
        estimated_value=lead_data.estimated_value,
        notes=lead_data.notes,
        created_by=lead_data.created_by,
        status="uploaded",
    )

    db.add(lead)
    await db.commit()
    await db.refresh(lead)

    return LeadResponse.model_validate(lead)


@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(lead_id: int, lead_data: LeadUpdate, db: AsyncSession = Depends(get_db)):
    """Update a lead"""
    # Get lead
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead with ID {lead_id} not found")

    # Update fields
    update_data = lead_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "email" and value:
            value = value.lower()
        setattr(lead, field, value)

    await db.commit()
    await db.refresh(lead)

    return LeadResponse.model_validate(lead)


@router.delete("/{lead_id}", response_model=MessageResponse)
async def delete_lead(lead_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a lead (and all related records via CASCADE)"""
    # Get lead
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead with ID {lead_id} not found")

    await db.delete(lead)
    await db.commit()

    return MessageResponse(message=f"Lead {lead_id} deleted successfully")


@router.get("/template/csv")
async def get_csv_template():
    """Download a sample CSV template"""
    from fastapi.responses import Response

    csv_content = CSVParser.get_sample_csv()

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads_template.csv"},
    )


@router.post("/score", response_model=LeadScoreResponse)
async def score_single_lead(
    payload: LeadScoreRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Score a single lead using AI.

    The LLM evaluates the lead against the ideal customer profile and returns
    a 0-100 score, priority label, reasoning, and recommended campaign.
    The result is persisted in ai_lead_scores (upsert).
    """
    result = await db.execute(select(Lead).where(Lead.id == payload.lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead {payload.lead_id} not found")

    lead_data = {
        "first_name": lead.first_name,
        "last_name": lead.last_name or "",
        "email": lead.email,
        "company": lead.company or "",
        "phone": lead.phone or "",
        "address": lead.address or "",
        "property_type": lead.property_type or "",
        "estimated_value": lead.estimated_value or "",
        "status": lead.status,
    }

    campaigns_result = await db.execute(
        select(Campaign.name).order_by(Campaign.created_at.desc()).limit(20)
    )
    available_campaigns = [row[0] for row in campaigns_result.fetchall()]

    ai_result = await score_lead(
        lead_data,
        icp_description=payload.icp_description,
        available_campaigns=available_campaigns,
    )

    from datetime import datetime
    existing = await db.execute(
        select(AiLeadScore).where(AiLeadScore.lead_id == lead.id)
    )
    score_row = existing.scalar_one_or_none()

    if score_row:
        score_row.score = ai_result["score"]
        score_row.priority = ai_result["priority"]
        score_row.reasoning = ai_result.get("reasoning")
        score_row.recommended_campaign = ai_result.get("recommended_campaign")
        score_row.personalization_hints = ai_result.get("personalization_hints")
        score_row.scored_at = datetime.utcnow()
    else:
        score_row = AiLeadScore(
            lead_id=lead.id,
            score=ai_result["score"],
            priority=ai_result["priority"],
            reasoning=ai_result.get("reasoning"),
            recommended_campaign=ai_result.get("recommended_campaign"),
            personalization_hints=ai_result.get("personalization_hints"),
            ai_model_used="gpt-4o",
            scored_at=datetime.utcnow(),
        )
        db.add(score_row)

    await db.commit()

    return LeadScoreResponse(
        result=LeadScoreResult(
            lead_id=lead.id,
            score=ai_result["score"],
            priority=ai_result["priority"],
            reasoning=ai_result.get("reasoning", ""),
            recommended_campaign=ai_result.get("recommended_campaign"),
            personalization_hints=ai_result.get("personalization_hints"),
        )
    )


@router.post("/score/bulk", response_model=LeadScoreBulkResponse)
async def score_bulk_leads(
    payload: LeadScoreBulkRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Score multiple leads using AI.

    Iterates through the provided lead IDs, scores each one, and persists
    results. Returns all scoring results in a single response.
    """
    from datetime import datetime

    leads_result = await db.execute(
        select(Lead).where(Lead.id.in_(payload.lead_ids))
    )
    leads = leads_result.scalars().all()

    if not leads:
        raise HTTPException(status_code=400, detail="No valid leads found")

    campaigns_result = await db.execute(
        select(Campaign.name).order_by(Campaign.created_at.desc()).limit(20)
    )
    available_campaigns = [row[0] for row in campaigns_result.fetchall()]

    results = []
    for lead in leads:
        lead_data = {
            "first_name": lead.first_name,
            "last_name": lead.last_name or "",
            "email": lead.email,
            "company": lead.company or "",
            "phone": lead.phone or "",
            "address": lead.address or "",
            "property_type": lead.property_type or "",
            "estimated_value": lead.estimated_value or "",
            "status": lead.status,
        }

        ai_result = await score_lead(
            lead_data,
            icp_description=payload.icp_description,
            available_campaigns=available_campaigns,
        )

        # Upsert
        existing = await db.execute(
            select(AiLeadScore).where(AiLeadScore.lead_id == lead.id)
        )
        score_row = existing.scalar_one_or_none()

        if score_row:
            score_row.score = ai_result["score"]
            score_row.priority = ai_result["priority"]
            score_row.reasoning = ai_result.get("reasoning")
            score_row.recommended_campaign = ai_result.get("recommended_campaign")
            score_row.personalization_hints = ai_result.get("personalization_hints")
            score_row.scored_at = datetime.utcnow()
        else:
            score_row = AiLeadScore(
                lead_id=lead.id,
                score=ai_result["score"],
                priority=ai_result["priority"],
                reasoning=ai_result.get("reasoning"),
                recommended_campaign=ai_result.get("recommended_campaign"),
                personalization_hints=ai_result.get("personalization_hints"),
                ai_model_used="gpt-4o",
                scored_at=datetime.utcnow(),
            )
            db.add(score_row)

        results.append(LeadScoreResult(
            lead_id=lead.id,
            score=ai_result["score"],
            priority=ai_result["priority"],
            reasoning=ai_result.get("reasoning", ""),
            recommended_campaign=ai_result.get("recommended_campaign"),
            personalization_hints=ai_result.get("personalization_hints"),
        ))

    await db.commit()

    return LeadScoreBulkResponse(
        total=len(payload.lead_ids),
        scored=len(results),
        results=results,
    )
