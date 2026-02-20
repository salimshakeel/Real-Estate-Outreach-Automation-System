"""
Email Service
==============
Handles all email sending operations.

Modes:
  - Mock (demo): Logs to console, no real emails sent
  - Production:  Sends via SendGrid API with full tracking

Key features:
  - send_campaign_email(): saves message_id back to DB so webhooks can track events
  - Retry logic with exponential backoff (3 attempts on failure)
  - Daily send rate limiter (email warming protection)
  - Personalization template engine using {{placeholder}} syntax
"""

import re
import uuid
import asyncio
from typing import Dict, Optional, List
from datetime import datetime, date

from app.config import get_settings

settings = get_settings()


# ============================================
# DAILY SEND RATE LIMITER (Email Warming)
# ============================================

class DailySendLimiter:
    """
    In-memory tracker for daily email send volume.

    Email warming = sending small batches at first to build sender
    reputation with Gmail/Outlook/Yahoo before ramping up to full volume.
    This prevents your domain from being flagged as spam when you're new.

    Resets automatically at UTC midnight.
    Controlled by SENDGRID_DAILY_SEND_LIMIT in .env
    """

    def __init__(self):
        self._count: int = 0
        self._date: date = date.today()

    def _reset_if_new_day(self):
        today = date.today()
        if today != self._date:
            self._count = 0
            self._date = today

    def can_send(self) -> bool:
        self._reset_if_new_day()
        limit = settings.SENDGRID_DAILY_SEND_LIMIT
        if limit <= 0:
            return True  # 0 = unlimited
        return self._count < limit

    def record_send(self):
        self._reset_if_new_day()
        self._count += 1

    @property
    def remaining_today(self) -> int:
        self._reset_if_new_day()
        limit = settings.SENDGRID_DAILY_SEND_LIMIT
        if limit <= 0:
            return 999999
        return max(0, limit - self._count)

    @property
    def sent_today(self) -> int:
        self._reset_if_new_day()
        return self._count


# Module-level singleton — shared across all requests in the same process
_daily_limiter = DailySendLimiter()


# ============================================
# EMAIL SERVICE
# ============================================

