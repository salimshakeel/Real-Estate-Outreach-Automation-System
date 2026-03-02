export interface Lead {
  id: number;
  email: string;
  first_name: string;
  last_name: string | null;
  company: string | null;
  phone: string | null;
  address: string | null;
  property_type: string | null;
  estimated_value: string | null;
  status: string;
  notes: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
  ai_score?: AiLeadScore | null;
}

export interface AiLeadScore {
  id: number;
  lead_id: number;
  score: number;
  priority: "Hot" | "Warm" | "Cold" | "Dead";
  reasoning: string | null;
  recommended_campaign: string | null;
  personalization_hints: string | null;
  scored_at: string | null;
  created_at: string;
}

export interface EmailTemplate {
  id: number;
  name: string;
  subject: string;
  body: string;
  is_default: boolean;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface Campaign {
  id: number;
  name: string;
  description: string | null;
  email_template: string | null;
  status: string;
  started_at: string | null;
  ended_at: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface CampaignVariation {
  id: number;
  label: string;
  subject: string;
  body: string;
  psychological_trigger: string | null;
  sends: number;
  opens: number;
  clicks: number;
  replies: number;
  is_winner: boolean;
  open_rate: number;
  reply_rate: number;
  created_at: string;
}

export interface EmailVariation {
  label: string;
  subject: string;
  body: string;
  psychological_trigger: string;
}

export interface EmailSequence {
  id: number;
  lead_id: number;
  sequence_day: number;
  email_subject: string | null;
  email_body: string | null;
  status: string;
  sent_at: string | null;
  opened_at: string | null;
  clicked_at: string | null;
  replied_at: string | null;
  sendgrid_message_id: string | null;
  bounce_reason: string | null;
  created_at: string;
  updated_at: string;
}

export interface SmsMessage {
  id: number;
  lead_id: number;
  to_number: string;
  body: string;
  status: string;
  twilio_sid: string | null;
  sent_at: string | null;
  created_at: string;
}

export interface VoiceCall {
  id: number;
  lead_id: number;
  to_number: string;
  retell_call_id: string | null;
  retell_agent_id: string | null;
  status: string;
  duration_seconds: number | null;
  call_summary: string | null;
  call_outcome: string | null;
  transcript: string | null;
  recording_url: string | null;
  started_at: string | null;
  ended_at: string | null;
  created_at: string;
}

export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface ChatbotResponse {
  reply: string;
  next_action: {
    type: "continue" | "book_meeting" | "escalate_human" | "end";
    reason: string | null;
  };
  updated_lead_score: number | null;
}

export interface DashboardStats {
  total_leads: number;
  leads_by_status: Record<string, number>;
  total_emails_sent: number;
  emails_opened: number;
  emails_replied: number;
  emails_bounced: number;
  open_rate: number;
  reply_rate: number;
  total_replies: number;
  replies_by_sentiment: Record<string, number>;
  total_bookings: number;
  upcoming_bookings: number;
  emails_sent_today: number;
  emails_sent_this_week: number;
  replies_today: number;
  bookings_this_week: number;
}

export interface DashboardFunnel {
  uploaded: number;
  contacted: number;
  replied: number;
  interested: number;
  booked: number;
  closed: number;
}

export interface DashboardActivity {
  type: string;
  lead_id: number;
  lead_name: string;
  description: string;
  timestamp: string;
}

export interface DashboardResponse {
  stats: DashboardStats;
  funnel: DashboardFunnel;
  recent_activity: DashboardActivity[];
}

export interface WeeklyInsights {
  period: string;
  summary: string;
  highlights: string[];
  recommendations: string[];
  stats_snapshot: {
    emails_sent: number;
    opens: number;
    replies: number;
    bookings: number;
    open_rate: number;
    reply_rate: number;
    prev_week_open_rate: number;
    prev_week_reply_rate: number;
    top_campaign: string;
    sms_sent: number;
    voice_calls: number;
  };
}

export interface AppConfig {
  app_name: string;
  version: string;
  environment: string;
  services: {
    database: boolean;
    sendgrid: boolean;
    twilio_sms: boolean;
    retell_voice: boolean;
    openai: boolean;
    calendly: boolean;
  };
  cors_origins: string[];
}

export interface PaginatedResponse<T> {
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
  items: T[];
}

export interface LeadScoreResult {
  lead_id: number;
  score: number;
  priority: string;
  reasoning: string;
  recommended_campaign: string | null;
  personalization_hints: string | null;
}

export interface ABTestAnalysis {
  campaign_id: number;
  winner_label: string;
  winner_subject: string;
  winner_body: string;
  explanation: string;
  pattern_learned: string;
  stats: Record<string, { sends: number; opens: number; clicks: number; replies: number }>;
}
