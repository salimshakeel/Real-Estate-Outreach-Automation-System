export const api = {
  scoreBulk: async (ids: number[]) => ({
    scored: ids.length,
    results: ids.map((id) => ({
      lead_id: id,
      score: Math.floor(Math.random() * 40 + 55),
      priority: ["Hot", "Warm", "Cold"][Math.floor(Math.random() * 3)] as "Hot" | "Warm" | "Cold",
    })),
  }),
  sendChat: async (_id: number, msgs: { role: string; content: string }[]) => {
    const last = (msgs[msgs.length - 1]?.content ?? "").toLowerCase();
    if (last.includes("price") || last.includes("cost"))
      return { reply: "Great question. How many properties are you managing? That helps me give the right pricing.", next_action: { type: "continue" }, updated_lead_score: 70 };
    if (last.includes("demo") || last.includes("call") || last.includes("meeting"))
      return { reply: "Let's get that set up. When works better — earlier or later this week?", next_action: { type: "book_meeting" }, updated_lead_score: 85 };
    if (last.includes("not interested") || last.includes("stop"))
      return { reply: "Understood — thanks for your time. Feel free to reach back anytime.", next_action: { type: "end" }, updated_lead_score: 15 };
    return { reply: "Thanks for reaching out! What's your biggest challenge with managing your properties right now?", next_action: { type: "continue" }, updated_lead_score: 55 };
  },
  sendSMS: async () => ({ success: true, status: "mock", sms_message_id: Date.now() }),
  startCall: async () => ({ success: true, status: "mock", voice_call_id: Date.now() }),
  generateVariations: async () => ({
    patterns_used: 3,
    variations: [
      { label: "A", subject: "Is your portfolio leaving money on the table?", body: "Hi {{first_name}},\n\nProperty managers in South Florida see 20% higher yields...", trigger: "curiosity" },
      { label: "B", subject: "3 managers just booked — spots filling fast", body: "Hi {{first_name}},\n\nWe're working with select managers this quarter...", trigger: "urgency" },
      { label: "C", subject: "How Pinnacle Realty boosted ROI 35%", body: "Hi {{first_name}},\n\nOne client in a similar position saw a 35% increase...", trigger: "social_proof" },
      { label: "D", subject: "Your competitors are using this", body: "Hi {{first_name}},\n\nOther managers in your area already started...", trigger: "fomo" },
      { label: "E", subject: "Expert insight for {{property_type}} portfolios", body: "Hi {{first_name}},\n\nOur analysis shows properties like yours have unique opportunity...", trigger: "authority" },
    ],
  }),
  getVariations: async () => [
    { label: "A", sends: 30, opens: 14, replies: 3, open_rate: 46.7, reply_rate: 10.0, is_winner: false, trigger: "curiosity" },
    { label: "B", sends: 30, opens: 18, replies: 5, open_rate: 60.0, reply_rate: 16.7, is_winner: true, trigger: "urgency" },
    { label: "C", sends: 30, opens: 12, replies: 2, open_rate: 40.0, reply_rate: 6.7, is_winner: false, trigger: "social_proof" },
    { label: "D", sends: 30, opens: 15, replies: 3, open_rate: 50.0, reply_rate: 10.0, is_winner: false, trigger: "fomo" },
    { label: "E", sends: 30, opens: 10, replies: 1, open_rate: 33.3, reply_rate: 3.3, is_winner: false, trigger: "authority" },
  ],
  analyzeAB: async () => ({
    winner: "B",
    explanation: "Variation B dominated — urgency-driven subject hit 60% opens and 16.7% replies, outperforming average by 2x.",
    pattern: "Urgency + specific numbers outperform curiosity and authority 2-3x in South Florida property outreach.",
  }),
};