class EmailService:


    # ----------------------------------------
    # TEMPLATE PERSONALIZATION
    # ----------------------------------------

    @staticmethod
    def personalize_template(template: str, lead_data: Dict) -> str:
        """
        Replace {{placeholders}} with actual lead data.

        Supported placeholders:
          {{first_name}}, {{last_name}}, {{full_name}},
          {{email}}, {{phone}}, {{address}},
          {{property_type}}, {{estimated_value}}, {{lead_id}}
        """
        placeholders = {
            "{{first_name}}":      lead_data.get("first_name", ""),
            "{{last_name}}":       lead_data.get("last_name", ""),
            "{{email}}":           lead_data.get("email", ""),
            "{{phone}}":           lead_data.get("phone", ""),
            "{{address}}":         lead_data.get("address", ""),
            "{{property_type}}":   lead_data.get("property_type", ""),
            "{{estimated_value}}": lead_data.get("estimated_value", ""),
            "{{lead_id}}":         str(lead_data.get("lead_id", "")),
            "{{full_name}}": (
                f"{lead_data.get('first_name', '')} "
                f"{lead_data.get('last_name', '')}".strip()
            ),
        }
        result = template
        for placeholder, value in placeholders.items():
            result = result.replace(placeholder, str(value) if value else "")
        return result

    @staticmethod
    def extract_placeholders(template: str) -> List[str]:
        """Return list of all {{placeholder}} names found in a template."""
        return re.findall(r'\{\{(\w+)\}\}', template)

    # ----------------------------------------
    # CORE SEND (auto-routes mock vs SendGrid)
    # ----------------------------------------

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None
    ) -> Dict:
        """
        Send a single email. Does NOT update the database.
        Use send_campaign_email() for campaign sends with DB tracking.

        Returns:
            {
              "success": bool,
              "message_id": str,
              "mode": "mock" | "sendgrid",
              "timestamp": str,
              "error": str   (only on failure)
            }
        """
        from_email = from_email or settings.SENDGRID_FROM_EMAIL

        if settings.sendgrid_configured:
            return await self._send_via_sendgrid(to_email, subject, body, from_email)
        else:
            return await self._send_mock(to_email, subject, body, from_email)

    # ----------------------------------------
    # PRODUCTION SEND WITH DB TRACKING + RETRY
    # ----------------------------------------

    async def send_campaign_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        sequence_id: int,
        db,
        from_email: Optional[str] = None,
        max_retries: int = 3,
    ) -> Dict:
        """
        Production email send with full DB tracking and retry logic.

        Use this in campaigns instead of send_email() directly.

        What this does beyond send_email():
          1. Checks daily send limit (email warming protection)
          2. Retries up to 3 times with exponential backoff on failure
          3. Saves the SendGrid message_id to the EmailSequence DB row
             so webhook events (opens, clicks, bounces) can be matched

        WHY the message_id matters:
          When SendGrid fires a webhook for "John opened your email",
          it sends us the message_id. We look up that message_id in
          the email_sequences table to find which lead/campaign it belongs to,
          then update opened_at, clicked_at, etc.
          Without saving the message_id here, webhooks are useless.

        Args:
            sequence_id: The EmailSequence.id to update with the message_id
            db:          Active AsyncSession — the caller handles commit
        """
        # ---- Daily limit check ----
        if not _daily_limiter.can_send():
            msg = (
                f"Daily send limit reached ({settings.SENDGRID_DAILY_SEND_LIMIT}/day). "
                f"Increase SENDGRID_DAILY_SEND_LIMIT in .env or wait until tomorrow UTC."
            )
            print(f"⛔ {msg}")
            return {
                "success": False,
                "error": msg,
                "skipped_daily_limit": True,
                "mode": "sendgrid" if settings.sendgrid_configured else "mock",
                "timestamp": datetime.utcnow().isoformat()
            }

        # ---- Send with retry and exponential backoff ----
        last_result: Dict = {}

        for attempt in range(1, max_retries + 1):
            last_result = await self.send_email(to_email, subject, body, from_email)

            if last_result.get("success"):
                _daily_limiter.record_send()

                # ---- CRITICAL: Save message_id to DB ----
                # This links SendGrid events back to our EmailSequence rows.
                if sequence_id and db:
                    await self._persist_message_id(
                        db=db,
                        sequence_id=sequence_id,
                        message_id=last_result["message_id"]
                    )

                return last_result

            # Failed — retry with backoff
            if attempt < max_retries:
                wait_seconds = 2 ** (attempt - 1)   # 1s, 2s, 4s
                print(
                    f"⚠️  Send attempt {attempt}/{max_retries} failed for {to_email}. "
                    f"Retrying in {wait_seconds}s... "
                    f"(error: {last_result.get('error')})"
                )
                await asyncio.sleep(wait_seconds)
            else:
                print(
                    f"❌ All {max_retries} send attempts failed for {to_email}. "
                    f"Last error: {last_result.get('error')}"
                )

        return last_result

    async def _persist_message_id(self, db, sequence_id: int, message_id: str):
        """
        Save the SendGrid message_id to the EmailSequence row.
        Called after a successful send in send_campaign_email().
        Note: caller is responsible for db.commit().
        """
        try:
            from sqlalchemy import select
            from app.models import EmailSequence

            result = await db.execute(
                select(EmailSequence).where(EmailSequence.id == sequence_id)
            )
            sequence = result.scalar_one_or_none()

            if sequence:
                sequence.sendgrid_message_id = message_id
                sequence.status = "sent"
                sequence.sent_at = datetime.utcnow()
                sequence.updated_at = datetime.utcnow()
                print(f"💾 Saved message_id '{message_id}' → sequence {sequence_id}")
            else:
                print(f"⚠️  EmailSequence {sequence_id} not found — message_id not saved")

        except Exception as e:
            # Log but don't fail the send response
            print(f"⚠️  Failed to persist message_id to sequence {sequence_id}: {e}")

    # ----------------------------------------
    # BULK SEND (no DB tracking)
    # ----------------------------------------

    async def send_bulk(
        self,
        emails: List[Dict],
        subject_template: str,
        body_template: str
    ) -> Dict:
        """
        Send personalized emails to a list of lead dicts.
        No DB tracking — for campaign sends use send_campaign_email() per lead.
        """
        results = {"total": len(emails), "sent": 0, "failed": 0, "details": []}

        for lead_data in emails:
            to_email = lead_data.get("email")
            subject = self.personalize_template(subject_template, lead_data)
            body = self.personalize_template(body_template, lead_data)
            result = await self.send_email(to_email, subject, body)

            if result.get("success"):
                results["sent"] += 1
            else:
                results["failed"] += 1

            results["details"].append({
                "email": to_email,
                "success": result.get("success"),
                "message_id": result.get("message_id"),
                "error": result.get("error")
            })

        return results

    # ----------------------------------------
    # SEND STATUS (for dashboard)
    # ----------------------------------------

    def get_send_status(self) -> Dict:
        """Returns current daily send status. Use on dashboard endpoint."""
        return {
            "sent_today": _daily_limiter.sent_today,
            "remaining_today": _daily_limiter.remaining_today,
            "daily_limit": settings.SENDGRID_DAILY_SEND_LIMIT,
            "unlimited": settings.SENDGRID_DAILY_SEND_LIMIT <= 0,
            "mode": "sendgrid" if settings.sendgrid_configured else "mock"
        }

    # ----------------------------------------
    # PRIVATE: MOCK SEND
    # ----------------------------------------

    async def _send_mock(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_email: Optional[str]
    ) -> Dict:
        """Mock send — logs to console, no real email sent."""
        message_id = f"mock_{uuid.uuid4().hex[:12]}"

        print("\n" + "=" * 60)
        print("📧 MOCK EMAIL (Demo Mode — configure SendGrid to send real emails)")
        print("=" * 60)
        print(f"  From:    {from_email or 'noreply@demo.com'}")
        print(f"  To:      {to_email}")
        print(f"  Subject: {subject}")
        print("-" * 60)
        preview = body[:300] + "..." if len(body) > 300 else body
        print(f"  Body:\n{preview}")
        print("=" * 60)
        print(f"  Message ID : {message_id}")
        print(f"  Timestamp  : {datetime.utcnow().isoformat()}Z")
        print("=" * 60 + "\n")

        return {
            "success": True,
            "message_id": message_id,
            "mode": "mock",
            "timestamp": datetime.utcnow().isoformat()
        }

    # ----------------------------------------
    # PRIVATE: SENDGRID SEND
    # ----------------------------------------

    async def _send_via_sendgrid(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_email: Optional[str]
    ) -> Dict:
        """Send via SendGrid API. Only called when API key + from_email are configured."""
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Email, To, Content

            message = Mail(
                from_email=Email(from_email, settings.SENDGRID_FROM_NAME),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", body)
            )

            sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
            response = sg.send(message)

            message_id = response.headers.get(
                "X-Message-Id",
                f"sg_{uuid.uuid4().hex[:12]}"
            )

            print(f"✅ Email sent → {to_email} | ID: {message_id} | Status: {response.status_code}")

            return {
                "success": True,
                "message_id": message_id,
                "mode": "sendgrid",
                "status_code": response.status_code,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            error_msg = str(e)
            print(f"❌ SendGrid error sending to {to_email}: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "mode": "sendgrid",
                "timestamp": datetime.utcnow().isoformat()
            }


# ============================================
# SINGLETON INSTANCE
# ============================================

email_service = EmailService()
