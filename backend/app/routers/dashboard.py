"""
Dashboard Router
Endpoints for dashboard statistics and analytics
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.database import get_db
from app.models import Lead, EmailSequence, Reply, Booking, Campaign
from app.schemas import (
    DashboardStats, DashboardLeadFunnel, DashboardRecentActivity, DashboardResponse
)

router = APIRouter()


# ============================================
# MAIN DASHBOARD
# ============================================
@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    db: AsyncSession = Depends(get_db)
):
    """
    Get complete dashboard with stats, funnel, and recent activity.
    
    This is the main endpoint for the dashboard view.
    """
    stats = await get_stats(db)
    funnel = await get_funnel(db)
    activity = await get_recent_activity(db)
    
    return DashboardResponse(
        stats=stats,
        funnel=funnel,
        recent_activity=activity
    )


# ============================================
# STATISTICS
# ============================================
@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard statistics only"""
    return await get_stats(db)


async def get_stats(db: AsyncSession) -> DashboardStats:
    """Calculate all dashboard statistics"""
    #HELLO WORLD
    # Time boundaries
    now = datetime.utcnow(0
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    
    # ---- LEADS ----
    total_leads_result = await db.execute(select(func.count(Lead.id)))
    total_leads = total_leads_result.scalar() or 0
    
    # Leads by status
    leads_by_status_query = select(
        Lead.status, func.count(Lead.id)
    ).group_by(Lead.status)
    leads_status_result = await db.execute(leads_by_status_query)
    leads_by_status = {row[0]: row[1] for row in leads_status_result.fetchall()}
    
    # ---- EMAILS ----
    total_emails_result = await db.execute(select(func.count(EmailSequence.id)))
    total_emails_sent = total_emails_result.scalar() or 0
    
    # Emails by status
    emails_opened_result = await db.execute(
        select(func.count(EmailSequence.id)).where(EmailSequence.status == 'opened')
    )
    emails_opened = emails_opened_result.scalar() or 0
    
    emails_replied_result = await db.execute(
        select(func.count(EmailSequence.id)).where(EmailSequence.status == 'replied')
    )
    emails_replied = emails_replied_result.scalar() or 0
    
    emails_bounced_result = await db.execute(
        select(func.count(EmailSequence.id)).where(EmailSequence.status == 'bounced')
    )
    emails_bounced = emails_bounced_result.scalar() or 0
    
    # Calculate rates
    open_rate = (emails_opened / total_emails_sent * 100) if total_emails_sent > 0 else 0.0
    reply_rate = (emails_replied / total_emails_sent * 100) if total_emails_sent > 0 else 0.0
    
    # ---- REPLIES ----
    total_replies_result = await db.execute(select(func.count(Reply.id)))
    total_replies = total_replies_result.scalar() or 0
    
    # Replies by sentiment
    replies_by_sentiment_query = select(
        Reply.sentiment, func.count(Reply.id)
    ).group_by(Reply.sentiment)
    replies_sentiment_result = await db.execute(replies_by_sentiment_query)
    replies_by_sentiment = {
        row[0] or "unprocessed": row[1] 
        for row in replies_sentiment_result.fetchall()
    }
    
    # ---- BOOKINGS ----
    total_bookings_result = await db.execute(select(func.count(Booking.id)))
    total_bookings = total_bookings_result.scalar() or 0
    
    upcoming_bookings_result = await db.execute(
        select(func.count(Booking.id)).where(Booking.scheduled_time >= now)
    )
    upcoming_bookings = upcoming_bookings_result.scalar() or 0
    
    # ---- TIME-BASED METRICS ----
    # Emails sent today
    emails_today_result = await db.execute(
        select(func.count(EmailSequence.id)).where(
            and_(
                EmailSequence.sent_at >= today_start,
                EmailSequence.status.in_(['sent', 'opened', 'replied'])
            )
        )
    )
    emails_sent_today = emails_today_result.scalar() or 0
    
    # Emails sent this week
    emails_week_result = await db.execute(
        select(func.count(EmailSequence.id)).where(
            and_(
                EmailSequence.sent_at >= week_start,
                EmailSequence.status.in_(['sent', 'opened', 'replied'])
            )
        )
    )
    emails_sent_this_week = emails_week_result.scalar() or 0
    
    # Replies today
    replies_today_result = await db.execute(
        select(func.count(Reply.id)).where(Reply.created_at >= today_start)
    )
    replies_today = replies_today_result.scalar() or 0
    
    # Bookings this week
    bookings_week_result = await db.execute(
        select(func.count(Booking.id)).where(
            Booking.scheduled_time >= week_start
        )
    )
    bookings_this_week = bookings_week_result.scalar() or 0
    
    return DashboardStats(
        total_leads=total_leads,
        leads_by_status=leads_by_status,
        total_emails_sent=total_emails_sent,
        emails_opened=emails_opened,
        emails_replied=emails_replied,
        emails_bounced=emails_bounced,
        open_rate=round(open_rate, 2),
        reply_rate=round(reply_rate, 2),
        total_replies=total_replies,
        replies_by_sentiment=replies_by_sentiment,
        total_bookings=total_bookings,
        upcoming_bookings=upcoming_bookings,
        emails_sent_today=emails_sent_today,
        emails_sent_this_week=emails_sent_this_week,
        replies_today=replies_today,
        bookings_this_week=bookings_this_week
    )


# ============================================
# LEAD FUNNEL
# ============================================
@router.get("/funnel", response_model=DashboardLeadFunnel)
async def get_dashboard_funnel(
    db: AsyncSession = Depends(get_db)
):
    """Get lead funnel data"""
    return await get_funnel(db)


async def get_funnel(db: AsyncSession) -> DashboardLeadFunnel:
    """Calculate lead funnel counts"""
    
    statuses = ['uploaded', 'contacted', 'replied', 'interested', 'booked', 'closed']
    funnel_data = {}
    
    for status in statuses:
        result = await db.execute(
            select(func.count(Lead.id)).where(Lead.status == status)
        )
        funnel_data[status] = result.scalar() or 0
    
    return DashboardLeadFunnel(**funnel_data)


# ============================================
# RECENT ACTIVITY
# ============================================
@router.get("/activity", response_model=list)
async def get_dashboard_activity(
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """Get recent activity feed"""
    return await get_recent_activity(db, limit)


async def get_recent_activity(db: AsyncSession, limit: int = 10) -> list:
    """Get recent activity across all entities"""
    
    activities = []
    
    # Recent emails sent
    emails_result = await db.execute(
        select(EmailSequence, Lead)
        .join(Lead, EmailSequence.lead_id == Lead.id)
        .where(EmailSequence.sent_at.isnot(None))
        .order_by(EmailSequence.sent_at.desc())
        .limit(limit)
    )
    
    for seq, lead in emails_result.fetchall():
        activities.append(DashboardRecentActivity(
            type="email_sent",
            lead_id=lead.id,
            lead_name=f"{lead.first_name} {lead.last_name or ''}".strip(),
            description=f"Email sent: {seq.email_subject[:50]}..." if seq.email_subject and len(seq.email_subject) > 50 else f"Email sent: {seq.email_subject or 'No subject'}",
            timestamp=seq.sent_at
        ))
    
    # Recent replies
    replies_result = await db.execute(
        select(Reply, Lead)
        .join(Lead, Reply.lead_id == Lead.id)
        .order_by(Reply.created_at.desc())
        .limit(limit)
    )
    
    for reply, lead in replies_result.fetchall():
        sentiment_text = f" ({reply.sentiment})" if reply.sentiment else ""
        activities.append(DashboardRecentActivity(
            type="reply_received",
            lead_id=lead.id,
            lead_name=f"{lead.first_name} {lead.last_name or ''}".strip(),
            description=f"Reply received{sentiment_text}",
            timestamp=reply.created_at
        ))
    
    # Recent bookings
    bookings_result = await db.execute(
        select(Booking, Lead)
        .join(Lead, Booking.lead_id == Lead.id)
        .order_by(Booking.created_at.desc())
        .limit(limit)
    )
    
    for booking, lead in bookings_result.fetchall():
        time_str = booking.scheduled_time.strftime("%b %d at %I:%M %p")
        activities.append(DashboardRecentActivity(
            type="booking_created",
            lead_id=lead.id,
            lead_name=f"{lead.first_name} {lead.last_name or ''}".strip(),
            description=f"Meeting scheduled for {time_str}",
            timestamp=booking.created_at
        ))
    
    # Sort all activities by timestamp and limit
    activities.sort(key=lambda x: x.timestamp, reverse=True)
    return activities[:limit]


# ============================================
# CAMPAIGN OVERVIEW
# ============================================
@router.get("/campaigns", response_model=dict)
async def get_campaigns_overview(
    db: AsyncSession = Depends(get_db)
):
    """Get quick overview of campaigns"""
    
    # Count by status
    campaigns_query = select(
        Campaign.status, func.count(Campaign.id)
    ).group_by(Campaign.status)
    
    result = await db.execute(campaigns_query)
    by_status = {row[0]: row[1] for row in result.fetchall()}
    
    # Get active campaigns
    active_result = await db.execute(
        select(Campaign)
        .where(Campaign.status == 'active')
        .order_by(Campaign.started_at.desc())
        .limit(5)
    )
    active_campaigns = [
        {
            "id": c.id,
            "name": c.name,
            "started_at": c.started_at
        }
        for c in active_result.scalars().all()
    ]
    
    total_result = await db.execute(select(func.count(Campaign.id)))
    total = total_result.scalar() or 0
    
    return {
        "total": total,
        "by_status": by_status,
        "active_campaigns": active_campaigns
    }


# ============================================
# QUICK STATS (LIGHTWEIGHT)
# ============================================
@router.get("/quick", response_model=dict)
async def get_quick_stats(
    db: AsyncSession = Depends(get_db)
):
    """
    Lightweight endpoint for quick stats refresh.
    
    Returns only essential counts for fast loading.
    """
    leads = await db.execute(select(func.count(Lead.id)))
    emails = await db.execute(select(func.count(EmailSequence.id)))
    replies = await db.execute(select(func.count(Reply.id)))
    bookings = await db.execute(select(func.count(Booking.id)))
    
    return {
        "leads": leads.scalar() or 0,
        "emails_sent": emails.scalar() or 0,
        "replies": replies.scalar() or 0,
        "bookings": bookings.scalar() or 0
    }
