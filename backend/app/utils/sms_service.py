"""
SMS Service (Step 3)
====================
Sends SMS via Twilio. Same vendor as SendGrid (Twilio owns SendGrid).

Modes:
  - Mock (demo): Logs to console, no real SMS sent
  - Production:  Sends via Twilio REST API, stores SID for status callbacks

Placeholders: Same as email — {{first_name}}, {{lead_id}}, etc.
"""

import asyncio

from app.config import get_settings

settings = get_settings()

# Lazy Twilio client (only when configured)
_twilio_client = None


def _get_twilio_client():
    """Return Twilio client or None if not configured."""
    global _twilio_client
    if _twilio_client is not None:
        return _twilio_client
    if not settings.twilio_configured:
        return None
    try:
        from twilio.rest import Client

        _twilio_client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN,
        )
        return _twilio_client
    except Exception:
        return None


def personalize_body(template: str, lead_data: dict) -> str:
    """
    Replace {{placeholders}} in SMS body with lead data.
    Same placeholders as email: first_name, last_name, full_name, email, phone,
    address, property_type, estimated_value, lead_id.
    """
    placeholders = {
        "{{first_name}}": lead_data.get("first_name", ""),
        "{{last_name}}": lead_data.get("last_name", ""),
        "{{email}}": lead_data.get("email", ""),
        "{{phone}}": lead_data.get("phone", ""),
        "{{address}}": lead_data.get("address", ""),
        "{{property_type}}": lead_data.get("property_type", ""),
        "{{estimated_value}}": lead_data.get("estimated_value", ""),
        "{{lead_id}}": str(lead_data.get("lead_id", "")),
        "{{full_name}}": (f"{lead_data.get('first_name', '')} " f"{lead_data.get('last_name', '')}".strip()),
    }
    result = template
    for placeholder, value in placeholders.items():
        result = result.replace(placeholder, str(value) if value else "")
    return result


def normalize_phone(phone: str) -> str:
    """
    Ensure phone is E.164 for Twilio (e.g. +15551234567).
    If already has +, return as-is (strip spaces). Otherwise prepend +1 for US.
    """
    if not phone:
        return ""
    cleaned = "".join(c for c in phone if c.isdigit() or c == "+").strip()
    if cleaned.startswith("+"):
        return cleaned
    if len(cleaned) == 10:
        return f"+1{cleaned}"
    if len(cleaned) == 11 and cleaned.startswith("1"):
        return f"+{cleaned}"
    return f"+{cleaned}" if cleaned else ""


class SmsService:
    """
    Send SMS via Twilio. When not configured, logs to console (demo mode).
    """

    def __init__(self) -> None:
        self.twilio_configured = settings.twilio_configured

    async def send_sms(
        self,
        to_phone: str,
        body: str,
        lead_id: int | None = None,
    ) -> dict[str, str | None]:
        """
        Send one SMS. Returns dict with keys: sid, status, error.

        - If Twilio is configured: calls Twilio API, returns twilio_sid and status.
        - If not: logs and returns sid=None, status="mock", error=None.
        """
        to_e164 = normalize_phone(to_phone)
        if not to_e164:
            return {
                "sid": None,
                "status": "failed",
                "error": "Invalid or missing phone number",
            }

        # SMS length: Twilio concatenates long messages; we just send.
        if not body or len(body.strip()) == 0:
            return {
                "sid": None,
                "status": "failed",
                "error": "Message body is empty",
            }

        client = _get_twilio_client()
        if not client:
            print(f"[SMS MOCK] To: {to_e164} | Body: {body[:80]}...")
            return {"sid": None, "status": "mock", "error": None}

        def _send():
            return client.messages.create(
                body=body,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=to_e164,
            )

        try:
            message = await asyncio.to_thread(_send)
            return {
                "sid": message.sid,
                "status": message.status or "sent",
                "error": None,
            }
        except Exception as e:
            err_msg = str(e)
            return {
                "sid": None,
                "status": "failed",
                "error": err_msg,
            }


# Singleton for routers
sms_service = SmsService()
