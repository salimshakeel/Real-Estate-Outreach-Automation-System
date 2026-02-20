from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, 
    ForeignKey, Numeric, CheckConstraint, Index, text
)
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


# ============================================
# TABLE 1: EMAIL_TEMPLATES (NO DEPENDENCIES)
# ============================================
class EmailTemplate(Base):
    __tablename__ = "email_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    is_default = Column(Boolean, default=False, server_default=text("FALSE"))
    created_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, server_default=text("CURRENT_TIMESTAMP"))

    __table_args__ = (
        Index("idx_email_templates_is_default", "is_default"),
        Index("idx_email_templates_created_at", "created_at"),
    )


# ============================================
# TABLE 2: CAMPAIGNS (NO DEPENDENCIES)
# ============================================
class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    email_template = Column(Text)
    status = Column(String(50), default="draft", server_default=text("'draft'"))
    started_at = Column(DateTime)
    ended_at = Column(DateTime)
    created_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, server_default=text("CURRENT_TIMESTAMP"))

    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'scheduled', 'active', 'completed', 'paused')",
            name="campaigns_status_check"
        ),
        Index("idx_campaigns_status", "status"),
        Index("idx_campaigns_created_at", "created_at"),
        Index("idx_campaigns_created_by", "created_by"),
    )


# ============================================
# TABLE 3: LEADS (NO DEPENDENCIES)
# ============================================
class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100))
    company = Column(String(100))
    phone = Column(String(20))
    address = Column(String(255))
    property_type = Column(String(100))
    estimated_value = Column(String(50))
    status = Column(String(50), default="uploaded", server_default=text("'uploaded'"))
    notes = Column(Text)
    created_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, server_default=text("CURRENT_TIMESTAMP"))

    # Relationships (CASCADE delete)
    email_sequences = relationship(
        "EmailSequence", 
        back_populates="lead", 
        cascade="all, delete-orphan"
    )
    replies = relationship(
        "Reply", 
        back_populates="lead", 
        cascade="all, delete-orphan"
    )
    bookings = relationship(
        "Booking", 
        back_populates="lead", 
        cascade="all, delete-orphan"
    )
    sms_messages = relationship(
        "SmsMessage",
        back_populates="lead",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('uploaded', 'contacted', 'replied', 'interested', 'booked', 'closed')",
            name="leads_status_check"
        ),
        Index("idx_leads_email", "email"),
        Index("idx_leads_status", "status"),
        Index("idx_leads_created_at", "created_at"),
        Index("idx_leads_created_by", "created_by"),
    )


# ============================================
# TABLE 4: EMAIL_SEQUENCES (DEPENDS ON: leads)
# ============================================
class EmailSequence(Base):
    __tablename__ = "email_sequences"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(
        Integer, 
        ForeignKey("leads.id", ondelete="CASCADE", onupdate="CASCADE"), 
        nullable=False
    )
    sequence_day = Column(Integer, default=1, server_default=text("1"))
    email_subject = Column(String(255))
    email_body = Column(Text)
    status = Column(String(50), default="pending", server_default=text("'pending'"))
    sent_at = Column(DateTime, nullable=True)
    opened_at = Column(DateTime, nullable=True)
    clicked_at = Column(DateTime, nullable=True)
    replied_at = Column(DateTime, nullable=True)
    sendgrid_message_id = Column(String(255))
    bounce_reason = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, server_default=text("CURRENT_TIMESTAMP"))

    # Relationship
    lead = relationship("Lead", back_populates="email_sequences")

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'scheduled', 'sent', 'opened', 'replied', 'bounced')",
            name="email_sequences_status_check"
        ),
        Index("idx_email_sequences_lead_id", "lead_id"),
        Index("idx_email_sequences_status", "status"),
        Index("idx_email_sequences_created_at", "created_at"),
        Index("idx_email_sequences_sendgrid_message_id", "sendgrid_message_id"),
    )


