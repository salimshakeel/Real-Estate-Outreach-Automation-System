"""
SendGrid Event Webhook Handler
================================
Receives real-time email events from SendGrid and updates the database.

Events handled (Phase 1):
  - open        → marks email opened, advances lead status
  - click       → records first click timestamp
  - bounce      → marks sequence bounced with reason, suppresses hard bounces
  - spamreport  → marks lead suppressed, excludes from future sends

How to set up in SendGrid dashboard (do this once after deploying):
  1. Go to: Settings → Mail Settings → Event Webhook
  2. HTTP Post URL:
        https://your-backend.onrender.com/webhooks/sendgrid/events?secret=YOUR_SECRET
  3. Check these boxes: Opens, Clicks, Bounces, Spam Reports
  4. Click "Test Your Integration" to verify it works
  5. Save

Security:
  We use a simple shared secret passed as a query parameter (?secret=VALUE).
  Set SENDGRID_WEBHOOK_SECRET in your .env to the same value.
  If the secret is missing or wrong, we return 403 Forbidden.
  If SENDGRID_WEBHOOK_SECRET is not set in .env, we skip verification
  (allows development/testing without a secret).
"""

import hmac
from datetime import UTC, datetime

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models import EmailSequence, Lead

router = APIRouter()
settings = get_settings()


# ============================================
# PYDANTIC MODELS FOR SWAGGER
# ============================================


class SendGridEvent(BaseModel):
    """
    Single event from SendGrid webhook.

    Example:
    {
        "event": "open",
        "sg_message_id": "abc123xyz.filter001...",
        "timestamp": 1708300000,
        "email": "john@example.com"
    }
    """

    event: str
    sg_message_id: str
    timestamp: int
    email: str
    type: str | None = None  # For bounce events: "hard" or "soft"
    reason: str | None = None  # For bounce events: reason text

    class Config:
        json_schema_extra = {
            "example": {
                "event": "open",
                "sg_message_id": "mock_abc123xyz",
                "timestamp": 1708300000,
                "email": "test@example.com",
            }
        }


# ============================================
# SECURITY HELPERS
# ============================================


def verify_webhook_secret(secret: str | None) -> bool:
    """
    Verify the request came from SendGrid using a shared secret.

    We configure SendGrid to append ?secret=VALUE to the webhook URL.
    This function checks that VALUE matches what we have in .env.

    Uses hmac.compare_digest() for constant-time comparison,
    which prevents timing-based attacks.
    """
    configured_secret = settings.SENDGRID_WEBHOOK_SECRET

    # If no secret is configured in .env, skip verification (dev mode)
    if not configured_secret:
        print("⚠️  SENDGRID_WEBHOOK_SECRET not set — skipping signature verification")
        return True

    # Reject if secret is missing from the request
    if not secret:
        return False

    # Constant-time string comparison (prevents timing attacks)
    return hmac.compare_digest(secret.encode(), configured_secret.encode())


# ============================================
# LEAD STATUS PROGRESSION HELPER
# ============================================

# We only ever move leads FORWARD through the pipeline, never backwards.
# e.g. a lead that has "replied" should never be downgraded to "contacted"
LEAD_STATUS_ORDER = [
    "uploaded",  # Just imported into the system
    "contacted",  # An email was sent to them
    "replied",  # They replied to an email
    "interested",  # Manually marked as interested
    "booked",  # Meeting/demo booked
    "closed",  # Deal closed or permanently suppressed
]


async def try_advance_lead_status(db: AsyncSession, lead_id: int, target_status: str):
    """
    Update a lead's status, but only if the new status is a forward step.
    Prevents overwriting higher-value statuses like 'replied' with 'contacted'.
    """
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()

    if not lead:
        return

    try:
        current_index = LEAD_STATUS_ORDER.index(lead.status)
        target_index = LEAD_STATUS_ORDER.index(target_status)
    except ValueError:
        return  # Unknown status string, skip safely

    if target_index > current_index:
        print(f"📈 Lead {lead_id}: {lead.status} → {target_status}")
        lead.status = target_status


async def suppress_lead(db: AsyncSession, lead_id: int, reason: str):
    """
    Mark a lead as suppressed so they never receive future emails.
    Called for spam reports and hard bounces.

    Appends a suppression note to lead.notes (non-destructive).
    Sets lead.status = 'closed' to exclude from all future campaigns.
    """
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()

    if not lead:
        return

    existing_notes = lead.notes or ""

    # Only suppress once — don't keep appending
    if "[SUPPRESSED" not in existing_notes:
        date_str = datetime.now(UTC).strftime("%Y-%m-%d")
        suppression_note = f"[SUPPRESSED {date_str}: {reason}]"
        lead.notes = f"{existing_notes} {suppression_note}".strip()
        lead.status = "closed"
        print(f"🚫 Lead {lead_id} suppressed: {reason}")


# ============================================
# CORE EVENT PROCESSOR
# ============================================


