"use client";

import { useState } from "react";
import { LEADS, type Lead } from "../data";
import { api } from "../api";
import { GlassCard, Btn, Input, TextArea, PriorityBadge, I } from "../ui";

const PLACEHOLDERS = ["{{first_name}}", "{{last_name}}", "{{company}}", "{{property_type}}"];

export function ViewSMS({ onToast }: { onToast: (m: string) => void }) {
  const [ctxLead, setCtxLead] = useState<Lead | null>(null);
  const [body, setBody] = useState("");
  const [sending, setSending] = useState(false);
  const [history, setHistory] = useState<{ lead_id: number; body: string; at: string }[]>([]);

  const send = async () => {
    if (!ctxLead || !body.trim()) return;
    setSending(true);
    try {
      await api.sendSMS();
      setHistory((h) => [...h, { lead_id: ctxLead.id, body, at: new Date().toISOString() }]);
      onToast("SMS sent");
      setBody("");
    } finally {
      setSending(false);
    }
  };

  const insertPlaceholder = (p: string) => {
    if (!ctxLead) return;
    const v: Record<string, string> = { "{{first_name}}": ctxLead.first_name, "{{last_name}}": ctxLead.last_name, "{{company}}": ctxLead.company, "{{property_type}}": ctxLead.property_type };
    setBody((b) => b + (v[p] ?? p));
  };

  return (
    <div style={{ display: "flex", gap: 24, minHeight: 400 }}>
      <GlassCard style={{ width: 280, flexShrink: 0 }}>
        <h3 style={{ fontSize: 12, fontWeight: 600, color: "var(--text-dim)", marginBottom: 12, textTransform: "uppercase", letterSpacing: "0.08em" }}>Leads</h3>
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          {LEADS.filter((l) => l.phone).map((l) => (
            <button key={l.id} onClick={() => setCtxLead(l)} style={{ padding: "12px 14px", borderRadius: "var(--radius-sm)", border: "none", background: ctxLead?.id === l.id ? "rgba(0,234,255,0.1)" : "rgba(255,255,255,0.04)", color: "var(--text)", cursor: "pointer", textAlign: "left", fontSize: 13 }}>
              <div style={{ fontWeight: 600 }}>{l.first_name} {l.last_name}</div>
              <div style={{ fontSize: 11, color: "var(--text-dim)" }}>{l.phone}</div>
            </button>
          ))}
        </div>
      </GlassCard>
      <GlassCard style={{ flex: 1, display: "flex", flexDirection: "column", gap: 20, minWidth: 0 }}>
        {ctxLead ? (
          <>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontWeight: 600 }}>To: {ctxLead.first_name} {ctxLead.last_name} · {ctxLead.phone}</span>
              <PriorityBadge p={ctxLead.priority} />
            </div>
            <div>
              <div style={{ fontSize: 11, color: "var(--text-dim)", marginBottom: 8 }}>Placeholders</div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {PLACEHOLDERS.map((p) => (
                  <button key={p} onClick={() => insertPlaceholder(p)} style={{ padding: "6px 12px", borderRadius: 6, border: "1px solid var(--border)", background: "rgba(255,255,255,0.04)", color: "var(--cyan)", fontSize: 12, cursor: "pointer" }}>{p}</button>
                ))}
              </div>
            </div>
            <TextArea placeholder="Message…" value={body} onChange={(e) => setBody(e.target.value)} rows={4} />
            <Btn primary icon={I.send} onClick={send} disabled={sending || !body.trim()}>Send SMS</Btn>
            {history.filter((h) => h.lead_id === ctxLead.id).length > 0 && (
              <div>
                <div style={{ fontSize: 11, color: "var(--text-dim)", marginBottom: 8 }}>History</div>
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  {history.filter((h) => h.lead_id === ctxLead.id).slice(-5).reverse().map((h, i) => (
                    <div key={i} style={{ padding: 12, background: "rgba(255,255,255,0.04)", borderRadius: "var(--radius-sm)", fontSize: 12 }}>{h.body} <span style={{ color: "var(--text-dim)" }}>{new Date(h.at).toLocaleString()}</span></div>
                  ))}
                </div>
              </div>
            )}
          </>
        ) : (
          <div style={{ color: "var(--text-dim)", fontSize: 14 }}>Select a lead with a phone number</div>
        )}
      </GlassCard>
    </div>
  );
}
