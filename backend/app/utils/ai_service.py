import json
from typing import Any

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
        self._openai_client: AsyncOpenAI | None = None

        # Lazily initialize OpenAI client (only when key exists)
        if settings.OPENAI_API_KEY:
            self._openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    def _safe_next_action_type(self, value: str | None) -> str:
        allowed = {"continue", "book_meeting", "escalate_human", "end"}
        return value if value in allowed else "continue"

    def _parse_ai_json(self, text: str) -> dict[str, Any] | None:
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
        lead_context: dict[str, Any],
        messages: list[dict[str, str]],
    ) -> dict[str, Any]:
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
        openai_messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
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
        lead_context: dict[str, Any],
        messages: list[dict[str, str]],
    ) -> dict[str, Any]:
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


# ---------------------------------------------------------------------------
# Standalone async LLM utility functions (used by routers, not class methods)
# ---------------------------------------------------------------------------


async def generate_email_variations(
    brief: dict,
    learned_patterns: list[str],
) -> dict:
    """Generate 5 email variations (A–E) based on a creative brief and
    previously learned patterns from A/B testing."""

    target_audience = brief.get("target_audience", "real estate professionals")
    goal = brief.get("goal", "book a meeting")
    pain_point = brief.get("pain_point", "low response rates")
    tone = brief.get("tone", "professional yet friendly")
    max_word_count = brief.get("max_word_count", 150)

    if not ai_service.openai_configured or not ai_service._openai_client:
        labels = ["A", "B", "C", "D", "E"]
        triggers = ["curiosity", "urgency", "social_proof", "fear_of_missing_out", "authority"]
        variations = [
            {
                "label": lbl,
                "subject": f"[Demo] Variation {lbl} – {pain_point.title()}",
                "body": (
                    f"Hi {{{{first_name}}}},\n\n"
                    f"Are you struggling with {pain_point}? "
                    f"We help {target_audience} {goal} faster.\n\n"
                    f"Would a quick 15-min call this week work?\n\n"
                    f"Best,\nThe Outreach Team"
                ),
                "psychological_trigger": triggers[i],
            }
            for i, lbl in enumerate(labels)
        ]
        return {"variations": variations, "patterns_used": len(learned_patterns)}

    patterns_block = "\n".join(f"- {p}" for p in learned_patterns) if learned_patterns else "None yet."

    system_prompt = (
        "You are an expert email copywriter for B2B real-estate outreach.\n"
        "Return ONLY a JSON object with this shape:\n"
        '{"variations": [{"label":"A","subject":"...","body":"...","psychological_trigger":"..."}, ...]}\n'
        "Generate exactly 5 variations labelled A through E.\n"
        "Each body must be under " + str(max_word_count) + " words.\n"
        "Use a different psychological trigger for each (curiosity, urgency, social_proof, fear_of_missing_out, authority)."
    )
    user_prompt = (
        f"Target audience: {target_audience}\n"
        f"Goal: {goal}\n"
        f"Pain point: {pain_point}\n"
        f"Tone: {tone}\n"
        f"Learned patterns from past A/B tests:\n{patterns_block}"
    )

    try:
        resp = await ai_service._openai_client.chat.completions.create(
            model=settings.OPENAI_MODEL or ai_service.primary_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
        )
        text = (resp.choices[0].message.content or "").strip()
        parsed = ai_service._parse_ai_json(text)
        if not parsed or "variations" not in parsed:
            return await generate_email_variations(brief, [])  # retry w/o patterns → hits demo
        parsed["patterns_used"] = len(learned_patterns)
        return parsed
    except Exception:
        return {
            "variations": [],
            "patterns_used": len(learned_patterns),
        }


