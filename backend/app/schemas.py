from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# ============================================
# GENERAL RESPONSE SCHEMAS
# ============================================

class MessageResponse(BaseModel):
    """Standard message response"""
    message: str
    success: bool = True


class PaginatedResponse(BaseModel):
    """Base for paginated responses"""
    total: int
    page: int
    per_page: int
    total_pages: int


# ============================================
# EMAIL TEMPLATE SCHEMAS
# ============================================

class EmailTemplateCreate(BaseModel):
    """Create a new email template"""
    name: str = Field(..., min_length=1, max_length=255)
    subject: str = Field(..., min_length=1, max_length=255)
    body: str = Field(..., min_length=1)
    is_default: bool = False
    created_by: Optional[str] = None


class EmailTemplateUpdate(BaseModel):
    """Update an existing email template"""
    name: Optional[str] = Field(None, max_length=255)
    subject: Optional[str] = Field(None, max_length=255)
    body: Optional[str] = None
    is_default: Optional[bool] = None


class EmailTemplateResponse(BaseModel):
    """Email template response"""
    id: int
    name: str
    subject: str
    body: str
    is_default: bool
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EmailTemplateListResponse(PaginatedResponse):
    """List of email templates"""
    items: List[EmailTemplateResponse]


# ============================================
# CAMPAIGN SCHEMAS
# ============================================

