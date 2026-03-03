"use client";

import { useEffect, useState, useCallback } from "react";
import { getInsights } from "@/lib/api";
import type { WeeklyInsights } from "@/lib/types";
import { INSIGHTS } from "../data";
import { GlassCard, GlowBar, I } from "../ui";

function toStats(ss: WeeklyInsights["stats_snapshot"] | undefined) {
  if (!ss) return { emails_sent: 0, open_rate: 0, reply_rate: 0, bookings: 0 };
  return {
    emails_sent: ss.emails_sent ?? 0,
    open_rate: ss.open_rate ?? 0,
    reply_rate: ss.reply_rate ?? 0,
    bookings: ss.bookings ?? 0,
  };
}

export function ViewInsights() {
  const [insights, setInsights] = useState<WeeklyInsights | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchInsights = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    try {
      const res = await getInsights();
      const data = res.data as WeeklyInsights;
      if (data?.period != null) setInsights(data);
    } catch {
      // Fallback to mock data if API fails
      setInsights({
        period: INSIGHTS.period,
        summary: INSIGHTS.summary,
        highlights: INSIGHTS.highlights,
        recommendations: INSIGHTS.recommendations,
        stats_snapshot: {
          emails_sent: INSIGHTS.stats.emails_sent,
          opens: INSIGHTS.stats.opens ?? 0,
          replies: INSIGHTS.stats.replies ?? 0,
          bookings: INSIGHTS.stats.bookings,
          open_rate: INSIGHTS.stats.open_rate,
          reply_rate: INSIGHTS.stats.reply_rate,
          prev_week_open_rate: INSIGHTS.stats.prev_open ?? 0,
          prev_week_reply_rate: INSIGHTS.stats.prev_reply ?? 0,
          top_campaign: "N/A",
          sms_sent: INSIGHTS.stats.sms ?? 0,
          voice_calls: INSIGHTS.stats.calls ?? 0,
        },
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void fetchInsights();
  }, [fetchInsights]);

  const display = insights ?? {
    period: INSIGHTS.period,
    summary: INSIGHTS.summary,
    highlights: INSIGHTS.highlights,
    recommendations: INSIGHTS.recommendations,
    stats_snapshot: {
      emails_sent: INSIGHTS.stats.emails_sent,
      opens: INSIGHTS.stats.opens ?? 0,
      replies: INSIGHTS.stats.replies ?? 0,
      bookings: INSIGHTS.stats.bookings,
      open_rate: INSIGHTS.stats.open_rate,
      reply_rate: INSIGHTS.stats.reply_rate,
      prev_week_open_rate: INSIGHTS.stats.prev_open ?? 0,
      prev_week_reply_rate: INSIGHTS.stats.prev_reply ?? 0,
      top_campaign: "N/A",
      sms_sent: INSIGHTS.stats.sms ?? 0,
      voice_calls: INSIGHTS.stats.calls ?? 0,
    },
  };
  const s = toStats(display.stats_snapshot);

  if (loading && !insights) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 28 }}>
        <h1 style={{ fontSize: 28, fontWeight: 800, letterSpacing: "-0.03em", marginBottom: 8 }}>AI Insights</h1>
        <p style={{ fontSize: 14, color: "var(--text-secondary)" }}>Loading insights…</p>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 28 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 800, letterSpacing: "-0.03em", marginBottom: 8 }}>AI Insights</h1>
          <p style={{ fontSize: 14, color: "var(--text-secondary)" }}>{display.period}</p>
        </div>
        <button
          type="button"
          onClick={() => void fetchInsights(true)}
          disabled={refreshing}
          style={{
            padding: "10px 18px",
            borderRadius: "var(--radius-sm)",
            border: "1px solid var(--cyan)",
            background: "rgba(0,234,255,0.08)",
            color: "var(--cyan)",
            fontSize: 13,
            fontWeight: 600,
            cursor: refreshing ? "not-allowed" : "pointer",
            opacity: refreshing ? 0.7 : 1,
          }}
        >
          {refreshing ? "Refreshing…" : "Refresh Insights"}
        </button>
      </div>
      <GlassCard className="stagger-1" style={{ padding: 28 }}>
        <h3 style={{ fontSize: 12, fontWeight: 600, color: "var(--text-dim)", marginBottom: 12, textTransform: "uppercase", letterSpacing: "0.08em" }}>Summary</h3>
        <p style={{ fontSize: 15, lineHeight: 1.6, color: "var(--text-secondary)" }}>{display.summary}</p>
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
            {(display.highlights ?? []).map((h, i) => (
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
            {(display.recommendations ?? []).map((r, i) => (
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
