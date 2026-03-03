from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

# ============================================
# GENERAL RESPONSE SCHEMAS
# ============================================


class MessageResponse(BaseModel):
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
    created_by: str | None = None


class EmailTemplateUpdate(BaseModel):
    """Update an existing email template"""

    name: str | None = Field(None, max_length=255)
    subject: str | None = Field(None, max_length=255)
    body: str | None = None
    is_default: bool | None = None


class EmailTemplateResponse(BaseModel):
    """Email template response"""

    id: int
    name: str
    subject: str
    body: str
    is_default: bool
    created_by: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EmailTemplateListResponse(PaginatedResponse):
    """List of email templates"""

    items: list[EmailTemplateResponse]


# ============================================
# CAMPAIGN SCHEMAS
# ============================================


class CampaignCreate(BaseModel):
    """Create a new campaign"""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    email_template: str | None = None
    created_by: str | None = None


class CampaignUpdate(BaseModel):
    """Update an existing campaign"""

    name: str | None = Field(None, max_length=255)
    description: str | None = None
    email_template: str | None = None
    status: str | None = Field(None, pattern="^(draft|scheduled|active|completed|paused)$")


class CampaignResponse(BaseModel):
    """Campaign response"""

    id: int
    name: str
    description: str | None
    email_template: str | None
    status: str
    started_at: datetime | None
    ended_at: datetime | None
    created_by: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CampaignListResponse(PaginatedResponse):
    """List of campaigns"""

    items: list[CampaignResponse]


class CampaignStartRequest(BaseModel):
    """Request to start a campaign"""

    lead_ids: list[int] = Field(..., min_length=1)
    email_template_id: int | None = None
    subject: str | None = None
    body: str | None = None


# ============================================
# LEAD SCHEMAS
# ============================================


class LeadCreate(BaseModel):
    """Create a single lead"""

    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    company: str | None = Field(None, max_length=100)
    phone: str | None = Field(None, max_length=20)
    address: str | None = Field(None, max_length=255)
    property_type: str | None = Field(None, max_length=100)
    estimated_value: str | None = Field(None, max_length=50)
    notes: str | None = None
    created_by: str | None = None


class LeadUpdate(BaseModel):
    """Update an existing lead"""

    email: EmailStr | None = None
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    company: str | None = Field(None, max_length=100)
    phone: str | None = Field(None, max_length=20)
    address: str | None = Field(None, max_length=255)
    property_type: str | None = Field(None, max_length=100)
    estimated_value: str | None = Field(None, max_length=50)
    status: str | None = Field(None, pattern="^(uploaded|contacted|replied|interested|booked|closed)$")
    notes: str | None = None


class LeadResponse(BaseModel):
    """Lead response"""

    id: int
    email: str
    first_name: str
    last_name: str | None
    company: str | None
    phone: str | None
    address: str | None
    property_type: str | None
    estimated_value: str | None
    status: str
    notes: str | None
    created_by: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LeadListResponse(PaginatedResponse):
    """List of leads"""

    items: list[LeadResponse]


class LeadBulkCreate(BaseModel):
    """Bulk create leads from CSV data"""

    leads: list[LeadCreate]


class LeadBulkResponse(BaseModel):
    """Response for bulk lead creation"""

    total: int
    created: int
    duplicates: int
    errors: list[str]


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

    status: str | None = Field(None, pattern="^(pending|scheduled|sent|opened|replied|bounced)$")
    sent_at: datetime | None = None
    opened_at: datetime | None = None
    clicked_at: datetime | None = None
    replied_at: datetime | None = None
    sendgrid_message_id: str | None = None
    bounce_reason: str | None = None


class EmailSequenceResponse(BaseModel):
    """Email sequence response"""

    id: int
    lead_id: int
    sequence_day: int
    email_subject: str | None
    email_body: str | None
    status: str
    sent_at: datetime | None
    opened_at: datetime | None
    clicked_at: datetime | None
    replied_at: datetime | None
    sendgrid_message_id: str | None
    bounce_reason: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EmailSequenceListResponse(PaginatedResponse):
    """List of email sequences"""

    items: list[EmailSequenceResponse]


# ============================================
# REPLY SCHEMAS
# ============================================


class ReplyCreate(BaseModel):
    """Create a reply (manual or from webhook)"""

    lead_id: int
    email_from: str | None = Field(None, max_length=255)
    email_subject: str | None = Field(None, max_length=255)
    email_body: str | None = None
    sentiment: str | None = Field(None, pattern="^(interested|not_now|unsubscribe|other)$")
    confidence_score: float | None = Field(None, ge=0, le=1)
    ai_model_used: str | None = Field(None, max_length=50)
    received_at: datetime | None = None