class CampaignCreate(BaseModel):
    """Create a new campaign"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    email_template: Optional[str] = None
    created_by: Optional[str] = None


class CampaignUpdate(BaseModel):
    """Update an existing campaign"""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    email_template: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(draft|scheduled|active|completed|paused)$")


class CampaignResponse(BaseModel):
    """Campaign response"""
    id: int
    name: str
    description: Optional[str]
    email_template: Optional[str]
    status: str
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CampaignListResponse(PaginatedResponse):
    """List of campaigns"""
    items: List[CampaignResponse]


class CampaignStartRequest(BaseModel):
    """Request to start a campaign"""
    lead_ids: List[int] = Field(..., min_length=1)
    email_template_id: Optional[int] = None
    subject: Optional[str] = None
    body: Optional[str] = None


# ============================================
# LEAD SCHEMAS
# ============================================

class LeadCreate(BaseModel):
    """Create a single lead"""
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    company: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=255)
    property_type: Optional[str] = Field(None, max_length=100)
    estimated_value: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None
    created_by: Optional[str] = None


class LeadUpdate(BaseModel):
    """Update an existing lead"""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    company: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=255)
    property_type: Optional[str] = Field(None, max_length=100)
    estimated_value: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, pattern="^(uploaded|contacted|replied|interested|booked|closed)$")
    notes: Optional[str] = None


class LeadResponse(BaseModel):
    """Lead response"""
    id: int
    email: str
    first_name: str
    last_name: Optional[str]
    company: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    property_type: Optional[str]
    estimated_value: Optional[str]
    status: str
    notes: Optional[str]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LeadListResponse(PaginatedResponse):
    """List of leads"""
    items: List[LeadResponse]


class LeadBulkCreate(BaseModel):
    """Bulk create leads from CSV data"""
    leads: List[LeadCreate]


class LeadBulkResponse(BaseModel):
    """Response for bulk lead creation"""
    total: int
    created: int
    duplicates: int
    errors: List[str]


# ============================================
# EMAIL SEQUENCE SCHEMAS
# ============================================

class EmailSequenceCreate(BaseModel):
    """Create an email sequence record"""
    lead_id: int
    sequence_day: int = 1
    email_subject: str = Field(..., max_length=255)
    email_body: str
    status: str = "pending"


class EmailSequenceUpdate(BaseModel):
    """Update email sequence status"""
    status: Optional[str] = Field(None, pattern="^(pending|scheduled|sent|opened|replied|bounced)$")
    sent_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    replied_at: Optional[datetime] = None
    sendgrid_message_id: Optional[str] = None
    bounce_reason: Optional[str] = None


class EmailSequenceResponse(BaseModel):
    """Email sequence response"""
    id: int
    lead_id: int
    sequence_day: int
    email_subject: Optional[str]
    email_body: Optional[str]
    status: str
    sent_at: Optional[datetime]
    opened_at: Optional[datetime]
    clicked_at: Optional[datetime]
    replied_at: Optional[datetime]
    sendgrid_message_id: Optional[str]
    bounce_reason: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EmailSequenceListResponse(PaginatedResponse):
    """List of email sequences"""
    items: List[EmailSequenceResponse]


# ============================================
# REPLY SCHEMAS
# ============================================

class ReplyCreate(BaseModel):
    """Create a reply (manual or from webhook)"""
    lead_id: int
    email_from: Optional[str] = Field(None, max_length=255)
    email_subject: Optional[str] = Field(None, max_length=255)
    email_body: Optional[str] = None
    sentiment: Optional[str] = Field(None, pattern="^(interested|not_now|unsubscribe|other)$")
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    ai_model_used: Optional[str] = Field(None, max_length=50)
    received_at: Optional[datetime] = None


class ReplyUpdate(BaseModel):
    """Update a reply (e.g., after AI processing)"""
    sentiment: Optional[str] = Field(None, pattern="^(interested|not_now|unsubscribe|other)$")
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    ai_model_used: Optional[str] = Field(None, max_length=50)
    processed_at: Optional[datetime] = None


class ReplyResponse(BaseModel):
    """Reply response"""
    id: int
    lead_id: int
    email_from: Optional[str]
    email_subject: Optional[str]
    email_body: Optional[str]
    sentiment: Optional[str]
    confidence_score: Optional[float]
    ai_model_used: Optional[str]
    received_at: Optional[datetime]
    processed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class ReplyListResponse(PaginatedResponse):
    """List of replies"""
    items: List[ReplyResponse]


# ============================================
# BOOKING SCHEMAS
# ============================================

class BookingCreate(BaseModel):
    """Create a booking (manual or from Calendly webhook)"""
    lead_id: int
    calendly_event_id: Optional[str] = Field(None, max_length=255)
    event_uri: Optional[str] = Field(None, max_length=255)
    scheduled_time: datetime
    calendly_invitee_email: Optional[str] = Field(None, max_length=255)
    calendly_response_status: Optional[str] = Field(None, pattern="^(confirmed|tentative|cancelled)$")


class BookingUpdate(BaseModel):
    """Update a booking"""
    scheduled_time: Optional[datetime] = None
    calendly_response_status: Optional[str] = Field(None, pattern="^(confirmed|tentative|cancelled)$")


class BookingResponse(BaseModel):
    """Booking response"""
    id: int
    lead_id: int
    calendly_event_id: Optional[str]
    event_uri: Optional[str]
    scheduled_time: datetime
    calendly_invitee_email: Optional[str]
    calendly_response_status: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BookingListResponse(PaginatedResponse):
    """List of bookings"""
    items: List[BookingResponse]


# ============================================
# DASHBOARD SCHEMAS
# ============================================

class DashboardStats(BaseModel):
    """Main dashboard statistics"""
    total_leads: int
    leads_by_status: dict  # {"uploaded": 50, "contacted": 30, ...}
    
    total_emails_sent: int
    emails_opened: int
    emails_replied: int
    emails_bounced: int
    
    open_rate: float  # percentage
    reply_rate: float  # percentage
    
    total_replies: int
    replies_by_sentiment: dict  # {"interested": 5, "not_now": 3, ...}
    
    total_bookings: int
    upcoming_bookings: int
    
    # Time-based metrics
    emails_sent_today: int
    emails_sent_this_week: int
    replies_today: int
    bookings_this_week: int


class DashboardLeadFunnel(BaseModel):
    """Lead funnel for dashboard"""
    uploaded: int
    contacted: int
    replied: int
    interested: int
    booked: int
    closed: int


class DashboardRecentActivity(BaseModel):
    """Recent activity item"""
    type: str  # "email_sent", "reply_received", "booking_created"
    lead_id: int
    lead_name: str
    description: str
    timestamp: datetime


class DashboardResponse(BaseModel):
    """Complete dashboard response"""
    stats: DashboardStats
    funnel: DashboardLeadFunnel
    recent_activity: List[DashboardRecentActivity]


# ============================================
# CSV UPLOAD SCHEMAS
# ============================================

class CSVColumnMapping(BaseModel):
    """Map CSV columns to lead fields"""
    email: str = "email"
    first_name: str = "first_name"
    last_name: Optional[str] = "last_name"
    company: Optional[str] = "company"
    phone: Optional[str] = "phone"
    address: Optional[str] = "address"
    property_type: Optional[str] = "property_type"
    estimated_value: Optional[str] = "estimated_value"


class CSVUploadResponse(BaseModel):
    """Response after CSV upload"""
    filename: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    duplicates: int
    created: int
    errors: List[str]


# ============================================
# CHATBOT SCHEMAS
# ============================================

class ChatMessage(BaseModel):
    """Single chat message in a conversation"""
    role: str  # "user" | "assistant" | "system"
    content: str


class ChatbotRequest(BaseModel):
    """Request from frontend chat widget to chatbot API"""
    lead_id: int
    messages: List[ChatMessage]
    lead_score: Optional[int] = None
    industry: Optional[str] = None
    source: Optional[str] = None  # e.g. "email_open", "email_click", "manual"
    last_email_summary: Optional[str] = None


class ChatbotNextAction(BaseModel):
    """What the system should do after this bot reply"""
    type: str  # "continue" | "book_meeting" | "escalate_human" | "end"
    reason: Optional[str] = None  # short, system-facing explanation


class ChatbotResponse(BaseModel):
    """Chatbot response returned to frontend"""
    reply: str
    next_action: ChatbotNextAction
    updated_lead_score: Optional[int] = None


class ChatbotHistoryResponse(BaseModel):
    """Full chatbot history for a lead"""
    lead_id: int
    messages: List[ChatMessage]


# ============================================
# SEND EMAIL SCHEMAS
# ============================================

class SendEmailRequest(BaseModel):
    """Request to send email to a lead"""
    lead_id: int
    subject: str = Field(..., min_length=1, max_length=255)
    body: str = Field(..., min_length=1)
    template_id: Optional[int] = None


class SendBulkEmailRequest(BaseModel):
    """Request to send emails to multiple leads"""
    lead_ids: List[int] = Field(..., min_length=1)
    subject: str = Field(..., min_length=1, max_length=255)
    body: str = Field(..., min_length=1)
    template_id: Optional[int] = None


class SendEmailResponse(BaseModel):
    """Response after sending email"""
    success: bool
    lead_id: int
    email_sequence_id: Optional[int]
    message: str


class SendBulkEmailResponse(BaseModel):
    """Response after sending bulk emails"""
    total: int
    sent: int
    failed: int
    results: List[SendEmailResponse]


# ============================================
# SMS SCHEMAS (Step 3)
# ============================================

class SmsSendRequest(BaseModel):
    """Request to send SMS to a lead"""
    lead_id: int
    body: str = Field(..., min_length=1, max_length=1600)
    personalize: bool = True  # Replace {{first_name}}, etc. with lead data


class SmsSendResponse(BaseModel):
    """Response after sending SMS"""
    success: bool
    lead_id: int
    sms_message_id: Optional[int] = None
    twilio_sid: Optional[str] = None
    status: str  # "sent" | "mock" | "failed"
    error: Optional[str] = None
    message: str


class SmsMessageResponse(BaseModel):
    """Single SMS record for history"""
    id: int
    lead_id: int
    to_number: str
    body: str
    status: str
    twilio_sid: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SmsHistoryResponse(BaseModel):
    """SMS history for a lead"""
    lead_id: int
    messages: List[SmsMessageResponse]
