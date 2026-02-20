

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, Integer

from app.database import get_db
from app.models import Campaign, Lead, EmailSequence, EmailTemplate
from app.schemas import (
    CampaignCreate, CampaignUpdate, CampaignResponse,
    CampaignListResponse, CampaignStartRequest, MessageResponse,
    EmailSequenceResponse
)
from app.utils.email_service import email_service, EmailService

router = APIRouter()


# ============================================
# CREATE CAMPAIGN
# ============================================
@router.post("", response_model=CampaignResponse)
async def create_campaign(
    campaign_data: CampaignCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new campaign (draft status).
    
    Campaigns are containers for organized email outreach.
    After creating, you can start it with selected leads.
    """
    campaign = Campaign(
        name=campaign_data.name,
        description=campaign_data.description,
        email_template=campaign_data.email_template,
        status="draft",
        created_by=campaign_data.created_by
    )
    
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    
    return CampaignResponse.model_validate(campaign)


# ============================================
# GET ALL CAMPAIGNS
# ============================================
@router.get("", response_model=CampaignListResponse)
async def get_campaigns(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, pattern="^(draft|scheduled|active|completed|paused)$"),
    search: Optional[str] = Query(None, description="Search by name"),
    db: AsyncSession = Depends(get_db)
):
    """Get all campaigns with pagination and filters"""
    
    # Build query
    query = select(Campaign)
    
    if status:
        query = query.where(Campaign.status == status)
    
    if search:
        query = query.where(Campaign.name.ilike(f"%{search}%"))
    
    # Get total count
    count_query = select(func.count()).select_from(Campaign)
    if status:
        count_query = count_query.where(Campaign.status == status)
    if search:
        count_query = count_query.where(Campaign.name.ilike(f"%{search}%"))
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Pagination
    total_pages = (total + per_page - 1) // per_page
    offset = (page - 1) * per_page
    
    query = query.order_by(Campaign.created_at.desc()).offset(offset).limit(per_page)
    
    result = await db.execute(query)
    campaigns = result.scalars().all()
    
    return CampaignListResponse(
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        items=[CampaignResponse.model_validate(c) for c in campaigns]
    )


# ============================================
# GET SINGLE CAMPAIGN WITH STATS
# ============================================
@router.get("/{campaign_id}", response_model=dict)
async def get_campaign(
    campaign_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get campaign details with statistics.
    
    Returns campaign info plus:
    - Number of leads in campaign
    - Emails sent, opened, replied, bounced
    - Success rates
    """
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()
    
    if not campaign:
        raise HTTPException(
            status_code=404,
            detail=f"Campaign with ID {campaign_id} not found"
        )
    
    # Get campaign statistics from email_sequences
    # Note: We track campaign membership through a naming convention in email_subject
    # In production, you'd add a campaign_id FK to EmailSequence
    
    # For now, get all sequences created around campaign start time
    stats_query = select(
        func.count(EmailSequence.id).label("total_emails"),
        func.sum(func.cast(EmailSequence.status == 'sent', Integer)).label("sent"),
        func.sum(func.cast(EmailSequence.status == 'opened', Integer)).label("opened"),
        func.sum(func.cast(EmailSequence.status == 'replied', Integer)).label("replied"),
        func.sum(func.cast(EmailSequence.status == 'bounced', Integer)).label("bounced"),
    )
    
    # For demo, we'll return placeholder stats
    # In production, link EmailSequence to Campaign with FK
    
    return {
        "campaign": CampaignResponse.model_validate(campaign),
        "stats": {
            "total_leads": 0,
            "emails_sent": 0,
            "emails_opened": 0,
            "emails_replied": 0,
            "emails_bounced": 0,
            "open_rate": 0.0,
            "reply_rate": 0.0
        }
    }


# ============================================
# UPDATE CAMPAIGN
# ============================================
@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: int,
    campaign_data: CampaignUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update campaign details"""
    
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()
    
    if not campaign:
        raise HTTPException(
            status_code=404,
            detail=f"Campaign with ID {campaign_id} not found"
        )
    
    # Don't allow status change on active campaigns via this endpoint
    if campaign_data.status and campaign.status == "active":
        raise HTTPException(
            status_code=400,
            detail="Use /pause or /complete endpoints to change active campaign status"
        )
    
    # Update fields
    update_data = campaign_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(campaign, field, value)
    
    await db.commit()
    await db.refresh(campaign)
    
    return CampaignResponse.model_validate(campaign)


# ============================================
# DELETE CAMPAIGN
# ============================================
@router.delete("/{campaign_id}", response_model=MessageResponse)
async def delete_campaign(
    campaign_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a campaign (only if draft or paused)"""
    
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()
    
    if not campaign:
        raise HTTPException(
            status_code=404,
            detail=f"Campaign with ID {campaign_id} not found"
        )
    
    if campaign.status == "active":
        raise HTTPException(
            status_code=400,
            detail="Cannot delete active campaign. Pause it first."
        )
    
    name = campaign.name
    await db.delete(campaign)
    await db.commit()
    
    return MessageResponse(message=f"Campaign '{name}' deleted successfully")


# ============================================
# START CAMPAIGN (SEND EMAILS TO LEADS)
# ============================================
@router.post("/{campaign_id}/start", response_model=dict)
async def start_campaign(
    campaign_id: int,
    request: CampaignStartRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Start a campaign by sending emails to selected leads.
    
    - Provide lead_ids to target
    - Optionally provide email_template_id OR custom subject/body
    - Creates EmailSequence records for tracking
    - Sends emails (mock in demo, SendGrid in production)
    """
    # Get campaign
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()
    
    if not campaign:
        raise HTTPException(
            status_code=404,
            detail=f"Campaign with ID {campaign_id} not found"
        )
    
    if campaign.status == "active":
        raise HTTPException(
            status_code=400,
            detail="Campaign is already active"
        )
    
    # Get email template
    subject = request.subject
    body = request.body
    
    if request.email_template_id:
        template_result = await db.execute(
            select(EmailTemplate).where(EmailTemplate.id == request.email_template_id)
        )
        template = template_result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(
                status_code=404,
                detail=f"Email template with ID {request.email_template_id} not found"
            )
        
        subject = template.subject
        body = template.body
    
    if not subject or not body:
        raise HTTPException(
            status_code=400,
            detail="Provide email_template_id OR both subject and body"
        )
    
    # Get leads
    leads_result = await db.execute(
        select(Lead).where(Lead.id.in_(request.lead_ids))
    )
    leads = leads_result.scalars().all()
    
    if not leads:
        raise HTTPException(
            status_code=400,
            detail="No valid leads found with provided IDs"
        )
    
    # Update campaign status
    campaign.status = "active"
    campaign.started_at = datetime.utcnow()
    
    # Store template in campaign
    campaign.email_template = f"Subject: {subject}\n\n{body}"
    
    # Process each lead
    results = {
        "campaign_id": campaign_id,
        "total_leads": len(leads),
        "emails_sent": 0,
        "emails_failed": 0,
        "details": []
    }
    
    for lead in leads:
        # Convert lead to dict for personalization
        lead_data = {
            "lead_id": lead.id,
            "first_name": lead.first_name,
            "last_name": lead.last_name or "",
            "email": lead.email,
            "phone": lead.phone or "",
            "address": lead.address or "",
            "property_type": lead.property_type or "",
            "estimated_value": lead.estimated_value or ""
        }
        
        # Personalize subject and body
        personalized_subject = EmailService.personalize_template(subject, lead_data)
        personalized_body = EmailService.personalize_template(body, lead_data)
        
        # Create email sequence record FIRST so we have an ID for tracking
        email_sequence = EmailSequence(
            lead_id=lead.id,
            sequence_day=1,
            email_subject=personalized_subject,
            email_body=personalized_body,
            status="pending",   # Will be updated to "sent" by send_campaign_email()
        )
        db.add(email_sequence)
        await db.flush()  # Gets us the sequence.id without committing the transaction
        
        # Send email — saves message_id back to the sequence row automatically
        # This is what makes webhook event tracking work.
        send_result = await email_service.send_campaign_email(
            to_email=lead.email,
            subject=personalized_subject,
            body=personalized_body,
            sequence_id=email_sequence.id,  # Links the message_id back to this row
            db=db
        )
        
        # Update sequence status if send failed
        if not send_result.get("success"):
            email_sequence.status = "bounced"
            email_sequence.bounce_reason = send_result.get("error", "Send failed")[:255]
        
        # Update lead status
        if send_result.get("success"):
            lead.status = "contacted"
            results["emails_sent"] += 1
        else:
            results["emails_failed"] += 1
        
        results["details"].append({
            "lead_id": lead.id,
            "email": lead.email,
            "success": send_result.get("success"),
            "message_id": send_result.get("message_id"),
            "error": send_result.get("error")
        })
    
    await db.commit()
    await db.refresh(campaign)
    
    results["campaign"] = CampaignResponse.model_validate(campaign).model_dump()
    
    return results


# ============================================
# PAUSE CAMPAIGN
# ============================================
@router.post("/{campaign_id}/pause", response_model=CampaignResponse)
async def pause_campaign(
    campaign_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Pause an active campaign"""
    
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()
    
    if not campaign:
        raise HTTPException(
            status_code=404,
            detail=f"Campaign with ID {campaign_id} not found"
        )
    
    if campaign.status != "active":
        raise HTTPException(
            status_code=400,
            detail=f"Campaign is not active (current status: {campaign.status})"
        )
    
    campaign.status = "paused"
    await db.commit()
    await db.refresh(campaign)
    
    return CampaignResponse.model_validate(campaign)


# ============================================
# COMPLETE CAMPAIGN
# ============================================
@router.post("/{campaign_id}/complete", response_model=CampaignResponse)
async def complete_campaign(
    campaign_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Mark a campaign as completed"""
    
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()
    
    if not campaign:
        raise HTTPException(
            status_code=404,
            detail=f"Campaign with ID {campaign_id} not found"
        )
    
    campaign.status = "completed"
    campaign.ended_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(campaign)
    
    return CampaignResponse.model_validate(campaign)


# ============================================
# RESUME CAMPAIGN
# ============================================
@router.post("/{campaign_id}/resume", response_model=CampaignResponse)
async def resume_campaign(
    campaign_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Resume a paused campaign"""
    
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()
    
    if not campaign:
        raise HTTPException(
            status_code=404,
            detail=f"Campaign with ID {campaign_id} not found"
        )
    
    if campaign.status != "paused":
        raise HTTPException(
            status_code=400,
            detail=f"Campaign is not paused (current status: {campaign.status})"
        )
    
    campaign.status = "active"
    await db.commit()
    await db.refresh(campaign)
    
    return CampaignResponse.model_validate(campaign)


# ============================================
# GET CAMPAIGN EMAIL HISTORY
# ============================================
@router.get("/{campaign_id}/emails", response_model=dict)
async def get_campaign_emails(
    campaign_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None, pattern="^(pending|scheduled|sent|opened|replied|bounced)$"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all emails sent as part of this campaign.
    
    For demo: Returns emails sent around campaign start time.
    For production: Would use campaign_id FK in EmailSequence.
    """
    # Verify campaign exists
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()
    
    if not campaign:
        raise HTTPException(
            status_code=404,
            detail=f"Campaign with ID {campaign_id} not found"
        )
    
    # For demo, get emails sent after campaign started
    # In production, use FK relationship
    query = select(EmailSequence)
    
    if campaign.started_at:
        query = query.where(EmailSequence.created_at >= campaign.started_at)
    
    if status:
        query = query.where(EmailSequence.status == status)
    
    # Pagination
    offset = (page - 1) * per_page
    query = query.order_by(EmailSequence.created_at.desc()).offset(offset).limit(per_page)
    
    result = await db.execute(query)
    sequences = result.scalars().all()
    
    # Get leads for context
    lead_ids = [s.lead_id for s in sequences]
    leads_result = await db.execute(
        select(Lead).where(Lead.id.in_(lead_ids))
    )
    leads_map = {l.id: l for l in leads_result.scalars().all()}
    
    emails = []
    for seq in sequences:
        lead = leads_map.get(seq.lead_id)
        emails.append({
            "id": seq.id,
            "lead_id": seq.lead_id,
            "lead_name": f"{lead.first_name} {lead.last_name or ''}".strip() if lead else "Unknown",
            "lead_email": lead.email if lead else "Unknown",
            "subject": seq.email_subject,
            "status": seq.status,
            "sent_at": seq.sent_at,
            "opened_at": seq.opened_at,
            "replied_at": seq.replied_at
        })
    
    return {
        "campaign": CampaignResponse.model_validate(campaign).model_dump(),
        "page": page,
        "per_page": per_page,
        "emails": emails
    }


# ============================================
# QUICK START: CREATE AND SEND IN ONE STEP
# ============================================
@router.post("/quick-start", response_model=dict)
async def quick_start_campaign(
    name: str = Query(..., description="Campaign name"),
    lead_ids: str = Query(..., description="Comma-separated lead IDs"),
    template_id: Optional[int] = Query(None, description="Email template ID"),
    subject: Optional[str] = Query(None, description="Custom subject (if no template)"),
    body: Optional[str] = Query(None, description="Custom body (if no template)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Quick start a campaign in one API call.
    
    1. Creates campaign
    2. Starts sending immediately
    3. Returns results
    
    Perfect for demo/testing!
    """
    # Create campaign
    campaign = Campaign(
        name=name,
        status="draft"
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    
    # Parse lead IDs
    try:
        parsed_lead_ids = [int(x.strip()) for x in lead_ids.split(",")]
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid lead_ids format. Use comma-separated integers."
        )
    
    # Build start request
    start_request = CampaignStartRequest(
        lead_ids=parsed_lead_ids,
        email_template_id=template_id,
        subject=subject,
        body=body
    )
    
    # Start campaign
    return await start_campaign(campaign.id, start_request, db)