class ReplyUpdate(BaseModel):
    """Update a reply (e.g., after AI processing)"""

    sentiment: str | None = Field(None, pattern="^(interested|not_now|unsubscribe|other)$")
    confidence_score: float | None = Field(None, ge=0, le=1)
    ai_model_used: str | None = Field(None, max_length=50)
    processed_at: datetime | None = None


class ReplyResponse(BaseModel):
    """Reply response"""

    id: int
    lead_id: int
    email_from: str | None
    email_subject: str | None
    email_body: str | None
    sentiment: str | None
    confidence_score: float | None
    ai_model_used: str | None
    received_at: datetime | None
    processed_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class ReplyListResponse(PaginatedResponse):
    """List of replies"""

    items: list[ReplyResponse]


# ============================================
# BOOKING SCHEMAS
# ============================================


class BookingCreate(BaseModel):
    """Create a booking (manual or from Calendly webhook)"""

    lead_id: int
    calendly_event_id: str | None = Field(None, max_length=255)
    event_uri: str | None = Field(None, max_length=255)
    scheduled_time: datetime
    calendly_invitee_email: str | None = Field(None, max_length=255)
    calendly_response_status: str | None = Field(None, pattern="^(confirmed|tentative|cancelled)$")


class BookingUpdate(BaseModel):
    """Update a booking"""

    scheduled_time: datetime | None = None
    calendly_response_status: str | None = Field(None, pattern="^(confirmed|tentative|cancelled)$")


class BookingResponse(BaseModel):
    """Booking response"""

    id: int
    lead_id: int
    calendly_event_id: str | None
    event_uri: str | None
    scheduled_time: datetime
    calendly_invitee_email: str | None
    calendly_response_status: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BookingListResponse(PaginatedResponse):
    """List of bookings"""

    items: list[BookingResponse]


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
    recent_activity: list[DashboardRecentActivity]


# ============================================
# CSV UPLOAD SCHEMAS
# ============================================


class CSVColumnMapping(BaseModel):
    """Map CSV columns to lead fields"""

    email: str = "email"
    first_name: str = "first_name"
    last_name: str | None = "last_name"
    company: str | None = "company"
    phone: str | None = "phone"
    address: str | None = "address"
    property_type: str | None = "property_type"
    estimated_value: str | None = "estimated_value"


class CSVUploadResponse(BaseModel):
    """Response after CSV upload"""

    filename: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    duplicates: int
    created: int
    errors: list[str]


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
    messages: list[ChatMessage]
    lead_score: int | None = None
    industry: str | None = None
    source: str | None = None  # e.g. "email_open", "email_click", "manual"
    last_email_summary: str | None = None


class ChatbotNextAction(BaseModel):
    """What the system should do after this bot reply"""

    type: str  # "continue" | "book_meeting" | "escalate_human" | "end"
    reason: str | None = None  # short, system-facing explanation


class ChatbotResponse(BaseModel):
    """Chatbot response returned to frontend"""

    reply: str
    next_action: ChatbotNextAction
    updated_lead_score: int | None = None


class ChatbotHistoryResponse(BaseModel):
    """Full chatbot history for a lead"""

    lead_id: int
    messages: list[ChatMessage]


# ============================================
# SEND EMAIL SCHEMAS
# ============================================


class SendEmailRequest(BaseModel):
    """Request to send email to a lead"""

    lead_id: int
    subject: str = Field(..., min_length=1, max_length=255)
    body: str = Field(..., min_length=1)
    template_id: int | None = None


class SendBulkEmailRequest(BaseModel):
    """Request to send emails to multiple leads"""

    lead_ids: list[int] = Field(..., min_length=1)
    subject: str = Field(..., min_length=1, max_length=255)
    body: str = Field(..., min_length=1)
    template_id: int | None = None


class SendEmailResponse(BaseModel):
    """Response after sending email"""

    success: bool
    lead_id: int
    email_sequence_id: int | None
    message: str


class SendBulkEmailResponse(BaseModel):
    """Response after sending bulk emails"""

    total: int
    sent: int
    failed: int
    results: list[SendEmailResponse]


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
    sms_message_id: int | None = None
    twilio_sid: str | None = None
    status: str  # "sent" | "mock" | "failed"
    error: str | None = None
    message: str