async def process_event(db: AsyncSession, event: dict) -> bool:
    """
    Process one SendGrid event and update the database accordingly.

    Returns True if the event was processed, False if skipped.

    SendGrid event payload example:
    {
        "event": "open",
        "sg_message_id": "abc123xyz.filter0001p1las1-18284-5FE6E393-1.0",
        "timestamp": 1614000000,
        "email": "john@example.com"
    }
    """
    event_type = event.get("event", "").lower()
    timestamp = event.get("timestamp")
    event_time = datetime.utcfromtimestamp(timestamp) if timestamp else datetime.utcnow()

    # SendGrid message IDs include a suffix after a dot (e.g. "abc123.filter001...")
    # We only stored the base ID when we sent the email, so strip the suffix
    raw_message_id = event.get("sg_message_id", "")
    message_id = raw_message_id.split(".")[0] if raw_message_id else None

    if not message_id:
        print(f"⚠️  Event '{event_type}' missing message_id — skipping")
        return False

    # Find the EmailSequence row that matches this message
    result = await db.execute(select(EmailSequence).where(EmailSequence.sendgrid_message_id == message_id))
    sequence = result.scalar_one_or_none()

    if not sequence:
        # This is normal for test sends from SendGrid dashboard,
        # or emails sent before tracking was configured.
        print(f"⚠️  No sequence found for message_id '{message_id}' ({event_type}) — skipping")
        return False

    lead_id = sequence.lead_id

    # --- Process by event type ---

    if event_type == "open":
        if not sequence.opened_at:
            # Only record the FIRST open (SendGrid fires this on every open)
            sequence.opened_at = event_time
            sequence.status = "opened"
            sequence.updated_at = datetime.utcnow()
            await try_advance_lead_status(db, lead_id, "contacted")
            print(f"📬 Opened: sequence {sequence.id} | lead {lead_id}")
        else:
            print(f"ℹ️  Duplicate open for sequence {sequence.id} — ignored")

    elif event_type == "click":
        if not sequence.clicked_at:
            sequence.clicked_at = event_time
            sequence.updated_at = datetime.utcnow()
            # A click implies the email was opened too
            if not sequence.opened_at:
                sequence.opened_at = event_time
            # Only update status if not already at a higher state
            if sequence.status not in ("replied", "opened"):
                sequence.status = "opened"
            await try_advance_lead_status(db, lead_id, "contacted")
            print(f"🖱️  Clicked: sequence {sequence.id} | lead {lead_id}")
        else:
            print(f"ℹ️  Duplicate click for sequence {sequence.id} — ignored")

    elif event_type == "bounce":
        bounce_type = event.get("type", "hard")  # "hard" or "soft"
        bounce_reason = event.get("reason", "Unknown reason")
        full_reason = f"{bounce_type}: {bounce_reason}"

        sequence.status = "bounced"
        sequence.bounce_reason = full_reason[:255]  # Column is VARCHAR(255)
        sequence.updated_at = datetime.utcnow()
        print(f"⚡ Bounced: sequence {sequence.id} | {full_reason[:60]}")

        # Hard bounce = address permanently invalid — suppress the lead
        # Soft bounce = temporary (mailbox full, server down) — don't suppress
        if bounce_type.lower() == "hard":
            await suppress_lead(db, lead_id, f"Hard bounce: {bounce_reason[:100]}")

    elif event_type == "spamreport":
        sequence.status = "bounced"
        sequence.bounce_reason = "Marked as spam by recipient"
        sequence.updated_at = datetime.utcnow()
        await suppress_lead(db, lead_id, "Spam report")
        print(f"🚨 Spam report: sequence {sequence.id} | lead {lead_id}")

    else:
        # We don't handle other event types in Phase 1 (delivered, unsubscribe, etc.)
        print(f"ℹ️  Unhandled event type '{event_type}' — skipped")
        return False

    return True


# ============================================
# WEBHOOK ENDPOINT
# ============================================


@router.post("/sendgrid/events")
async def handle_sendgrid_events(
    events: list[SendGridEvent] = Body(
        ...,
        example=[
            {"event": "open", "sg_message_id": "mock_abc123xyz", "timestamp": 1708300000, "email": "test@example.com"}
        ],
    ),
    secret: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Main SendGrid webhook endpoint.

    SendGrid POSTs a JSON array of events to this URL whenever
    an email is opened, clicked, bounced, or reported as spam.

    Full webhook URL to set in SendGrid dashboard:
    https://your-backend.onrender.com/webhooks/sendgrid/events?secret=YOUR_SECRET
    """
    # Security check
    if not verify_webhook_secret(secret):
        print("🔒 Webhook rejected: invalid or missing secret")
        raise HTTPException(status_code=403, detail="Forbidden: invalid webhook secret")

    # Process all events
    total = len(events)
    processed = 0
    skipped = 0

    for event in events:
        try:
            # Convert Pydantic model to dict for processing
            event_dict = event.model_dump()
            success = await process_event(db, event_dict)
            if success:
                processed += 1
            else:
                skipped += 1
        except Exception as e:
            # Log individual failures but keep processing the rest of the batch.
            # If we raise here, SendGrid will retry the ENTIRE batch.
            print(f"❌ Error on event {event.event} / " f"{event.sg_message_id}: {e}")
            skipped += 1

    # Commit all DB changes in one transaction
    try:
        await db.commit()
    except Exception as e:
        print(f"❌ DB commit failed after webhook processing: {e}")
        raise HTTPException(status_code=500, detail="Database commit failed")

    print(f"✅ Webhook batch done: {total} received | {processed} processed | {skipped} skipped")

    # IMPORTANT: Return 200. If we return 4xx or 5xx, SendGrid retries the whole batch.
    return {"received": total, "processed": processed, "skipped": skipped}


# ============================================
# HEALTH CHECK (GET version of the same URL)
# ============================================


@router.get("/sendgrid/events")
async def webhook_health():
    """
    GET version of the webhook URL.

    Visit this in a browser to confirm the endpoint is live and
    reachable before configuring it in the SendGrid dashboard.

    Expected response: {"status": "ready", "secret_configured": true, ...}
    """
    return {
        "status": "ready",
        "endpoint": "POST /webhooks/sendgrid/events",
        "secret_configured": bool(settings.SENDGRID_WEBHOOK_SECRET),
        "events_handled": ["open", "click", "bounce", "spamreport"],
        "tip": "Set this URL in SendGrid: Settings → Mail Settings → Event Webhook",
    }
