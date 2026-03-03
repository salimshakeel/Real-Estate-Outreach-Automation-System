# Frontend API Documentation — New Endpoints Only

**Base URL:** `http://localhost:8000`

This document covers **only the new endpoints** added after the initial CRUD system. These are: AI Lead Scoring, AI Campaign Generation & A/B Testing, Chatbot, SMS, Voice Calls, AI Weekly Insights, Demo Utilities, and Webhooks.

The previous endpoints (Leads CRUD, Templates CRUD, Campaigns CRUD, basic Dashboard) are already documented separately and remain unchanged.

---

# Table of Contents

1. [AI Lead Scoring](#1-ai-lead-scoring)
2. [AI Campaign Generation & A/B Testing](#2-ai-campaign-generation--ab-testing)
3. [Chatbot](#3-chatbot)
4. [SMS](#4-sms)
5. [Voice Calls](#5-voice-calls)
6. [AI Weekly Insights](#6-ai-weekly-insights)
7. [Config Update](#7-config-update)
8. [Demo Utilities](#8-demo-utilities)
9. [Webhooks](#9-webhooks)
10. [New Data Models & Status Values](#10-new-data-models--status-values)
11. [Frontend Integration Guide](#11-frontend-integration-guide)

---

# 1. AI Lead Scoring

Scores leads using AI against an ideal customer profile. With OpenAI configured, the LLM reasons about each lead. Without it, a rule-based fallback runs (phone +10, address +10, value >$500K +20, etc.).

Scores are persisted in the `ai_lead_scores` table — one row per lead, upserted on each call.

---

## POST `/api/leads/score`

Score a single lead.

**Request:**
```json
{
  "lead_id": 1,
  "icp_description": "Commercial property managers in South Florida with portfolios above $500K"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| lead_id | int | Yes | Lead to score |
| icp_description | string | No | Ideal customer profile text. Makes scoring more accurate when provided. |

**Response:**
```json
{
  "result": {
    "lead_id": 1,
    "score": 78,
    "priority": "Hot",
    "reasoning": "Lead manages a multi-unit property in Miami valued at $720K. Strong match to ICP — commercial property manager in South Florida with high-value portfolio.",
    "recommended_campaign": "premium-property-outreach",
    "personalization_hints": "Reference their Coral Gables location and Single Family property type. Lead with ROI data for similar recent sales."
  }
}
```

**Priority mapping:**

| Score | Priority | Color suggestion |
|-------|----------|-----------------|
| 75-100 | Hot | Red / `#EF4444` |
| 50-74 | Warm | Orange / `#F59E0B` |
| 25-49 | Cold | Blue / `#3B82F6` |
| 0-24 | Dead | Gray / `#6B7280` |

**How to show in frontend:**
- On the lead detail page, show a score card with the number (0-100), a colored priority badge, and the reasoning text below.
- The `recommended_campaign` can be shown as a suggestion chip.
- `personalization_hints` can appear as a tooltip or info box when composing emails/SMS to this lead.

---

## POST `/api/leads/score/bulk`

Score multiple leads at once.

**Request:**
```json
{
  "lead_ids": [1, 2, 3, 4, 5],
  "icp_description": "Commercial property managers in South Florida"
}
```

**Response:**
```json
{
  "total": 5,
  "scored": 5,
  "results": [
    {
      "lead_id": 1,
      "score": 78,
      "priority": "Hot",
      "reasoning": "Strong match...",
      "recommended_campaign": "premium-property-outreach",
      "personalization_hints": "Reference their Coral Gables location..."
    },
    {
      "lead_id": 2,
      "score": 42,
      "priority": "Cold",
      "reasoning": "Limited data available...",
      "recommended_campaign": "general-outreach",
      "personalization_hints": "Use generic real estate angle..."
    }
  ]
}
```

**How to show in frontend:**
- Add a "Score All Leads with AI" button on the leads list page. When clicked, collect all visible lead IDs and call this endpoint.
- Show a modal with an ICP text input before scoring: "Describe your ideal customer (optional)".
- After scoring, add a `priority` column to the leads table. Make it sortable so Hot leads float to the top.
- Show a toast/notification: "5 leads scored — 2 Hot, 1 Warm, 2 Cold".

---

# 2. AI Campaign Generation & A/B Testing

These three endpoints handle the AI email generation workflow: generate 5 variations, view their performance, and analyze the winner.

---

## POST `/api/campaigns/{campaign_id}/generate`

AI generates 5 email variations (A through E) for a campaign. Each targets a different psychological trigger. The system automatically reads past learned patterns from the `ai_patterns` table and feeds them into the prompt.

**Request:**
```json
{
  "campaign_id": 1,
  "target_audience": "Property managers in South Florida with portfolios above $500K",
  "goal": "Book a 15-minute discovery call",
  "pain_point": "Low response rates from cold outreach",
  "tone": "professional but conversational",
  "max_word_count": 150
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| campaign_id | int | Yes | Must match URL parameter |
| target_audience | string | Yes | Who the emails target |
| goal | string | Yes | What you want the lead to do |
| pain_point | string | No | The problem to address. Default: "low engagement" |
| tone | string | No | Default: "professional but conversational" |
| max_word_count | int | No | Default: 150 |

**Response:**
```json
{
  "campaign_id": 1,
  "variations": [
    {
      "label": "A",
      "subject": "Is your Miami portfolio leaving money on the table?",
      "body": "Hi {{first_name}},\n\nProperty managers in South Florida are seeing 20% higher yields...",
      "psychological_trigger": "curiosity"
    },
    {
      "label": "B",
      "subject": "3 property managers just booked — spots filling fast",
      "body": "Hi {{first_name}},\n\nWe're working with select property managers this quarter...",
      "psychological_trigger": "urgency"
    },
    {
      "label": "C",
      "subject": "How Pinnacle Realty boosted their portfolio ROI by 35%",
      "body": "Hi {{first_name}},\n\nOne of our clients was in a similar position...",
      "psychological_trigger": "social_proof"
    },
    {
      "label": "D",
      "subject": "Your competitors are using this — are you?",
      "body": "Hi {{first_name}},\n\nOther property managers in South Florida...",
      "psychological_trigger": "fear_of_missing_out"
    },
    {
      "label": "E",
      "subject": "Expert insight for {{property_type}} portfolios",
      "body": "Hi {{first_name}},\n\nBased on our analysis of the South Florida market...",
      "psychological_trigger": "authority"
    }
  ],
  "patterns_used": 3
}
```

**How to show in frontend:**
- After creating a campaign, show a "Generate with AI" button that opens a form with the fields above.
- Display the 5 variations as tabs (A | B | C | D | E) or cards.
- Each card shows: label, subject line, body preview, and a trigger badge (e.g. "curiosity" in purple, "urgency" in red).
- Show `patterns_used` as "AI used 3 learned patterns from past campaigns" at the top.
- Let the user edit each variation before starting the campaign.
- The bodies contain `{{first_name}}` etc. — show these as highlighted placeholder chips in the editor.

---

## GET `/api/campaigns/{campaign_id}/variations`

Get all variations for a campaign with live engagement stats.

**Response:**
```json
[
  {
    "id": 1,
    "label": "A",
    "subject": "Is your Miami portfolio leaving money on the table?",
    "body": "Hi {{first_name}}...",
    "psychological_trigger": "curiosity",
    "sends": 100,
    "opens": 42,
    "clicks": 15,
    "replies": 8,
    "is_winner": false,
    "open_rate": 42.0,
    "reply_rate": 8.0,
    "created_at": "2026-02-01T10:00:00"
  },
  {
    "id": 2,
    "label": "B",
    "subject": "3 property managers just booked...",
    "body": "Hi {{first_name}}...",
    "psychological_trigger": "urgency",
    "sends": 100,
    "opens": 55,
    "clicks": 20,
    "replies": 12,
    "is_winner": true,
    "open_rate": 55.0,
    "reply_rate": 12.0,
    "created_at": "2026-02-01T10:00:00"
  }
]
```

**How to show in frontend:**
- On the campaign detail page, show a "Variations" tab with a comparison table:

| Variation | Subject | Sends | Opens | Open Rate | Replies | Reply Rate | Winner |
|-----------|---------|-------|-------|-----------|---------|------------|--------|
| A | Is your Miami portfolio... | 100 | 42 | 42.0% | 8 | 8.0% | |
| **B** | **3 property managers...** | **100** | **55** | **55.0%** | **12** | **12.0%** | **Trophy icon** |

- Use progress bars for open_rate and reply_rate columns.
- Highlight the `is_winner: true` row with a gold border or trophy icon.
- If no winner yet (all `is_winner: false`), show an "Analyze Results" button.

---

## POST `/api/campaigns/{campaign_id}/analyze`

AI analyzes the A/B test. Picks a winner using weighted scoring: replies 50%, opens 30%, clicks 20%. Saves the learned pattern to the database so future campaigns get smarter.

**Request:** No body needed — reads variations from the database.

**Response:**
```json
{
  "campaign_id": 1,
  "winner_label": "B",
  "winner_subject": "3 property managers just booked — spots filling fast",
  "winner_body": "Hi {{first_name}},\n\nWe're working with select property managers...",
  "explanation": "Variation B dominated across all weighted metrics. Its urgency-driven subject line achieved a 55% open rate (vs 42% average) and 12% reply rate (vs 6% average). The scarcity framing created FOMO that drove action.",
  "pattern_learned": "Urgency-based subject lines with specific social proof numbers outperform curiosity and authority angles by 2-3x in South Florida property manager outreach.",
  "stats": {
    "A": { "sends": 100, "opens": 42, "clicks": 15, "replies": 8 },
    "B": { "sends": 100, "opens": 55, "clicks": 20, "replies": 12 },
    "C": { "sends": 100, "opens": 38, "clicks": 12, "replies": 5 },
    "D": { "sends": 100, "opens": 45, "clicks": 18, "replies": 7 },
    "E": { "sends": 100, "opens": 35, "clicks": 10, "replies": 4 }
  }
}
```

**How to show in frontend:**
- Show "Analyze A/B Results" button on campaigns that have variations.
- After analysis, display a results card:
  - Winner badge: "Winner: Variation B — Urgency"
  - Explanation paragraph (the `explanation` field)
  - A bar chart comparing all 5 variations (sends, opens, replies)
  - "New AI Learning" callout box showing `pattern_learned` with a brain icon
  - The `stats` object can power the chart directly

---

# 3. Chatbot

Real-time AI sales chatbot. Uses OpenAI when configured, rule-based fallback in demo mode. Messages are persisted in the `chatbot_messages` table.

---

## POST `/api/chatbot/message`

Send a message and get an AI reply.

**Request:**
```json
{
  "lead_id": 1,
  "messages": [
    { "role": "user", "content": "Hi, I got your email about my property" },
    { "role": "assistant", "content": "Hi John! Great to hear from you. What questions do you have?" },
    { "role": "user", "content": "What's the pricing for your service?" }
  ],
  "lead_score": 65,
  "industry": "real_estate",
  "source": "email_click",
  "last_email_summary": "Initial outreach about 123 Oak Street property"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| lead_id | int | Yes | Lead in the conversation |
| messages | array | Yes | Full conversation history. Each item: `{ role: "user"/"assistant", content: "..." }` |
| lead_score | int | No | Current score for context |
| industry | string | No | Lead's industry |
| source | string | No | How they arrived: `email_open`, `email_click`, `manual` |
| last_email_summary | string | No | Summary of last email sent to them |

**Response:**
```json
{
  "reply": "Great question on pricing. Before I can give you an accurate picture, how many properties are you currently managing?",
  "next_action": {
    "type": "continue",
    "reason": "Pricing question — qualifying with team-size question."
  },
  "updated_lead_score": 70
}
```

**`next_action.type` values and what frontend should do:**

| Type | Frontend Action |
|------|----------------|
| `continue` | Keep the chat open, wait for next user message |
| `book_meeting` | Show a "Book a Demo" CTA button below the reply |
| `escalate_human` | Show a "Connect with a Human" button below the reply |
| `end` | Show a "Conversation ended" message, disable input |

**How to show in frontend:**
- Build a chat widget — either a bottom-right floating panel or a full section on the lead detail page.
- Send the **entire conversation history** with each request (the backend doesn't maintain state between calls — it needs all messages each time).
- Display messages as bubbles: user on right, assistant on left.
- After each assistant reply, check `next_action.type` and show the appropriate CTA.
- If `updated_lead_score` is returned and different from current, update the lead's score display.

---

## GET `/api/chatbot/history/{lead_id}`

Get full chat history for a lead (oldest to newest).

**Response:**
```json
{
  "lead_id": 1,
  "messages": [
    { "role": "user", "content": "Hi, I got your email" },
    { "role": "assistant", "content": "Hi John! Great to hear from you..." },
    { "role": "user", "content": "What's the pricing?" },
    { "role": "assistant", "content": "Great question on pricing..." }
  ]
}
```

**How to show in frontend:**
- Call this when opening a chat for a returning lead. Pre-populate the chat widget with the history so the conversation continues seamlessly.

---

# 4. SMS

Send SMS to leads via Twilio. In demo mode (no Twilio keys), messages are logged as `status: "mock"` and stored in the database.

---

## POST `/api/sms/send`

Send an SMS to a lead.

**Request:**
```json
{
  "lead_id": 1,
  "body": "Hi {{first_name}}, following up on my email about {{address}}. Would a quick call this week work?",
  "personalize": true
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| lead_id | int | Yes | Lead to SMS. Must have a phone number. |
| body | string | Yes | Message text, max 1600 chars. Supports `{{first_name}}`, `{{last_name}}`, `{{email}}`, `{{phone}}`, `{{address}}`, `{{property_type}}`, `{{estimated_value}}` |
| personalize | bool | No | Default: true. Replaces placeholders with lead data. |

**Response (success):**
```json
{
  "success": true,
  "lead_id": 1,
  "sms_message_id": 5,
  "twilio_sid": "SM1234567890abcdef",
  "status": "sent",
  "error": null,
  "message": "SMS sent"
}
```

**Response (demo mode):**
```json
{
  "success": true,
  "lead_id": 1,
  "sms_message_id": 5,
  "twilio_sid": null,
  "status": "mock",
  "error": null,
  "message": "SMS sent"
}
```

**Response (error — no phone):**
```json
// HTTP 400
{ "detail": "Lead has no phone number; add a phone before sending SMS." }
```

**How to show in frontend:**
- On the lead detail page, add a "Send SMS" button (only enabled if lead has a phone number).
- Open a compose modal with a text area for the message body.
- Show placeholder buttons ({{first_name}}, {{address}}, etc.) that insert into the text area on click.
- After sending, show a toast: "SMS sent to +1555..." or the error message.
- If `status: "mock"`, show a small "Demo Mode" badge on the toast.

---

## GET `/api/sms/history/{lead_id}`

Get all SMS messages sent to a lead (oldest first).

**Response:**
```json
{
  "lead_id": 1,
  "messages": [
    {
      "id": 5,
      "lead_id": 1,
      "to_number": "+15551234567",
      "body": "Hi John, following up on my email about 123 Oak Street...",
      "status": "sent",
      "twilio_sid": "SM1234567890abcdef",
      "sent_at": "2026-02-15T14:30:00",
      "created_at": "2026-02-15T14:30:00"
    }
  ]
}
```

**SMS status values:** `pending`, `sent`, `delivered`, `failed`, `undelivered`

**How to show in frontend:**
- On the lead detail page, add an "SMS" tab showing a timeline of sent messages.
- Each message shows: body text, status badge (green for sent/delivered, red for failed), timestamp.

---

# 5. Voice Calls

Outbound AI voice calls via Retell AI + Twilio SIP trunk. In demo mode, calls are logged as `status: "mock"`.

---

## POST `/api/voice/call`

Start an outbound AI voice call.

**Request:**
```json
{
  "lead_id": 1,
  "dynamic_variables": {
    "property_address": "123 Oak Street",
    "caller_name": "Sarah from Outreach Team"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| lead_id | int | Yes | Lead to call. Must have a phone number. |
| dynamic_variables | object | No | Extra variables injected into the Retell agent prompt. `first_name`, `last_name`, `company`, `address`, `property_type` are auto-filled from lead data — you only need to pass additional custom ones here. |

**Response:**
```json
{
  "success": true,
  "lead_id": 1,
  "voice_call_id": 3,
  "retell_call_id": "call_abc123def456",
  "status": "calling",
  "error": null,
  "message": "Call initiated"
}
```

**How to show in frontend:**
- On the lead detail page, add a "Start AI Call" button (only enabled if lead has phone).
- Optionally show a modal where the user can add custom dynamic_variables before calling.
- After initiating, show a "Call in progress..." indicator with a pulse animation.
- Poll `GET /api/voice/call/{voice_call_id}` every 10-15 seconds to check if the call completed, then refresh the history.

---

## GET `/api/voice/history/{lead_id}`

Get all voice calls for a lead (newest first).

**Response:**
```json
{
  "lead_id": 1,
  "calls": [
    {
      "id": 3,
      "lead_id": 1,
      "to_number": "+15551234567",
      "retell_call_id": "call_abc123def456",
      "retell_agent_id": "agent_xyz789",
      "status": "completed",
      "duration_seconds": 145,
      "call_summary": "Lead expressed interest in selling. Wants a follow-up call next Tuesday.",
      "call_outcome": "interested",
      "transcript": "Agent: Hi John, this is Sarah...\nJohn: Oh hi, yes I got your email...",
      "recording_url": "https://storage.retellai.com/recordings/abc123.wav",
      "started_at": "2026-02-16T10:00:00",
      "ended_at": "2026-02-16T10:02:25",
      "created_at": "2026-02-16T10:00:00"
    }
  ]
}
```

**How to show in frontend:**
- On the lead detail page, add a "Voice Calls" tab.
- Each call shows: status badge, duration (format as "2m 25s"), outcome badge, summary text.
- Expandable section for the full transcript.
- If `recording_url` exists, show an audio player.
- If `call_summary` exists, show it prominently as the AI's summary of what happened.

---

## GET `/api/voice/call/{call_id}`

Get a single voice call by its database ID.

**Response:** Same shape as a single item in the `calls` array above.

**How to use:** Poll this after starting a call to check when it completes.

---

**Voice Call Status Values:**
| Status | Meaning | Badge Color |
|--------|---------|-------------|
| pending | Queued | Gray |
| calling | Ringing | Yellow |
| in_progress | Conversation happening | Blue |
| completed | Call finished | Green |
| failed | Error occurred | Red |
| no_answer | Lead didn't pick up | Orange |
| busy | Line was busy | Orange |
| voicemail | Went to voicemail | Purple |

**Voice Call Outcome Values:**
| Outcome | Meaning | Badge Color |
|---------|---------|-------------|
| booked | Meeting scheduled | Green |
| interested | Lead showed interest | Blue |
| not_interested | Lead declined | Red |
| callback | Lead wants a callback | Yellow |
| voicemail | Left a voicemail | Purple |
| no_outcome | Inconclusive | Gray |

---

# 6. AI Weekly Insights

## GET `/api/dashboard/insights`

AI-generated weekly performance report. The LLM reads the last 7 days of data and produces a plain-English summary with highlights and actionable recommendations.

**Response:**
```json
{
  "period": "Feb 11 - Feb 18, 2026",
  "summary": "This week you sent 45 emails with a 52.8% open rate and 13.9% reply rate. Your Tuesday sends got 2x more opens than Friday. Your shortest emails drove 80% of your replies.",
  "highlights": [
    "Total emails sent: 45",
    "Open rate: 52.8% (up from 41.2% last week)",
    "Reply rate: 13.9%",
    "Top campaign: Q1 2026 Outreach",
    "SMS messages sent: 12"
  ],
  "recommendations": [
    "Double down on Tuesday/Wednesday sends — they consistently outperform.",
    "Test shorter subject lines based on your A/B learnings.",
    "Follow up with non-openers via SMS.",
    "Consider voice calls for Hot-scored leads who haven't replied."
  ],
  "stats_snapshot": {
    "emails_sent": 45,
    "opens": 24,
    "replies": 6,
    "bookings": 2,
    "open_rate": 52.8,
    "reply_rate": 13.9,
    "prev_week_open_rate": 41.2,
    "prev_week_reply_rate": 10.0,
    "top_campaign": "Q1 2026 Outreach",
    "sms_sent": 12,
    "voice_calls": 3
  }
}
```

**How to show in frontend:**
- On the dashboard page, add a full-width "AI Insights" card.
- Top: `period` as the card header ("Week of Feb 11 - Feb 18, 2026").
- Middle: `summary` as a paragraph (the AI coach talking to the user).
- Left column: `highlights` as bullet points with small metric badges from `stats_snapshot`.
- Right column: `recommendations` as action items — show them with checkbox styling so it feels like a to-do list.
- Include a "Refresh Insights" button that re-calls this endpoint.
- Compare current vs previous week: show green/red arrows next to `open_rate` vs `prev_week_open_rate`.

---

# 7. Config Update

The existing `GET /config` endpoint now returns additional service statuses.

**Response (updated shape):**
```json
{
  "app_name": "Real Estate Outreach API",
  "version": "1.0.0",
  "environment": "development",
  "services": {
    "database": true,
    "sendgrid": false,
    "twilio_sms": false,
    "retell_voice": false,
    "openai": true,
    "calendly": false
  },
  "cors_origins": ["http://localhost:3000", "http://localhost:5173"]
}
```

**How to use in frontend:**
- Call `GET /config` on app load.
- `services.openai === true` → show "AI-Powered" badges on scoring, generation, insights, chatbot.
- `services.openai === false` → show "Demo Mode" badges instead (everything still works, just uses rule-based fallbacks).
- `services.twilio_sms === true` → SMS is live. `false` → SMS works but messages are mocked.
- `services.retell_voice === true` → Voice calls are live. `false` → Calls are mocked.
- `services.sendgrid === true` → Emails actually send. `false` → Emails are logged only.

---

# 8. Demo Utilities

These endpoints simulate events for testing when real services aren't connected. Useful for demoing the full pipeline.

---

## POST `/api/demo/simulate/open`

Simulate a lead opening their most recent email.

**Request:**
```json
{ "lead_id": 1 }
```

**Response:**
```json
{
  "success": true,
  "message": "Simulated email open for John Doe",
  "lead_id": 1,
  "email_sequence_id": 5,
  "opened_at": "2026-02-18T10:00:00"
}
```

---

## POST `/api/demo/simulate/reply`

Simulate a lead replying to an email.

**Request:**
```json
{
  "lead_id": 1,
  "sentiment": "interested",
  "reply_text": "Yes, I'd love to chat about selling my property."
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| lead_id | int | Yes | Lead who replies |
| sentiment | string | No | `interested`, `not_now`, `unsubscribe`, `other`. Default: `interested` |
| reply_text | string | No | Custom reply text. If omitted, auto-generated based on sentiment. |

**Response:**
```json
{
  "success": true,
  "message": "Simulated interested reply from John",
  "lead_id": 1,
  "lead_status": "interested",
  "reply_id": 8,
  "sentiment": "interested"
}
```

---

## POST `/api/demo/simulate/booking`

Simulate a lead booking a meeting.

**Request:**
```json
{
  "lead_id": 1,
  "days_from_now": 3
}
```

**Response:**
```json
{
  "success": true,
  "message": "Simulated booking for John on February 21 at 02:00 PM",
  "lead_id": 1,
  "lead_status": "booked",
  "booking_id": 4,
  "scheduled_time": "2026-02-21T14:00:00"
}
```

---

## POST `/api/demo/seed`

Seed database with 5 sample leads, 1 email template, and 1 draft campaign. Fails if data already exists (call reset first).

**Response:**
```json
{
  "success": true,
  "message": "Demo data seeded successfully",
  "data": { "leads_created": 5, "templates_created": 1, "campaigns_created": 1 }
}
```

---

## POST `/api/demo/reset?confirm=true`

Delete ALL data. Requires `?confirm=true` query parameter.

**Response:**
```json
{
  "success": true,
  "message": "All demo data has been reset. Upload new leads to start fresh."
}
```

**How to show in frontend:**
- Add a "Demo Controls" panel (collapsible, maybe in settings or a debug drawer).
- Buttons: "Seed Data", "Simulate Open", "Simulate Reply", "Simulate Booking", "Reset All".
- The simulate buttons should ask for a lead_id (dropdown of existing leads).
- The reset button should have a confirmation dialog.

---

# 9. Webhooks

These are backend-only — the frontend doesn't call them. But the frontend should display the data they produce.

## POST `/webhooks/sendgrid/events`

Receives email events from SendGrid: `open`, `click`, `bounce`, `spamreport`. Automatically updates `email_sequences` and `leads` tables.

**Frontend impact:** After SendGrid processes events, the lead detail page will show updated `opened_at`, `clicked_at`, `replied_at` timestamps and status changes in the email history.

## POST `/api/voice/webhook/retell`

Receives voice call events from Retell AI: `call_ended`, `call_analyzed`. Automatically updates `voice_calls` with transcript, summary, recording URL, outcome, and duration.

**Frontend impact:** After a call completes and Retell sends its webhook, the voice call history will show `transcript`, `call_summary`, `call_outcome`, `duration_seconds`, and `recording_url`. Poll the voice call endpoint to pick up these updates.

---

# 10. New Data Models & Status Values

## Lead Score Priorities
```
Hot (75-100) → immediate aggressive outreach
Warm (50-74) → nurture sequence
Cold (25-49) → monthly check-in
Dead (0-24)  → skip
```

## SMS Statuses
```
pending → sent → delivered
              → failed
              → undelivered
```

## Voice Call Statuses
```
pending → calling → in_progress → completed
                                → failed
                                → no_answer
                                → busy
                                → voicemail
```

## Voice Call Outcomes
```
booked | interested | not_interested | callback | voicemail | no_outcome
```

## Chatbot Next Actions
```
continue | book_meeting | escalate_human | end
```

## Psychological Triggers (Campaign Variations)
```
curiosity | urgency | social_proof | fear_of_missing_out | authority
```

---

# 11. Frontend Integration Guide

## New Axios Functions to Add

```javascript
// AI Lead Scoring
export const scoreLead = (leadId, icpDescription = null) =>
  api.post('/api/leads/score', { lead_id: leadId, icp_description: icpDescription });

export const scoreBulkLeads = (leadIds, icpDescription = null) =>
  api.post('/api/leads/score/bulk', { lead_ids: leadIds, icp_description: icpDescription });

// AI Campaign Generation
export const generateVariations = (campaignId, brief) =>
  api.post(`/api/campaigns/${campaignId}/generate`, brief);

export const getVariations = (campaignId) =>
  api.get(`/api/campaigns/${campaignId}/variations`);

export const analyzeABTest = (campaignId) =>
  api.post(`/api/campaigns/${campaignId}/analyze`);

// Chatbot
export const sendChatMessage = (leadId, messages, context = {}) =>
  api.post('/api/chatbot/message', { lead_id: leadId, messages, ...context });

export const getChatHistory = (leadId) =>
  api.get(`/api/chatbot/history/${leadId}`);

// SMS
export const sendSMS = (leadId, body, personalize = true) =>
  api.post('/api/sms/send', { lead_id: leadId, body, personalize });

export const getSMSHistory = (leadId) =>
  api.get(`/api/sms/history/${leadId}`);

// Voice
export const startVoiceCall = (leadId, dynamicVars = null) =>
  api.post('/api/voice/call', { lead_id: leadId, dynamic_variables: dynamicVars });

export const getVoiceHistory = (leadId) =>
  api.get(`/api/voice/history/${leadId}`);

export const getVoiceCall = (callId) =>
  api.get(`/api/voice/call/${callId}`);

// AI Insights
export const getInsights = () => api.get('/api/dashboard/insights');

// Config (check which services are live)
export const getConfig = () => api.get('/config');

// Demo utilities
export const simulateOpen = (leadId) =>
  api.post('/api/demo/simulate/open', { lead_id: leadId });

export const simulateReply = (leadId, sentiment = 'interested') =>
  api.post('/api/demo/simulate/reply', { lead_id: leadId, sentiment });

export const simulateBooking = (leadId, daysFromNow = 3) =>
  api.post('/api/demo/simulate/booking', { lead_id: leadId, days_from_now: daysFromNow });

export const seedData = () => api.post('/api/demo/seed');
export const resetData = () => api.post('/api/demo/reset?confirm=true');
```

## New UI Components Needed

1. **Lead Score Card** — score number (big), priority badge (colored), reasoning text, recommended campaign chip, personalization hints.

2. **Bulk Score Button** — on leads table, "Score All with AI" button → ICP input modal → progress indicator → results update table.

3. **AI Campaign Generator** — form (target_audience, goal, pain_point, tone) → 5-tab variation viewer → edit capability → "Use for Campaign" button.

4. **Variation Comparison Table** — columns: label, subject, sends, opens, open_rate, clicks, replies, reply_rate, winner badge. Progress bars for rates.

5. **A/B Analysis Card** — winner announcement, explanation paragraph, pattern learned callout, bar chart of all variations.

6. **Chat Widget** — message bubbles (user right, bot left), CTA buttons based on next_action, message input with send button.

7. **SMS Compose Modal** — text area with placeholder insertion buttons, character counter (max 1600), send button.

8. **SMS History Timeline** — chronological list of messages with status badges.

9. **Voice Call Section** — "Start AI Call" button, call status indicator with pulse animation, call history cards with summary/outcome/duration, expandable transcript, audio player for recordings.

10. **AI Insights Card** — period header, summary paragraph, highlights bullets, recommendations checklist, stat comparison badges with arrows.

11. **Demo Controls Panel** — collapsible panel with simulate/seed/reset buttons.

12. **Service Status Indicators** — green/yellow dots from `/config` showing which services are live vs demo.

---

*New Endpoints Total: 18 (Lead Scoring 2, Campaign AI 3, Chatbot 2, SMS 2, Voice 3, Insights 1, Demo 5)*

*Documentation Generated: February 18, 2026*
