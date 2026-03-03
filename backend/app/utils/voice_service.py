"""
Voice Service (Step 4)
======================
Makes outbound AI voice calls via Retell AI + Twilio SIP trunk.

Architecture:
  Twilio owns the phone number → SIP trunk routes to Retell →
  Retell runs the AI agent conversation → our backend triggers
  calls via Retell's Create Phone Call API and receives results
  via webhook.

Modes:
  - Mock (demo): Logs call, returns fake call_id.
  - Production: Calls Retell API, returns real call_id.
"""

import httpx

from app.config import get_settings

settings = get_settings()

RETELL_API_BASE = "https://api.retellai.com"


def _normalize_phone(phone: str) -> str:
    """E.164 normalization (same logic as sms_service)."""
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


class VoiceService:
    """Trigger outbound voice calls via Retell AI."""

    def __init__(self) -> None:
        self.configured = settings.retell_configured

    async def start_call(
        self,
        to_phone: str,
        lead_id: int | None = None,
        dynamic_vars: dict[str, str] | None = None,
    ) -> dict[str, str | None]:
        """
        Initiate an outbound call to `to_phone`.

        `dynamic_vars` are injected into the Retell agent prompt at runtime,
        e.g. {"first_name": "James", "property_address": "120 Maple Drive"}.

        Returns: { call_id, status, error }
        """
        to_e164 = _normalize_phone(to_phone)
        if not to_e164:
            return {"call_id": None, "status": "failed", "error": "Invalid or missing phone number"}

        if not self.configured:
            print(f"[VOICE MOCK] Outbound call to {to_e164} | lead_id={lead_id}")
            return {"call_id": None, "status": "mock", "error": None}

        payload: dict = {
            "from_number": settings.RETELL_FROM_NUMBER,
            "to_number": to_e164,
        }
        if settings.RETELL_AGENT_ID:
            payload["override_agent_id"] = settings.RETELL_AGENT_ID
        if dynamic_vars:
            payload["retell_llm_dynamic_variables"] = dynamic_vars

        headers = {
            "Authorization": f"Bearer {settings.RETELL_API_KEY}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{RETELL_API_BASE}/v2/create-phone-call",
                    json=payload,
                    headers=headers,
                )
            if resp.status_code in (200, 201):
                data = resp.json()
                return {
                    "call_id": data.get("call_id"),
                    "status": data.get("call_status", "calling"),
                    "error": None,
                }
            return {
                "call_id": None,
                "status": "failed",
                "error": f"Retell API {resp.status_code}: {resp.text[:300]}",
            }
        except Exception as e:
            return {"call_id": None, "status": "failed", "error": str(e)}

    async def get_call(self, call_id: str) -> dict | None:
        """Fetch call details from Retell (status, transcript, duration, recording)."""
        if not self.configured or not call_id:
            return None

        headers = {
            "Authorization": f"Bearer {settings.RETELL_API_KEY}",
        }
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    f"{RETELL_API_BASE}/v2/get-call/{call_id}",
                    headers=headers,
                )
            if resp.status_code == 200:
                return resp.json()
            return None
        except Exception:
            return None


voice_service = VoiceService()