class SmsMessageResponse(BaseModel):
    """Single SMS record for history"""

    id: int
    lead_id: int
    to_number: str
    body: str
    status: str
    twilio_sid: str | None = None
    sent_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class SmsHistoryResponse(BaseModel):
    """SMS history for a lead"""

    lead_id: int
    messages: list[SmsMessageResponse]


# ============================================
# VOICE SCHEMAS (Step 4)
# ============================================


class VoiceCallRequest(BaseModel):
    """Request to start an outbound AI voice call to a lead"""

    lead_id: int
    dynamic_variables: dict | None = None  # Extra vars injected into Retell agent prompt


class VoiceCallResponse(BaseModel):
    """Response after initiating a voice call"""

    success: bool
    lead_id: int
    voice_call_id: int | None = None  # DB record PK
    retell_call_id: str | None = None
    status: str  # "calling" | "mock" | "failed"
    error: str | None = None
    message: str


class VoiceCallDetailResponse(BaseModel):
    """Single voice call record"""

    id: int
    lead_id: int
    to_number: str
    retell_call_id: str | None = None
    retell_agent_id: str | None = None
    status: str
    duration_seconds: int | None = None
    call_summary: str | None = None
    call_outcome: str | None = None
    transcript: str | None = None
    recording_url: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class VoiceCallHistoryResponse(BaseModel):
    """All voice calls for a lead"""

    lead_id: int
    calls: list[VoiceCallDetailResponse]


# ============================================
# LLM INTEGRATION SCHEMAS
# ============================================


class CampaignBrief(BaseModel):
    """Brief for AI email campaign generation"""
    campaign_id: int
    target_audience: str = Field(..., min_length=1)
    goal: str = Field(..., min_length=1)
    pain_point: str | None = None
    tone: str = "professional but conversational"
    max_word_count: int = 150


class EmailVariation(BaseModel):
    """Single AI-generated email variation"""
    label: str  # A, B, C, D, E
    subject: str
    body: str
    psychological_trigger: str


class CampaignGenerateResponse(BaseModel):
    """Response from AI campaign generator"""
    campaign_id: int
    variations: list[EmailVariation]
    patterns_used: int  # How many learned patterns were fed into the prompt


class ABTestAnalysisRequest(BaseModel):
    """Request to analyze A/B test results"""
    campaign_id: int


class ABTestWinner(BaseModel):
    """A/B test analysis result"""
    campaign_id: int
    winner_label: str  # "A", "B", etc.
    winner_subject: str
    winner_body: str
    explanation: str
    pattern_learned: str  # The new pattern saved to ai_patterns
    stats: dict  # Per-variation stats


class LeadScoreRequest(BaseModel):
    """Request to score a single lead"""
    lead_id: int
    icp_description: str | None = None  # Client's ideal customer profile


class LeadScoreBulkRequest(BaseModel):
    """Request to score multiple leads"""
    lead_ids: list[int] = Field(..., min_length=1)
    icp_description: str | None = None


class LeadScoreResult(BaseModel):
    """Single lead scoring result"""
    lead_id: int
    score: int  # 0-100
    priority: str  # Hot / Warm / Cold / Dead
    reasoning: str
    recommended_campaign: str | None = None
    personalization_hints: str | None = None


class LeadScoreResponse(BaseModel):
    """Response for single lead scoring"""
    result: LeadScoreResult


class LeadScoreBulkResponse(BaseModel):
    """Response for bulk lead scoring"""
    total: int
    scored: int
    results: list[LeadScoreResult]


class WeeklyInsightsResponse(BaseModel):
    """AI-generated weekly insights"""
    period: str  # e.g. "Feb 17 - Feb 23, 2026"
    summary: str  # Plain English summary
    highlights: list[str]  # Key bullets
    recommendations: list[str]  # Action items
    stats_snapshot: dict  # Raw numbers used


class CampaignVariationResponse(BaseModel):
    """Single campaign variation with stats"""
    id: int
    label: str
    subject: str
    body: str
    psychological_trigger: str | None
    sends: int
    opens: int
    clicks: int
    replies: int
    is_winner: bool
    open_rate: float
    reply_rate: float
    created_at: datetime

    class Config:
        from_attributes = True


class AiLeadScoreResponse(BaseModel):
    """Stored AI lead score"""
    id: int
    lead_id: int
    score: int
    priority: str
    reasoning: str | None
    recommended_campaign: str | None
    personalization_hints: str | None
    scored_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class AiPatternResponse(BaseModel):
    """Single learned AI pattern"""
    id: int
    pattern: str
    category: str
    confidence: float | None
    sample_size: int | None
    source_campaign_id: int | None
    created_at: datetime

    class Config:
        from_attributes = True