async def analyze_ab_test(
    variations_data: list[dict],
) -> dict:
    """Analyze A/B test results with weighted scoring and pick a winner."""

    if not ai_service.openai_configured or not ai_service._openai_client:
        winner = max(variations_data, key=lambda v: v.get("replies", 0)) if variations_data else {}
        return {
            "winner_label": winner.get("label", "A"),
            "explanation": (
                f"Variation {winner.get('label', 'A')} had the highest reply count "
                f"({winner.get('replies', 0)} replies) among all tested variations."
            ),
            "pattern_learned": (
                "Subject lines that reference specific pain points tend to "
                "generate more replies in real-estate outreach."
            ),
        }

    rows = "\n".join(
        f"- {v.get('label')}: subject=\"{v.get('subject','')}\", "
        f"sends={v.get('sends',0)}, opens={v.get('opens',0)}, "
        f"clicks={v.get('clicks',0)}, replies={v.get('replies',0)}"
        for v in variations_data
    )

    system_prompt = (
        "You are a data-driven email marketing analyst.\n"
        "Score each variation using weighted scoring: replies 50%, opens 30%, clicks 20%.\n"
        "Return ONLY a JSON object:\n"
        '{"winner_label": "X", "explanation": "...", "pattern_learned": "..."}\n'
        "The pattern_learned should be a reusable insight for future campaigns."
    )
    user_prompt = f"A/B test results:\n{rows}"

    try:
        resp = await ai_service._openai_client.chat.completions.create(
            model=settings.OPENAI_MODEL or ai_service.primary_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
        )
        text = (resp.choices[0].message.content or "").strip()
        parsed = ai_service._parse_ai_json(text)
        if not parsed or "winner_label" not in parsed:
            winner = max(variations_data, key=lambda v: v.get("replies", 0)) if variations_data else {}
            return {
                "winner_label": winner.get("label", "A"),
                "explanation": "LLM response could not be parsed; fell back to highest reply count.",
                "pattern_learned": "N/A",
            }
        return parsed
    except Exception:
        winner = max(variations_data, key=lambda v: v.get("replies", 0)) if variations_data else {}
        return {
            "winner_label": winner.get("label", "A"),
            "explanation": "Analysis unavailable due to an internal error; selected by highest reply count.",
            "pattern_learned": "N/A",
        }


