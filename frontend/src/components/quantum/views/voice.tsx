"use client";

import { useEffect, useState } from "react";
import { getLeads, getVoiceHistory, startVoiceCall } from "@/lib/api";
import type { Lead as ApiLead } from "@/lib/types";
import { type Lead } from "../data";
import { GlassCard, Btn, PriorityBadge, I } from "../ui";

export function ViewVoice({ onToast }: { onToast: (m: string) => void }) {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [ctxLead, setCtxLead] = useState<Lead | null>(null);
  const [calling, setCalling] = useState(false);
  const [callActive, setCallActive] = useState(false);
  const [history, setHistory] = useState<{ started_at: string; status?: string }[]>([]);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await getLeads(1, 50);
        const items = (res.data?.items ?? []) as ApiLead[];
        const mapped: Lead[] = items.map((l) => ({
          id: l.id,
          first_name: l.first_name,
          last_name: l.last_name ?? "",
          email: l.email,
          phone: l.phone ?? "",
          company: l.company ?? "",
          status: l.status,
          address: l.address ?? "",
          property_type: l.property_type ?? "",
          estimated_value: l.estimated_value ?? "",
          score: l.ai_score?.score ?? 50,
          priority: (l.ai_score?.priority ?? "Warm") as Lead["priority"],
        }));
        setLeads(mapped);
        if (!ctxLead && mapped.length) {
          const firstWithPhone = mapped.find((l) => l.phone && l.phone.trim());
          setCtxLead(firstWithPhone ?? mapped[0]);
        }
      } catch {
        /* keep empty */
      }
    };
    void load();
  }, []);

  useEffect(() => {
    if (!ctxLead) {
      setHistory([]);
      return;
    }
    const load = async () => {
      try {
        const res = await getVoiceHistory(ctxLead.id);
        const list = (res.data?.calls ?? []) as { started_at?: string; status?: string }[];
        setHistory(list.map((c) => ({ started_at: c.started_at ?? new Date().toISOString(), status: c.status })));
      } catch {
        setHistory([]);
      }
    };
    void load();
  }, [ctxLead]);

  const startCall = async () => {
    if (!ctxLead) return;
    setCalling(true);
    try {
      const res = await startVoiceCall(ctxLead.id, null);
      const data = res.data as { success?: boolean; status?: string };
      if (data.success) {
        setCallActive(true);
        setHistory((h) => [{ started_at: new Date().toISOString(), status: "calling" }, ...h]);
        onToast("Call started — lead’s phone will ring (Retell AI will talk)");
        setTimeout(() => setCallActive(false), 8000);
      } else {
        onToast("Call failed — check lead has phone and Retell is configured");
      }
    } catch {
      onToast("Call request failed");
    } finally {
      setCalling(false);
    }
  };

  return (
    <div style={{ display: "flex", gap: 24, minHeight: 400 }}>
      <GlassCard style={{ width: 280, flexShrink: 0 }}>
        <h3 style={{ fontSize: 12, fontWeight: 600, color: "var(--text-dim)", marginBottom: 12, textTransform: "uppercase", letterSpacing: "0.08em" }}>
          Leads {leads.some((l) => l.phone?.trim()) ? `(${leads.filter((l) => l.phone?.trim()).length} with phone)` : ""}
        </h3>
        {leads.length === 0 ? (
          <p style={{ fontSize: 12, color: "var(--text-dim)" }}>No leads yet. Upload CSV or add leads in the Leads section.</p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {leads.map((l) => (
              <button
                key={l.id}
                onClick={() => setCtxLead(l)}
                style={{
                  padding: "12px 14px", borderRadius: "var(--radius-sm)", border: "none", background: ctxLead?.id === l.id ? "rgba(0,234,255,0.1)" : "rgba(255,255,255,0.04)", color: l.phone?.trim() ? "var(--text)" : "var(--text-dim)", cursor: "pointer", textAlign: "left", fontSize: 13, opacity: l.phone?.trim() ? 1 : 0.85,
                }}
              >
                <div style={{ fontWeight: 600 }}>{l.first_name} {l.last_name}</div>
                <div style={{ fontSize: 11, color: "var(--text-dim)" }}>{l.phone?.trim() ? l.phone : "No phone — add in Leads"}</div>
              </button>
            ))}
          </div>
        )}
      </GlassCard>
      <GlassCard style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 24, minWidth: 0 }}>
        {ctxLead ? (
          <>
            {!ctxLead.phone?.trim() && (
              <div style={{ padding: "12px 14px", borderRadius: 8, background: "rgba(255,184,0,0.1)", border: "1px solid rgba(255,184,0,0.3)", fontSize: 13, color: "var(--amber)", marginBottom: 12, textAlign: "left" }}>
                <strong>No phone number.</strong> Add a phone for {ctxLead.first_name} in the <strong>Leads</strong> section to start a voice call.
              </div>
            )}
            <div style={{ padding: "8px 12px", borderRadius: 8, background: "rgba(0,234,255,0.06)", border: "1px solid rgba(0,234,255,0.2)", fontSize: 12, color: "var(--text-secondary)", marginBottom: 16, textAlign: "left" }}>
              <strong style={{ color: "var(--cyan)" }}>Voice role:</strong> You start an <strong>AI phone call</strong> to the lead ({ctxLead.first_name}). Retell AI will ring their phone and conduct the conversation. You use this for hot leads who haven’t booked yet.
            </div>
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: 22, fontWeight: 700, marginBottom: 8 }}>{ctxLead.first_name} {ctxLead.last_name}</div>
              <div style={{ color: "var(--text-secondary)", marginBottom: 8 }}>{ctxLead.company}{ctxLead.phone?.trim() ? ` · ${ctxLead.phone}` : " (no phone)"}</div>
              <PriorityBadge p={ctxLead.priority} />
            </div>
            {callActive ? (
              <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "16px 24px", background: "var(--green)", color: "#000", borderRadius: 12, fontWeight: 600 }}>
                <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#000", animation: "pulse 1s ease infinite" }} />
                Call in progress…
              </div>
            ) : (
              <Btn primary icon={I.call} onClick={startCall} disabled={calling || !ctxLead.phone?.trim()}>{calling ? "Connecting…" : "Start voice call"}</Btn>
            )}
            {history.length > 0 && (
              <div style={{ width: "100%", maxWidth: 400 }}>
                <div style={{ fontSize: 11, color: "var(--text-dim)", marginBottom: 8 }}>Call history</div>
                {history.slice(0, 10).map((h, i) => (
                  <div key={i} style={{ padding: 10, background: "rgba(255,255,255,0.04)", borderRadius: 8, fontSize: 12, marginBottom: 6 }}>{new Date(h.started_at).toLocaleString()}{h.status ? ` · ${h.status}` : ""}</div>
                ))}
              </div>
            )}
          </>
        ) : leads.length === 0 ? (
          <div style={{ color: "var(--text-dim)", fontSize: 14 }}>No leads yet. Go to <strong>Leads</strong> to upload or add leads.</div>
        ) : (
          <div style={{ color: "var(--text-dim)", fontSize: 14 }}>Select a lead to start a voice call. If they have no phone, add one in <strong>Leads</strong>.</div>
        )}
      </GlassCard>
    </div>
  );
}
