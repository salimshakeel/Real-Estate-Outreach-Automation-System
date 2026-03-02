export const LEADS = [
  { id: 1, first_name: "James", last_name: "Morrison", email: "james@morrison.com", phone: "+15551234001", company: "Morrison Realty", status: "contacted", address: "1420 Coral Way, Miami", property_type: "Multi-Family", estimated_value: "$850,000", score: 82, priority: "Hot" as const },
  { id: 2, first_name: "Sarah", last_name: "Chen", email: "sarah@chenproperties.com", phone: "+15551234002", company: "Chen Properties", status: "interested", address: "789 Biscayne Blvd, Miami", property_type: "Condo", estimated_value: "$420,000", score: 68, priority: "Warm" as const },
  { id: 3, first_name: "Michael", last_name: "Torres", email: "mike@torresgroup.com", phone: "+15551234003", company: "Torres Group", status: "uploaded", address: "2100 NW 42nd Ave, Miami", property_type: "Single Family", estimated_value: "$350,000", score: 35, priority: "Cold" as const },
  { id: 4, first_name: "Emily", last_name: "Watson", email: "emily@watsonhomes.com", phone: "+15551234004", company: "Watson Homes", status: "booked", address: "555 Brickell Key Dr, Miami", property_type: "Condo", estimated_value: "$1,200,000", score: 91, priority: "Hot" as const },
  { id: 5, first_name: "David", last_name: "Kim", email: "david@kimrealestate.com", phone: "+15551234005", company: "Kim Real Estate", status: "replied", address: "3200 Collins Ave, Miami Beach", property_type: "Condo", estimated_value: "$680,000", score: 55, priority: "Warm" as const },
  { id: 6, first_name: "Lisa", last_name: "Patel", email: "lisa@patelprop.com", phone: "", company: "Patel Properties", status: "uploaded", address: "4400 NE 2nd Ave, Miami", property_type: "Townhouse", estimated_value: "$290,000", score: 18, priority: "Dead" as const },
];

export const CAMPAIGNS = [
  { id: 1, name: "Q1 South Florida Outreach", status: "active", leads_count: 150, emails_sent: 145, opens: 78, replies: 21, created_at: "2026-02-01" },
  { id: 2, name: "Miami Condo Owners", status: "draft", leads_count: 50, emails_sent: 0, opens: 0, replies: 0, created_at: "2026-02-10" },
  { id: 3, name: "Commercial Property Mgrs", status: "completed", leads_count: 80, emails_sent: 80, opens: 42, replies: 12, created_at: "2026-01-15" },
];

export const INSIGHTS = {
  period: "Feb 18 – Feb 25, 2026",
  summary: "Exceptional week. Your 52.8% open rate is the highest this month — driven by urgency-based subject lines on Tuesday sends. Short, punchy emails drove 80% of replies. Three new Hot leads identified via AI scoring are ready for voice calls.",
  highlights: ["145 emails sent", "52.8% open rate (+11.6pp)", "14.5% reply rate", "3 new Hot leads", "12 SMS follow-ups", "2 AI voice calls"],
  recommendations: ["Double down on Tue/Wed sends", "Use urgency subjects for Warm leads", "SMS the 12 non-openers", "Voice call the 2 unboooked Hot leads"],
  stats: { emails_sent: 145, opens: 78, replies: 21, bookings: 4, open_rate: 52.8, reply_rate: 14.5, prev_open: 41.2, prev_reply: 10.0, sms: 12, calls: 2 },
};

export const CONFIG = {
  services: { database: true, sendgrid: false, twilio_sms: false, retell_voice: false, openai: true, calendly: false },
  ai_powered: true,
  demo_mode: true,
};

export type Lead = (typeof LEADS)[number];
export type Campaign = (typeof CAMPAIGNS)[number];
