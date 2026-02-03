"""
Demo Router
Endpoints for simulating events during demos (open, reply, booking)
These endpoints are for DEMO/TESTING purposes only.
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models import Lead, EmailSequence, Reply, Booking, Campaign, EmailTemplate

router = APIRouter()


# ============================================
# REQUEST SCHEMAS
# ============================================

class SimulateOpenRequest(BaseModel):
    lead_id: int


class SimulateReplyRequest(BaseModel):
    lead_id: int
    sentiment: str = "interested"  # interested, not_now, unsubscribe, other
    reply_text: Optional[str] = None


class SimulateBookingRequest(BaseModel):
    lead_id: int
    days_from_now: int = 3  # Schedule meeting X days from now


# ============================================
# SIMULATE EMAIL OPEN
# ============================================
@router.post("/simulate/open")
async def simulate_email_open(
    request: SimulateOpenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Simulate an email being opened by a lead.
    Updates the most recent email sequence for this lead.
    """
    # Get lead
    lead_result = await db.execute(
        select(Lead).where(Lead.id == request.lead_id)
    )
    lead = lead_result.scalar_one_or_none()
    
    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead {request.lead_id} not found")
    
    # Get most recent email sequence for this lead
    seq_result = await db.execute(
        select(EmailSequence)
        .where(EmailSequence.lead_id == request.lead_id)
        .order_by(EmailSequence.created_at.desc())
        .limit(1)
    )
    sequence = seq_result.scalar_one_or_none()
    
    if not sequence:
        raise HTTPException(
            status_code=400, 
            detail=f"No email sequence found for lead {request.lead_id}. Send an email first."
        )
    
    # Update sequence
    sequence.opened_at = datetime.utcnow()
    sequence.status = "opened"
    
    await db.commit()
    
    return {
        "success": True,
        "message": f"Simulated email open for {lead.first_name} {lead.last_name or ''}",
        "lead_id": lead.id,
        "email_sequence_id": sequence.id,
        "opened_at": sequence.opened_at
    }


