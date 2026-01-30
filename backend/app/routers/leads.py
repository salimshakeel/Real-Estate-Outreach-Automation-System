"""
Leads Router
Endpoints for managing leads (contacts/sellers)
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Lead, EmailSequence, Reply, Booking
from app.schemas import (
    LeadCreate, LeadUpdate, LeadResponse, LeadListResponse,
    LeadBulkResponse, CSVUploadResponse, MessageResponse
)
from app.utils.csv_parser import CSVParser

router = APIRouter()


# ============================================
# STEP 1: CSV UPLOAD ENDPOINT
# ============================================
@router.post("/upload", response_model=CSVUploadResponse)
async def upload_leads_csv(
    file: UploadFile = File(..., description="CSV file with leads"),
    db: AsyncSession = Depends(get_db)
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
        raise HTTPException(
            status_code=400,
            detail="File must be a CSV file"
        )
    
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
            errors=errors
        )
    
    # Insert leads into database
    created = 0
    duplicates = 0
    
    for lead_data in valid_leads:
        # Check if email already exists
        existing = await db.execute(
            select(Lead).where(Lead.email == lead_data["email"])
        )
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
            status="uploaded"
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
        errors=errors
    )


# ============================================
# STEP 2: VIEW ALL LEADS ENDPOINT
# ============================================
@router.get("", response_model=LeadListResponse)
async def get_leads(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search by email or name"),
    db: AsyncSession = Depends(get_db)
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
            (Lead.email.ilike(search_term)) |
            (Lead.first_name.ilike(search_term)) |
            (Lead.last_name.ilike(search_term))
        )
    
    # Get total count
    count_query = select(func.count()).select_from(Lead)
    if status:
        count_query = count_query.where(Lead.status == status)
    if search:
        search_term = f"%{search}%"
        count_query = count_query.where(
            (Lead.email.ilike(search_term)) |
            (Lead.first_name.ilike(search_term)) |
            (Lead.last_name.ilike(search_term))
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
        items=[LeadResponse.model_validate(lead) for lead in leads]
    )


# ============================================
# STEP 3: GET SINGLE LEAD WITH HISTORY
# ============================================
@router.get("/{lead_id}", response_model=dict)
async def get_lead(
    lead_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a single lead with complete history.
    
    Returns:
    - Lead details
    - Email sequences (emails sent)
    - Replies received
    - Bookings scheduled
    """
    # Get lead with relationships
    query = select(Lead).options(
        selectinload(Lead.email_sequences),
        selectinload(Lead.replies),
        selectinload(Lead.bookings)
    ).where(Lead.id == lead_id)
    
    result = await db.execute(query)
    lead = result.scalar_one_or_none()
    
    if not lead:
        raise HTTPException(
            status_code=404,
            detail=f"Lead with ID {lead_id} not found"
        )
    
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
                "replied_at": es.replied_at
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
                "received_at": r.received_at
            }
            for r in lead.replies
        ],
        "bookings": [
            {
                "id": b.id,
                "scheduled_time": b.scheduled_time,
                "calendly_response_status": b.calendly_response_status,
                "created_at": b.created_at
            }
            for b in lead.bookings
        ],
        "stats": {
            "total_emails_sent": len(lead.email_sequences),
            "total_replies": len(lead.replies),
            "total_bookings": len(lead.bookings)
        }
    }


# ============================================
# ADDITIONAL ENDPOINTS
# ============================================

@router.post("", response_model=LeadResponse)
async def create_lead(
    lead_data: LeadCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a single lead manually"""
    # Check if email already exists
    existing = await db.execute(
        select(Lead).where(Lead.email == lead_data.email.lower())
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"Lead with email {lead_data.email} already exists"
        )
    
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
        status="uploaded"
    )
    
    db.add(lead)
    await db.commit()
    await db.refresh(lead)
    
    return LeadResponse.model_validate(lead)


@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: int,
    lead_data: LeadUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a lead"""
    # Get lead
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    
    if not lead:
        raise HTTPException(
            status_code=404,
            detail=f"Lead with ID {lead_id} not found"
        )
    
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
async def delete_lead(
    lead_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a lead (and all related records via CASCADE)"""
    # Get lead
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    
    if not lead:
        raise HTTPException(
            status_code=404,
            detail=f"Lead with ID {lead_id} not found"
        )
    
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
        headers={
            "Content-Disposition": "attachment; filename=leads_template.csv"
        }
    )
