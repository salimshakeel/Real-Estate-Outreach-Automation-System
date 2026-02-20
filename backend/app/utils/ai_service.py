

from typing import Dict, List, Any, Optional
import json

from openai import AsyncOpenAI

from app.config import get_settings


settings = get_settings()


class AIService:
    """
    Central AI service for the backend.

    In production, this will call external LLM APIs (OpenAI/Anthropic).
    For now, it supports a safe demo mode when OPENAI is not configured.
    """

    def __init__(self) -> None:
        self.openai_configured = settings.openai_configured
        # These can be extended later when wiring real LLMs
        self.primary_model = getattr(settings, "OPENAI_MODEL", "gpt-4.1")
        self.fallback_model = "gpt-3.5-turbo"
        self._openai_client: Optional[AsyncOpenAI] = None

        # Lazily initialize OpenAI client (only when key exists)
        if settings.OPENAI_API_KEY:
            self._openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    def _safe_next_action_type(self, value: Optional[str]) -> str:
        allowed = {"continue", "book_meeting", "escalate_human", "end"}
        return value if value in allowed else "continue"

    def _parse_ai_json(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Attempt to parse a JSON object from an LLM response.
        Returns None if parsing fails.
        """
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                return data
        except Exception:
            return None
        return None

    async def _openai_chatbot_json(
        self,
        lead_context: Dict[str, Any],
        messages: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """
        Call OpenAI and return normalized chatbot JSON:
        { reply, next_action: {type, reason}, updated_lead_score }
        """
        if not self._openai_client:
            raise RuntimeError("OpenAI client not initialized")

        first_name = lead_context.get("first_name") or "there"
        company = lead_context.get("company") or ""
        industry = lead_context.get("industry") or ""
        lead_score = lead_context.get("lead_score")
        source = lead_context.get("source") or ""
        last_email_summary = lead_context.get("last_email_summary") or ""

        system_prompt = (
            "You are a friendly, concise sales assistant. Your job is to qualify leads and help book demos.\n"
            "Rules:\n"
            "- Ask ONE question at a time.\n"
            "- Keep responses under 50 words.\n"
            "- If asked about pricing, qualify first (team size + use case).\n"
            "- If the user wants a demo/call, suggest booking.\n"
            "- If the user is frustrated or requests a human, escalate.\n"
            "- Never promise unbuilt features. Never offer discounts.\n\n"
            "Return ONLY a JSON object with this exact shape:\n"
            "{\n"
            '  "reply": string,\n'
            '  "next_action": {"type": "continue|book_meeting|escalate_human|end", "reason": string},\n'
            '  "updated_lead_score": number or null\n'
            "}\n\n"
            "Context:\n"
            f"- Lead first name: {first_name}\n"
            f"- Company: {company}\n"
            f"- Industry: {industry}\n"
            f"- Current lead score: {lead_score}\n"
            f"- Trigger source: {source}\n"
            f"- Last email summary: {last_email_summary}\n"
        )

        # Keep only last ~10 messages for cost control
        trimmed = messages[-10:] if len(messages) > 10 else messages
        openai_messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
        for m in trimmed:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role not in {"user", "assistant", "system"}:
                role = "user"
            openai_messages.append({"role": role, "content": content})

        resp = await self._openai_client.chat.completions.create(
            model=settings.OPENAI_MODEL or self.primary_model,
            messages=openai_messages,
            temperature=0.4,
        )

        text = (resp.choices[0].message.content or "").strip()
        parsed = self._parse_ai_json(text)

        # If model didn't return JSON, fallback to a safe wrapper
        if not parsed:
            return {
                "reply": text or "Thanks — could you share your biggest outreach challenge right now?",
                "next_action": {"type": "continue", "reason": "LLM returned non-JSON; default to continue."},
                "updated_lead_score": lead_score,
            }

        next_action = parsed.get("next_action") or {}
        action_type = self._safe_next_action_type(next_action.get("type"))

        return {
            "reply": str(parsed.get("reply") or "").strip() or "What’s your biggest challenge with outreach right now?",
            "next_action": {
                "type": action_type,
                "reason": str(next_action.get("reason") or "").strip() or None,
            },
            "updated_lead_score": parsed.get("updated_lead_score", lead_score),
        }

    async def generate_chatbot_reply(
        self,
        lead_context: Dict[str, Any],
        messages: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """
        Generate a chatbot reply and next action.

        Return format:
        {
          "reply": str,
          "next_action": {"type": "...", "reason": "..."},
          "updated_lead_score": int | None
        }

        In demo mode (no OpenAI configured), this returns a simple,
        deterministic response so the API is still usable.
        """
        # Normalized last user message (used by both demo and "real" branches)
        last_user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_message = msg.get("content", "")
                break

        first_name = lead_context.get("first_name") or "there"
        normalized = last_user_message.lower()

        # --- DEMO MODE: simple rule-based engine, no external calls ---
        if not self.openai_configured:
            base_reply = (
                f"Hi {first_name}, I'm here to answer questions about our outreach system. "
                "Could you tell me a bit about your biggest challenge with booking meetings right now?"
            )

            # Pricing intent
            if "price" in normalized or "pricing" in normalized or "$" in normalized:
                base_reply = (
                    "Great question on pricing. Before that, how many people on your team "
                    "would use this outreach system?"
                )
            # Demo / call intent
            elif "demo" in normalized or "call" in normalized or "meeting" in normalized:
                return {
                    "reply": "Sounds good. I can help arrange a quick demo. Do you prefer earlier this week or later?",
                    "next_action": {
                        "type": "book_meeting",
                        "reason": "User mentioned demo/call/meeting – suggest booking.",
                    },
                    "updated_lead_score": max((lead_context.get("lead_score") or 50) + 10, 0),
                }
            # Frustration / escalation
            elif any(w in normalized for w in ["frustrated", "angry", "upset", "this is not helpful"]):
                return {
                    "reply": "I’m sorry this hasn’t been helpful so far. I can connect you with a human specialist if you’d like.",
                    "next_action": {
                        "type": "escalate_human",
                        "reason": "Frustration detected – recommend human handoff.",
                    },
                    "updated_lead_score": lead_context.get("lead_score"),
                }
            # Conversation end
            elif any(w in normalized for w in ["thanks, that's all", "thank you, that's all", "no more questions"]):
                return {
                    "reply": "Glad I could help. If anything else comes up, you can reach out here again anytime.",
                    "next_action": {
                        "type": "end",
                        "reason": "User indicated conversation is finished.",
                    },
                    "updated_lead_score": lead_context.get("lead_score"),
                }

            return {
                "reply": base_reply,
                "next_action": {
                    "type": "continue",
                    "reason": "Demo mode fallback reply – keep conversation going.",
                },
                "updated_lead_score": lead_context.get("lead_score"),
            }

        # --- REAL LLM BRANCH (OpenAI) ---
        # If OPENAI_API_KEY is configured, call OpenAI and return JSON-structured output.
        if self._openai_client:
            try:
                return await self._openai_chatbot_json(lead_context=lead_context, messages=messages)
            except Exception:
                # If LLM fails for any reason, fall back to safe deterministic behavior below.
                pass

        # Fallback if OpenAI is configured but call fails
        reply = (
            f"Hi {first_name}, thanks for reaching out. "
            "To make sure this fits, what are you currently using for outreach?"
        )

        if "demo" in normalized or "call" in normalized or "meeting" in normalized:
            return {
                "reply": "Happy to set something up. Would mid-week work better, or are you free earlier?",
                "next_action": {
                    "type": "book_meeting",
                    "reason": "User requested demo/call – suggest booking.",
                },
                "updated_lead_score": max((lead_context.get("lead_score") or 50) + 10, 0),
            }

        if "price" in normalized or "pricing" in normalized or "$" in normalized:
            return {
                "reply": "Pricing depends a bit on team size and volume. Roughly how many people would use this day to day?",
                "next_action": {
                    "type": "continue",
                    "reason": "Pricing question – ask qualifying team-size question.",
                },
                "updated_lead_score": lead_context.get("lead_score"),
            }

        return {
            "reply": reply,
            "next_action": {
                "type": "continue",
                "reason": "Standard qualification question.",
            },
            "updated_lead_score": lead_context.get("lead_score"),
        }


# Singleton instance used by routers
ai_service = AIService()

