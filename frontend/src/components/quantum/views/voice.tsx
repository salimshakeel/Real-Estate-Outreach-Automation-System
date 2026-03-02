"use client";

import { useState } from "react";
import { LEADS, type Lead } from "../data";
import { api } from "../api";
import { GlassCard, Btn, PriorityBadge, I } from "../ui";

export function ViewVoice({ onToast }: { onToast: (m: string) => void }) {
  const [ctxLead, setCtxLead] = useState<Lead | null>(null);
  const [calling, setCalling] = useState(false);
  const [callActive, setCallActive] = useState(false);
  const [history, setHistory] = useState<{ lead_id: number; at: string }[]>([]);

  const startCall = async () => {
    if (!ctxLead) return;
    setCalling(true);
    try {
      await api.startCall();
      setCallActive(true);
      setHistory((h) => [...h, { lead_id: ctxLead.id, at: new Date().toISOString() }]);
      onToast("Call started");
      setTimeout(() => setCallActive(false), 5000);
    } finally {
      setCalling(false);
    }
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
      <GlassCard style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 24, minWidth: 0 }}>
        {ctxLead ? (
          <>
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: 22, fontWeight: 700, marginBottom: 8 }}>{ctxLead.first_name} {ctxLead.last_name}</div>
              <div style={{ color: "var(--text-secondary)", marginBottom: 8 }}>{ctxLead.company}</div>
              <PriorityBadge p={ctxLead.priority} />
            </div>
            {callActive ? (
              <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "16px 24px", background: "var(--green)", color: "#000", borderRadius: 12, fontWeight: 600 }}>
                <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#000", animation: "pulse 1s ease infinite" }} />
                Call in progress…
              </div>
            ) : (
              <Btn primary icon={I.call} onClick={startCall} disabled={calling}>{calling ? "Connecting…" : "Start voice call"}</Btn>
            )}
            {history.filter((h) => h.lead_id === ctxLead.id).length > 0 && (
              <div style={{ width: "100%", maxWidth: 400 }}>
                <div style={{ fontSize: 11, color: "var(--text-dim)", marginBottom: 8 }}>Call history</div>
                {history.filter((h) => h.lead_id === ctxLead.id).slice(-5).reverse().map((h, i) => (
                  <div key={i} style={{ padding: 10, background: "rgba(255,255,255,0.04)", borderRadius: 8, fontSize: 12, marginBottom: 6 }}>{new Date(h.at).toLocaleString()}</div>
                ))}
              </div>
            )}
          </>
        ) : (
          <div style={{ color: "var(--text-dim)", fontSize: 14 }}>Select a lead to start a voice call</div>
        )}
      </GlassCard>
    </div>
  );
}