# ============================================
# SIMULATE EMAIL REPLY
# ============================================
@router.post("/simulate/reply")
async def simulate_email_reply(
    request: SimulateReplyRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Simulate a lead replying to an email.
    Creates a Reply record and updates lead status.
    """
    # Validate sentiment
    valid_sentiments = ["interested", "not_now", "unsubscribe", "other"]
    if request.sentiment not in valid_sentiments:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sentiment. Must be one of: {valid_sentiments}"
        )
    
    # Get lead
    lead_result = await db.execute(
        select(Lead).where(Lead.id == request.lead_id)
    )
    lead = lead_result.scalar_one_or_none()
    
    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead {request.lead_id} not found")
    
    # Get most recent email sequence
    seq_result = await db.execute(
        select(EmailSequence)
        .where(EmailSequence.lead_id == request.lead_id)
        .order_by(EmailSequence.created_at.desc())
        .limit(1)
    )
    sequence = seq_result.scalar_one_or_none()
    
    # Update sequence if exists
    if sequence:
        sequence.replied_at = datetime.utcnow()
        sequence.status = "replied"
    
    # Create reply record
    reply_texts = {
        "interested": "Yes, I'm interested! When can we schedule a call?",
        "not_now": "Thanks for reaching out, but now isn't a good time. Maybe later.",
        "unsubscribe": "Please remove me from your mailing list.",
        "other": "Thanks for the email. I have some questions."
    }
    
    reply = Reply(
        lead_id=lead.id,
        email_from=lead.email,
        email_subject=f"Re: {sequence.email_subject if sequence else 'Your email'}",
        email_body=request.reply_text or reply_texts.get(request.sentiment, "Thanks for the email."),
        sentiment=request.sentiment,
        confidence_score=0.95,  # High confidence for simulated replies
        ai_model_used="demo_simulation",
        received_at=datetime.utcnow(),
        processed_at=datetime.utcnow()
    )
    db.add(reply)
    
    # Update lead status based on sentiment
    status_map = {
        "interested": "interested",
        "not_now": "replied",
        "unsubscribe": "closed",
        "other": "replied"
    }
    lead.status = status_map.get(request.sentiment, "replied")
    
    await db.commit()
    await db.refresh(reply)
    
    return {
        "success": True,
        "message": f"Simulated {request.sentiment} reply from {lead.first_name}",
        "lead_id": lead.id,
        "lead_status": lead.status,
        "reply_id": reply.id,
        "sentiment": request.sentiment
    }


# ============================================
# SIMULATE BOOKING
# ============================================
@router.post("/simulate/booking")
async def simulate_booking(
    request: SimulateBookingRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Simulate a lead booking a meeting (Calendly-style).
    Creates a Booking record and updates lead status to 'booked'.
    """
    # Get lead
    lead_result = await db.execute(
        select(Lead).where(Lead.id == request.lead_id)
    )
    lead = lead_result.scalar_one_or_none()
    
    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead {request.lead_id} not found")
    
    # Calculate scheduled time
    scheduled_time = datetime.utcnow() + timedelta(days=request.days_from_now)
    # Round to nearest hour at 2 PM
    scheduled_time = scheduled_time.replace(hour=14, minute=0, second=0, microsecond=0)
    
    # Create booking
    booking = Booking(
        lead_id=lead.id,
        calendly_event_id=f"demo_evt_{lead.id}_{int(datetime.utcnow().timestamp())}",
        event_uri=f"https://calendly.com/demo/event/{lead.id}",
        scheduled_time=scheduled_time,
        calendly_invitee_email=lead.email,
        calendly_response_status="confirmed"
    )
    db.add(booking)
    
    # Update lead status
    lead.status = "booked"
    
    await db.commit()
    await db.refresh(booking)
    
    return {
        "success": True,
        "message": f"Simulated booking for {lead.first_name} on {scheduled_time.strftime('%B %d at %I:%M %p')}",
        "lead_id": lead.id,
        "lead_status": lead.status,
        "booking_id": booking.id,
        "scheduled_time": scheduled_time
    }


# ============================================
# RESET DEMO DATA
# ============================================
@router.post("/reset")
async def reset_demo_data(
    confirm: bool = Query(False, description="Set to true to confirm deletion"),
    db: AsyncSession = Depends(get_db)
):
    """
    Reset all demo data. Deletes all leads, campaigns, templates, etc.
    
    ⚠️ WARNING: This deletes ALL data!
    
    Requires confirm=true parameter for safety.
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="This will delete ALL data. Add ?confirm=true to proceed."
        )
    
    try:
        # Delete in correct order (respect foreign keys)
        await db.execute(delete(Booking))
        await db.execute(delete(Reply))
        await db.execute(delete(EmailSequence))
        await db.execute(delete(Lead))
        await db.execute(delete(Campaign))
        await db.execute(delete(EmailTemplate))
        
        await db.commit()
        
        return {
            "success": True,
            "message": "All demo data has been reset. Upload new leads to start fresh."
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")


# ============================================
# SEED DEMO DATA
# ============================================
@router.post("/seed")
async def seed_demo_data(db: AsyncSession = Depends(get_db)):
    """
    Seed the database with sample demo data.
    Creates sample leads, templates, and a campaign.
    """
    # Check if data already exists
    existing_leads = await db.execute(
        select(func.count()).select_from(Lead)
    )
    if existing_leads.scalar() > 0:
        raise HTTPException(
            status_code=400,
            detail="Data already exists. Use /reset?confirm=true first to clear data."
        )
    
    try:
        # Create sample leads
        sample_leads = [
            Lead(email="john.smith@example.com", first_name="John", last_name="Smith", 
                 address="123 Oak Street, Miami FL", property_type="Single Family", 
                 estimated_value="$450,000", status="uploaded"),
            Lead(email="sarah.jones@example.com", first_name="Sarah", last_name="Jones",
                 address="456 Palm Ave, Fort Lauderdale FL", property_type="Condo",
                 estimated_value="$320,000", status="uploaded"),
            Lead(email="mike.wilson@example.com", first_name="Mike", last_name="Wilson",
                 address="789 Beach Blvd, Miami Beach FL", property_type="Townhouse",
                 estimated_value="$580,000", status="uploaded"),
            Lead(email="emma.davis@example.com", first_name="Emma", last_name="Davis",
                 address="321 Sunset Dr, Coral Gables FL", property_type="Single Family",
                 estimated_value="$720,000", status="uploaded"),
            Lead(email="david.brown@example.com", first_name="David", last_name="Brown",
                 address="654 Ocean View, Key Biscayne FL", property_type="Condo",
                 estimated_value="$890,000", status="uploaded"),
        ]
        
        for lead in sample_leads:
            db.add(lead)
        
        # Create default template
        template = EmailTemplate(
            name="Initial Outreach",
            subject="Quick question about {{address}}",
            body="""Hi {{first_name}},

I noticed your property at {{address}} and wanted to reach out.

I work with homeowners in your area and have helped many achieve great results when selling their properties.

Would you be open to a quick 10-minute call to discuss your options? No pressure at all.

Best regards,
Your Real Estate Team""",
            is_default=True
        )
        db.add(template)
        
        # Create a draft campaign
        campaign = Campaign(
            name="Q1 2026 Miami Outreach",
            description="Initial outreach to Miami-area property owners",
            status="draft"
        )
        db.add(campaign)
        
        await db.commit()
        
        return {
            "success": True,
            "message": "Demo data seeded successfully",
            "data": {
                "leads_created": len(sample_leads),
                "templates_created": 1,
                "campaigns_created": 1
            }
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Seed failed: {str(e)}")