async def score_lead(
    lead_data: dict,
    icp_description: str | None = None,
    available_campaigns: list[str] | None = None,
) -> dict:
    """Score a lead 0-100, assign a priority tier, recommend a real campaign,
    and generate actionable personalization hints."""

    campaigns_list = available_campaigns or []

    def _demo_score(ld: dict) -> dict:
        score = 30
        if ld.get("phone"):
            score += 10
        if ld.get("address"):
            score += 10
        est = ld.get("estimated_value") or 0
        if isinstance(est, str):
            est = float(est.replace("$", "").replace(",", "") or 0)
        if est > 500_000:
            score += 20
        if ld.get("property_type"):
            score += 5
        if ld.get("company"):
            score += 5

        score = min(score, 100)
        if score >= 75:
            priority = "Hot"
        elif score >= 50:
            priority = "Warm"
        elif score >= 25:
            priority = "Cold"
        else:
            priority = "Dead"

        rec_campaign = campaigns_list[0] if campaigns_list else "general-outreach"
        prop = ld.get("property_type", "property")
        addr = ld.get("address", "their area")

        return {
            "score": score,
            "priority": priority,
            "reasoning": f"Rule-based demo score for {ld.get('first_name', 'lead')}.",
            "recommended_campaign": rec_campaign,
            "personalization_hints": (
                f"Reference their {prop} property in {addr}. "
                f"Lead with ROI angle if value is above $500K, "
                f"or market-trend angle for mid-range properties."
            ),
        }

    if not ai_service.openai_configured or not ai_service._openai_client:
        return _demo_score(lead_data)

    lead_block = "\n".join(f"- {k}: {v}" for k, v in lead_data.items() if v)
    icp_block = icp_description or "No specific ICP provided."
    campaigns_block = (
        "\n".join(f"- {c}" for c in campaigns_list) if campaigns_list
        else "No campaigns exist yet — suggest a campaign type name."
    )

    system_prompt = (
        "You are a lead-scoring engine for real-estate outreach.\n"
        "Return ONLY a JSON object:\n"
        '{"score": <0-100>, "priority": "Hot|Warm|Cold|Dead", '
        '"reasoning": "...", "recommended_campaign": "...", "personalization_hints": "..."}\n\n'
        "Score criteria: completeness of data, estimated property value, "
        "match to the ideal customer profile, and engagement potential.\n\n"
        "recommended_campaign: Pick the BEST matching campaign from the "
        "available campaigns list. If none fit, suggest a descriptive name.\n\n"
        "personalization_hints: Write 2-3 specific, actionable sentences a "
        "salesperson can use when emailing this lead. Reference their property "
        "type, location, estimated value, and any unique angle that would "
        "resonate with them. Be concrete — not generic advice."
    )
    user_prompt = (
        f"Lead data:\n{lead_block}\n\n"
        f"Ideal Customer Profile:\n{icp_block}\n\n"
        f"Available campaigns:\n{campaigns_block}"
    )

    try:
        resp = await ai_service._openai_client.chat.completions.create(
            model=settings.OPENAI_MODEL or ai_service.primary_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
        )
        text = (resp.choices[0].message.content or "").strip()
        parsed = ai_service._parse_ai_json(text)
        if not parsed or "score" not in parsed:
            return _demo_score(lead_data)
        parsed.setdefault("priority", "Warm")
        parsed.setdefault("reasoning", "")
        parsed.setdefault("recommended_campaign",
                          campaigns_list[0] if campaigns_list else "general-outreach")
        parsed.setdefault("personalization_hints", "")
        return parsed
    except Exception:
        return _demo_score(lead_data)


async def generate_personalization_hints(
    lead_data: dict,
    campaign_goal: str,
) -> dict:
    """Suggest a personalization angle given lead data and campaign goal."""

    property_type = lead_data.get("property_type", "property")
    city = lead_data.get("city") or lead_data.get("address", "their area")

    if not ai_service.openai_configured or not ai_service._openai_client:
        return {
            "hints": (
                f"Reference their property type ({property_type}) and local "
                f"market conditions in {city}. Lead with ROI angle."
            ),
        }

    lead_block = "\n".join(f"- {k}: {v}" for k, v in lead_data.items() if v)

    system_prompt = (
        "You are a personalization strategist for real-estate email outreach.\n"
        "Return ONLY a JSON object:\n"
        '{"hints": "..."}\n'
        "The hints field should be 1-3 sentences of actionable personalization advice."
    )
    user_prompt = (
        f"Lead data:\n{lead_block}\n\n"
        f"Campaign goal: {campaign_goal}"
    )

    try:
        resp = await ai_service._openai_client.chat.completions.create(
            model=settings.OPENAI_MODEL or ai_service.primary_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
        )
        text = (resp.choices[0].message.content or "").strip()
        parsed = ai_service._parse_ai_json(text)
        if not parsed or "hints" not in parsed:
            return {
                "hints": f"Reference their {property_type} property and local market conditions in {city}.",
            }
        return parsed
    except Exception:
        return {
            "hints": f"Reference their {property_type} property and local market conditions in {city}.",
        }


