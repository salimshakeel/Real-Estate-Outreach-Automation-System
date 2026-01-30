"""
Email Templates Router
Endpoints for managing email templates
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models import EmailTemplate
from app.schemas import (
    EmailTemplateCreate, EmailTemplateUpdate, EmailTemplateResponse,
    EmailTemplateListResponse, MessageResponse
)
from app.utils.email_service import EmailService

router = APIRouter()


# ============================================
# CREATE TEMPLATE
# ============================================
@router.post("", response_model=EmailTemplateResponse)
async def create_template(
    template_data: EmailTemplateCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new email template.
    
    Use {{placeholders}} for personalization:
    - {{first_name}}, {{last_name}}, {{full_name}}
    - {{email}}, {{phone}}
    - {{address}}, {{property_type}}, {{estimated_value}}
    """
    # Check if name already exists
    existing = await db.execute(
        select(EmailTemplate).where(EmailTemplate.name == template_data.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"Template with name '{template_data.name}' already exists"
        )
    
    # If setting as default, unset other defaults
    if template_data.is_default:
        await db.execute(
            select(EmailTemplate).where(EmailTemplate.is_default == True)
        )
        # Update all to non-default
        result = await db.execute(select(EmailTemplate).where(EmailTemplate.is_default == True))
        for tmpl in result.scalars().all():
            tmpl.is_default = False
    
    # Create template
    template = EmailTemplate(
        name=template_data.name,
        subject=template_data.subject,
        body=template_data.body,
        is_default=template_data.is_default,
        created_by=template_data.created_by
    )
    
    db.add(template)
    await db.commit()
    await db.refresh(template)
    
    return EmailTemplateResponse.model_validate(template)


# ============================================
# GET ALL TEMPLATES
# ============================================
@router.get("", response_model=EmailTemplateListResponse)
async def get_templates(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by name"),
    db: AsyncSession = Depends(get_db)
):
    """Get all email templates with pagination"""
    
    # Build query
    query = select(EmailTemplate)
    
    if search:
        query = query.where(EmailTemplate.name.ilike(f"%{search}%"))
    
    # Get total count
    count_query = select(func.count()).select_from(EmailTemplate)
    if search:
        count_query = count_query.where(EmailTemplate.name.ilike(f"%{search}%"))
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Pagination
    total_pages = (total + per_page - 1) // per_page
    offset = (page - 1) * per_page
    
    query = query.order_by(EmailTemplate.created_at.desc()).offset(offset).limit(per_page)
    
    result = await db.execute(query)
    templates = result.scalars().all()
    
    return EmailTemplateListResponse(
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        items=[EmailTemplateResponse.model_validate(t) for t in templates]
    )


# ============================================
# GET SINGLE TEMPLATE
# ============================================
@router.get("/{template_id}", response_model=EmailTemplateResponse)
async def get_template(
    template_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a single template by ID"""
    
    result = await db.execute(
        select(EmailTemplate).where(EmailTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=404,
            detail=f"Template with ID {template_id} not found"
        )
    
    return EmailTemplateResponse.model_validate(template)


# ============================================
# GET DEFAULT TEMPLATE
# ============================================
@router.get("/default/active", response_model=EmailTemplateResponse)
async def get_default_template(
    db: AsyncSession = Depends(get_db)
):
    """Get the default email template"""
    
    result = await db.execute(
        select(EmailTemplate).where(EmailTemplate.is_default == True)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=404,
            detail="No default template set"
        )
    
    return EmailTemplateResponse.model_validate(template)


# ============================================
# UPDATE TEMPLATE
# ============================================
@router.put("/{template_id}", response_model=EmailTemplateResponse)
async def update_template(
    template_id: int,
    template_data: EmailTemplateUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing template"""
    
    result = await db.execute(
        select(EmailTemplate).where(EmailTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=404,
            detail=f"Template with ID {template_id} not found"
        )
    
    # If setting as default, unset others
    if template_data.is_default:
        all_templates = await db.execute(
            select(EmailTemplate).where(EmailTemplate.is_default == True)
        )
        for tmpl in all_templates.scalars().all():
            if tmpl.id != template_id:
                tmpl.is_default = False
    
    # Update fields
    update_data = template_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)
    
    await db.commit()
    await db.refresh(template)
    
    return EmailTemplateResponse.model_validate(template)


# ============================================
# DELETE TEMPLATE
# ============================================
@router.delete("/{template_id}", response_model=MessageResponse)
async def delete_template(
    template_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a template"""
    
    result = await db.execute(
        select(EmailTemplate).where(EmailTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=404,
            detail=f"Template with ID {template_id} not found"
        )
    
    await db.delete(template)
    await db.commit()
    
    return MessageResponse(message=f"Template '{template.name}' deleted successfully")


# ============================================
# PREVIEW TEMPLATE WITH SAMPLE DATA
# ============================================
@router.post("/{template_id}/preview")
async def preview_template(
    template_id: int,
    sample_data: Optional[dict] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Preview a template with sample or provided data.
    
    Returns the personalized subject and body.
    """
    result = await db.execute(
        select(EmailTemplate).where(EmailTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=404,
            detail=f"Template with ID {template_id} not found"
        )
    
    # Use provided data or sample data
    lead_data = sample_data or {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "phone": "555-1234",
        "address": "123 Oak Street, Anytown",
        "property_type": "Single Family",
        "estimated_value": "$450,000"
    }
    
    # Personalize
    personalized_subject = EmailService.personalize_template(template.subject, lead_data)
    personalized_body = EmailService.personalize_template(template.body, lead_data)
    
    # Extract placeholders used
    placeholders = EmailService.extract_placeholders(template.subject + template.body)
    
    return {
        "template_id": template.id,
        "template_name": template.name,
        "original": {
            "subject": template.subject,
            "body": template.body
        },
        "personalized": {
            "subject": personalized_subject,
            "body": personalized_body
        },
        "placeholders_found": list(set(placeholders)),
        "sample_data_used": lead_data
    }


# ============================================
# CREATE DEFAULT TEMPLATES (SEED DATA)
# ============================================
@router.post("/seed/defaults", response_model=MessageResponse)
async def seed_default_templates(
    db: AsyncSession = Depends(get_db)
):
    """Create default email templates for quick start"""
    
    default_templates = [
        {
            "name": "Initial Outreach",
            "subject": "Quick question about {{address}}",
            "body": """Hi {{first_name}},

I noticed your property at {{address}} and wanted to reach out.

I'm a local real estate agent specializing in {{property_type}} properties in your area. I've helped many homeowners get top dollar for their properties, and I'd love to discuss how I can help you.

Would you be open to a quick 10-minute call this week?

Best regards,
[Your Name]
[Your Phone]""",
            "is_default": True
        },
        {
            "name": "Follow Up #1",
            "subject": "Following up - {{address}}",
            "body": """Hi {{first_name}},

I wanted to follow up on my previous email about your property at {{address}}.

I understand you're busy, but I believe I could help you get the best possible price for your {{property_type}}.

Do you have 10 minutes this week for a quick chat?

Best,
[Your Name]""",
            "is_default": False
        },
        {
            "name": "Market Update",
            "subject": "{{first_name}}, market update for {{address}}",
            "body": """Hi {{first_name}},

I wanted to share some exciting news about the real estate market in your area.

Properties like yours at {{address}} are in high demand right now. Recent sales in your neighborhood have been strong, and I believe your {{property_type}} could attract significant interest.

Would you like me to prepare a free market analysis for your property?

Best regards,
[Your Name]""",
            "is_default": False
        }
    ]
    
    created = 0
    for tmpl_data in default_templates:
        # Check if exists
        existing = await db.execute(
            select(EmailTemplate).where(EmailTemplate.name == tmpl_data["name"])
        )
        if existing.scalar_one_or_none():
            continue
        
        template = EmailTemplate(**tmpl_data)
        db.add(template)
        created += 1
    
    await db.commit()
    
    return MessageResponse(message=f"Created {created} default templates")
