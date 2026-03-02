"use client";

import { useState } from "react";
import { LEADS, CONFIG } from "../data";
import { GlassCard, Btn, Input, Badge, I } from "../ui";

export function ViewDemo({ onToast }: { onToast: (m: string) => void }) {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [replyText, setReplyText] = useState("");
  const [daysFromNow, setDaysFromNow] = useState(3);
  const [loading, setLoading] = useState<string | null>(null);

  const lead = LEADS.find((l) => l.id === selectedId);
  const services = CONFIG?.services ?? { database: true, sendgrid: false, twilio_sms: false, retell_voice: false, openai: true, calendly: false };

  const simulate = async (action: "open" | "reply" | "booking") => {
    if (!selectedId) return;
    setLoading(action);
    await new Promise((r) => setTimeout(r, 600));
    setLoading(null);
    onToast(`Simulated ${action}`);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 28 }}>
      <div>
        <h1 style={{ fontSize: 28, fontWeight: 800, letterSpacing: "-0.03em", marginBottom: 8 }}>Demo Tools</h1>
        <p style={{ fontSize: 14, color: "var(--text-secondary)" }}>Simulate events and inspect service status</p>
      </div>
      <GlassCard style={{ padding: 28 }}>
        <h3 style={{ fontSize: 12, fontWeight: 600, color: "var(--text-dim)", marginBottom: 16, textTransform: "uppercase", letterSpacing: "0.08em" }}>Select lead</h3>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          {LEADS.map((l) => (
            <button
              key={l.id}
              onClick={() => setSelectedId(l.id)}
              style={{
                padding: "10px 18px", borderRadius: "var(--radius-sm)", border: selectedId === l.id ? "2px solid var(--cyan)" : "1px solid var(--border)", background: selectedId === l.id ? "rgba(0,234,255,0.08)" : "rgba(255,255,255,0.04)", color: "var(--text)", cursor: "pointer", fontSize: 13, fontWeight: 500,
              }}
            >
              {l.first_name} {l.last_name}
            </button>
          ))}
        </div>
      </GlassCard>
      {lead && (
        <>
          <GlassCard style={{ padding: 28 }}>
            <h3 style={{ fontSize: 12, fontWeight: 600, color: "var(--text-dim)", marginBottom: 16, textTransform: "uppercase", letterSpacing: "0.08em" }}>Simulate</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 10, alignItems: "center" }}>
                <Btn glass onClick={() => simulate("open")} disabled={!!loading}>Simulate open</Btn>
                <Btn glass onClick={() => simulate("reply")} disabled={!!loading}>Simulate reply</Btn>
                <Btn glass onClick={() => simulate("booking")} disabled={!!loading}>Simulate booking</Btn>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                <div>
                  <label style={{ fontSize: 11, color: "var(--text-dim)", marginBottom: 6, display: "block" }}>Reply text (optional)</label>
                  <Input placeholder="e.g. Yes, interested" value={replyText} onChange={(e) => setReplyText(e.target.value)} />
                </div>
                <div>
                  <label style={{ fontSize: 11, color: "var(--text-dim)", marginBottom: 6, display: "block" }}>Booking days from now</label>
                  <Input type="number" min={0} value={daysFromNow} onChange={(e) => setDaysFromNow(Number(e.target.value) || 0)} />
                </div>
              </div>
            </div>
          </GlassCard>
          <GlassCard style={{ padding: 28 }}>
            <h3 style={{ fontSize: 12, fontWeight: 600, color: "var(--text-dim)", marginBottom: 16, textTransform: "uppercase", letterSpacing: "0.08em" }}>Service status</h3>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
              {Object.entries(services).map(([key, ok]) => (
                <Badge key={key} color={ok ? "var(--green)" : "var(--text-dim)"} bg={ok ? "rgba(0,230,138,0.15)" : "rgba(255,255,255,0.06)"}>
                  {key.replace(/_/g, " ")}: {ok ? "ON" : "OFF"}
                </Badge>
              ))}
            </div>
          </GlassCard>
        </>
      )}
    </div>
  );
}
