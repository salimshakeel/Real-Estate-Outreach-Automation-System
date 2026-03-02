"use client";

import { INSIGHTS } from "../data";
import { GlassCard, GlowBar, I } from "../ui";

export function ViewInsights() {
  const s = INSIGHTS.stats;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 28 }}>
      <div>
        <h1 style={{ fontSize: 28, fontWeight: 800, letterSpacing: "-0.03em", marginBottom: 8 }}>AI Insights</h1>
        <p style={{ fontSize: 14, color: "var(--text-secondary)" }}>{INSIGHTS.period}</p>
      </div>
      <GlassCard className="stagger-1" style={{ padding: 28 }}>
        <h3 style={{ fontSize: 12, fontWeight: 600, color: "var(--text-dim)", marginBottom: 12, textTransform: "uppercase", letterSpacing: "0.08em" }}>Summary</h3>
        <p style={{ fontSize: 15, lineHeight: 1.6, color: "var(--text-secondary)" }}>{INSIGHTS.summary}</p>
      </GlassCard>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 20 }}>
        <GlassCard className="stagger-2" style={{ padding: 24 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
            <span style={{ color: "var(--cyan)", opacity: 0.8 }}>{I.bar}</span>
            <span style={{ fontSize: 12, color: "var(--text-dim)" }}>Emails sent</span>
          </div>
          <div style={{ fontSize: 28, fontWeight: 800, color: "var(--cyan)" }}>{s.emails_sent}</div>
          <GlowBar value={s.emails_sent} max={200} color="var(--cyan)" delay={0.1} />
        </GlassCard>
        <GlassCard className="stagger-2" style={{ padding: 24 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
            <span style={{ color: "var(--purple)", opacity: 0.8 }}>{I.spark}</span>
            <span style={{ fontSize: 12, color: "var(--text-dim)" }}>Open rate</span>
          </div>
          <div style={{ fontSize: 28, fontWeight: 800, color: "var(--purple)" }}>{s.open_rate}%</div>
          <GlowBar value={s.open_rate} max={100} color="var(--purple)" delay={0.15} />
        </GlassCard>
        <GlassCard className="stagger-2" style={{ padding: 24 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
            <span style={{ color: "var(--green)", opacity: 0.8 }}>{I.chat}</span>
            <span style={{ fontSize: 12, color: "var(--text-dim)" }}>Reply rate</span>
          </div>
          <div style={{ fontSize: 28, fontWeight: 800, color: "var(--green)" }}>{s.reply_rate}%</div>
          <GlowBar value={s.reply_rate} max={100} color="var(--green)" delay={0.2} />
        </GlassCard>
        <GlassCard className="stagger-2" style={{ padding: 24 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
            <span style={{ color: "var(--amber)", opacity: 0.8 }}>{I.trophy}</span>
            <span style={{ fontSize: 12, color: "var(--text-dim)" }}>Bookings</span>
          </div>
          <div style={{ fontSize: 28, fontWeight: 800, color: "var(--amber)" }}>{s.bookings}</div>
          <GlowBar value={s.bookings} max={10} color="var(--amber)" delay={0.25} />
        </GlassCard>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
        <GlassCard className="stagger-3" style={{ padding: 28 }}>
          <h3 style={{ fontSize: 12, fontWeight: 600, color: "var(--text-dim)", marginBottom: 16, textTransform: "uppercase", letterSpacing: "0.08em" }}>Highlights</h3>
          <ul style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: 10 }}>
            {INSIGHTS.highlights.map((h, i) => (
              <li key={i} style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 13, color: "var(--text-secondary)" }}>
                <span style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--cyan)" }} />
                {h}
              </li>
            ))}
          </ul>
        </GlassCard>
        <GlassCard className="stagger-3" style={{ padding: 28 }}>
          <h3 style={{ fontSize: 12, fontWeight: 600, color: "var(--text-dim)", marginBottom: 16, textTransform: "uppercase", letterSpacing: "0.08em" }}>Recommendations</h3>
          <ul style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: 10 }}>
            {INSIGHTS.recommendations.map((r, i) => (
              <li key={i} style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 13, color: "var(--text-secondary)" }}>
                <span style={{ color: "var(--green)" }}>{I.zap}</span>
                {r}
              </li>
            ))}
          </ul>
        </GlassCard>
      </div>
    </div>
  );
}
