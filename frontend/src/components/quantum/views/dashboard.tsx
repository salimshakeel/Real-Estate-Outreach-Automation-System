"use client";

import { LEADS, CAMPAIGNS, INSIGHTS } from "../data";
import { MetricCard, GlassCard, PriorityBadge, I } from "../ui";

export function ViewDashboard() {
  const s = INSIGHTS.stats;
  const topLeads = [...LEADS].sort((a, b) => b.score - a.score).slice(0, 5);
  const activeCampaigns = CAMPAIGNS.filter((c) => c.status === "active" || c.status === "draft");

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 28 }}>
      <div>
        <h1 style={{ fontSize: 28, fontWeight: 800, letterSpacing: "-0.03em", marginBottom: 8 }}>Dashboard</h1>
        <p style={{ fontSize: 14, color: "var(--text-secondary)" }}>{INSIGHTS.period}</p>
      </div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 20 }}>
        <MetricCard label="Emails sent" value={s.emails_sent} change={12} icon={I.mail} color="var(--cyan)" delay={0} />
        <MetricCard label="Open rate" value={s.open_rate} suffix="%" change={s.open_rate - (s.prev_open ?? 0)} icon={I.bar} color="var(--purple)" delay={0.05} />
        <MetricCard label="Replies" value={s.replies} change={s.reply_rate - (s.prev_reply ?? 0)} icon={I.chat} color="var(--green)" delay={0.1} />
        <MetricCard label="Bookings" value={s.bookings} icon={I.trophy} color="var(--amber)" delay={0.15} />
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
        <GlassCard className="stagger-2" style={{ padding: 28 }}>
          <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 20, color: "var(--text-secondary)" }}>Pipeline</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            {["uploaded", "contacted", "replied", "interested", "booked"].map((status, i) => {
              const count = LEADS.filter((l) => l.status === status).length;
              const pct = LEADS.length ? (count / LEADS.length) * 100 : 0;
              return (
                <div key={status}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6, fontSize: 12 }}>
                    <span style={{ textTransform: "capitalize", color: "var(--text-secondary)" }}>{status}</span>
                    <span style={{ fontWeight: 600 }}>{count}</span>
                  </div>
                  <div style={{ width: "100%", height: 6, background: "rgba(255,255,255,0.04)", borderRadius: 6, overflow: "hidden" }}>
                    <div style={{ width: `${pct}%`, height: "100%", background: "linear-gradient(90deg, var(--cyan), var(--purple))", borderRadius: 6, transition: "width 0.5s ease" }} />
                  </div>
                </div>
              );
            })}
          </div>
        </GlassCard>
        <GlassCard className="stagger-2" style={{ padding: 28 }}>
          <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 20, color: "var(--text-secondary)" }}>Active campaigns</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {activeCampaigns.map((c) => (
              <div key={c.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px 14px", background: "rgba(255,255,255,0.03)", borderRadius: "var(--radius-sm)" }}>
                <span style={{ fontSize: 13, fontWeight: 500 }}>{c.name}</span>
                <span style={{ fontSize: 11, padding: "4px 10px", borderRadius: 20, background: c.status === "active" ? "var(--cyan-dim)" : "rgba(255,255,255,0.06)", color: c.status === "active" ? "var(--cyan)" : "var(--text-dim)" }}>{c.status}</span>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>
      <GlassCard className="stagger-3" style={{ padding: 28 }}>
        <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 20, color: "var(--text-secondary)" }}>Top leads by score</h3>
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {topLeads.map((l) => (
            <div key={l.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "14px 16px", background: "rgba(255,255,255,0.03)", borderRadius: "var(--radius-sm)" }}>
              <div>
                <span style={{ fontWeight: 600, fontSize: 13 }}>{l.first_name} {l.last_name}</span>
                <span style={{ color: "var(--text-dim)", fontSize: 12, marginLeft: 10 }}>{l.company}</span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <span style={{ fontSize: 13, fontWeight: 700, color: "var(--cyan)" }}>{l.score}</span>
                <PriorityBadge p={l.priority} />
              </div>
            </div>
          ))}
        </div>
      </GlassCard>
    </div>
  );
}