# ============================================
# TABLE 5: REPLIES (DEPENDS ON: leads)
# ============================================
class Reply(Base):
    __tablename__ = "replies"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(
        Integer, 
        ForeignKey("leads.id", ondelete="CASCADE", onupdate="CASCADE"), 
        nullable=False
    )
    email_from = Column(String(255))
    email_subject = Column(String(255))
    email_body = Column(Text)
    sentiment = Column(String(50), nullable=True, default=None)
    confidence_score = Column(Numeric(3, 2), nullable=True)
    ai_model_used = Column(String(50))
    received_at = Column(DateTime, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, server_default=text("CURRENT_TIMESTAMP"))

    # Relationship
    lead = relationship("Lead", back_populates="replies")

    __table_args__ = (
        CheckConstraint(
            "sentiment IN ('interested', 'not_now', 'unsubscribe', 'other') OR sentiment IS NULL",
            name="replies_sentiment_check"
        ),
        CheckConstraint(
            "(confidence_score >= 0 AND confidence_score <= 1) OR confidence_score IS NULL",
            name="replies_confidence_check"
        ),
        Index("idx_replies_lead_id", "lead_id"),
        Index("idx_replies_sentiment", "sentiment"),
        Index("idx_replies_created_at", "created_at"),
    )


# ============================================
# TABLE 6: BOOKINGS (DEPENDS ON: leads)
# ============================================
class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(
        Integer, 
        ForeignKey("leads.id", ondelete="CASCADE", onupdate="CASCADE"), 
        nullable=False
    )
    calendly_event_id = Column(String(255))
    event_uri = Column(String(255))
    scheduled_time = Column(DateTime, nullable=False)
    calendly_invitee_email = Column(String(255))
    calendly_response_status = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, server_default=text("CURRENT_TIMESTAMP"))

    # Relationship
    lead = relationship("Lead", back_populates="bookings")

    __table_args__ = (
        CheckConstraint(
            "calendly_response_status IN ('confirmed', 'tentative', 'cancelled') OR calendly_response_status IS NULL",
            name="bookings_response_status_check"
        ),
        Index("idx_bookings_lead_id", "lead_id"),
        Index("idx_bookings_scheduled_time", "scheduled_time"),
        Index("idx_bookings_created_at", "created_at"),
    )


# ============================================
# TABLE 7: CHATBOT_MESSAGES (DEPENDS ON: leads)
# ============================================
class ChatbotMessage(Base):
    __tablename__ = "chatbot_messages"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(
        Integer,
        ForeignKey("leads.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    role = Column(String(20), nullable=False)  # "user" | "assistant" | "system"
    content = Column(Text, nullable=False)
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    # Relationship back to lead (one-to-many)
    lead = relationship("Lead", backref="chatbot_messages")

    __table_args__ = (
        Index("idx_chatbot_messages_lead_id", "lead_id"),
        Index("idx_chatbot_messages_created_at", "created_at"),
    )
#HELLO WORLD

# ============================================
# TABLE 8: SMS_MESSAGES (DEPENDS ON: leads)
# ============================================
class SmsMessage(Base):
    __tablename__ = "sms_messages"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(
        Integer,
        ForeignKey("leads.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    to_number = Column(String(20), nullable=False)  # E.164
    body = Column(Text, nullable=False)
    status = Column(String(50), default="pending", server_default=text("'pending'"))
    twilio_sid = Column(String(255), nullable=True)  # Twilio Message SID for status callbacks
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    lead = relationship("Lead", back_populates="sms_messages")

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'sent', 'delivered', 'failed', 'undelivered')",
            name="sms_messages_status_check"
        ),
        Index("idx_sms_messages_lead_id", "lead_id"),
        Index("idx_sms_messages_status", "status"),
        Index("idx_sms_messages_created_at", "created_at"),
        Index("idx_sms_messages_twilio_sid", "twilio_sid"),
    )