async def generate_weekly_insights(
    stats: dict,
) -> dict:
    """Generate a plain-English weekly performance summary with highlights
    and recommendations."""

    if not ai_service.openai_configured or not ai_service._openai_client:
        emails_sent = stats.get("emails_sent", 0)
        opens = stats.get("opens", 0)
        replies = stats.get("replies", 0)
        open_rate = stats.get("open_rate", 0)
        reply_rate = stats.get("reply_rate", 0)
        return {
            "summary": (
                f"This week you sent {emails_sent} emails with a {open_rate:.1f}% open rate "
                f"and {reply_rate:.1f}% reply rate. You received {replies} replies and "
                f"{stats.get('bookings', 0)} bookings."
            ),
            "highlights": [
                f"Total emails sent: {emails_sent}",
                f"Open rate: {open_rate:.1f}%",
                f"Reply rate: {reply_rate:.1f}%",
                f"Top campaign: {stats.get('top_campaign', 'N/A')}",
            ],
            "recommendations": [
                "Test subject-line variations to lift open rates.",
                "Follow up with non-openers after 48 hours.",
                "Consider adding SMS touchpoints for high-value leads.",
            ],
        }

    stats_block = "\n".join(f"- {k}: {v}" for k, v in stats.items())

    system_prompt = (
        "You are a marketing analytics assistant for a real-estate outreach platform.\n"
        "Return ONLY a JSON object:\n"
        '{"summary": "...", "highlights": ["...", "..."], "recommendations": ["...", "..."]}\n'
        "summary: 2-3 sentence plain-English overview.\n"
        "highlights: 3-5 bullet strings of notable data points.\n"
        "recommendations: 2-4 actionable suggestions for next week."
    )
    user_prompt = f"Weekly stats:\n{stats_block}"

    try:
        resp = await ai_service._openai_client.chat.completions.create(
            model=settings.OPENAI_MODEL or ai_service.primary_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
        )
        text = (resp.choices[0].message.content or "").strip()
        parsed = ai_service._parse_ai_json(text)
        if not parsed or "summary" not in parsed:
            return await generate_weekly_insights(stats={})  # safe demo fallback
        parsed.setdefault("highlights", [])
        parsed.setdefault("recommendations", [])
        return parsed
    except Exception:
        return {
            "summary": "Weekly insights could not be generated due to an internal error.",
            "highlights": [],
            "recommendations": ["Retry insights generation later."],
        }


async def analyze_campaign_performance(
    campaign_data: dict,
) -> dict:
    """Analyze a single campaign's aggregate stats and return a plain-English
    summary with an actionable suggestion."""

    name = campaign_data.get("name", "Campaign")

    if not ai_service.openai_configured or not ai_service._openai_client:
        sends = campaign_data.get("sends", 0)
        opens = campaign_data.get("opens", 0)
        replies = campaign_data.get("replies", 0)
        open_pct = (opens / sends * 100) if sends else 0
        reply_pct = (replies / sends * 100) if sends else 0
        return {
            "analysis": (
                f"{name} sent {sends} emails with a {open_pct:.1f}% open rate "
                f"and {reply_pct:.1f}% reply rate."
            ),
            "suggestion": (
                "Try refreshing the subject line or adjusting send times "
                "to improve engagement."
            ),
        }

    stats_block = "\n".join(f"- {k}: {v}" for k, v in campaign_data.items())

    system_prompt = (
        "You are a campaign performance analyst for real-estate outreach.\n"
        "Return ONLY a JSON object:\n"
        '{"analysis": "...", "suggestion": "..."}\n'
        "analysis: 2-3 sentences summarising performance.\n"
        "suggestion: 1-2 sentences with a concrete next step."
    )
    user_prompt = f"Campaign data:\n{stats_block}"

    try:
        resp = await ai_service._openai_client.chat.completions.create(
            model=settings.OPENAI_MODEL or ai_service.primary_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
        )
        text = (resp.choices[0].message.content or "").strip()
        parsed = ai_service._parse_ai_json(text)
        if not parsed or "analysis" not in parsed:
            return {
                "analysis": f"{name} performance data could not be analyzed by the LLM.",
                "suggestion": "Review raw metrics manually and adjust targeting.",
            }
        return parsed
    except Exception:
        return {
            "analysis": f"Analysis for {name} is unavailable due to an internal error.",
            "suggestion": "Retry later or review metrics in the dashboard.",
        }
