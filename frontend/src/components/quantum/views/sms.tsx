"use client";

import { useEffect, useState } from "react";
import { getLeads, getSMSHistory, sendSMS } from "@/lib/api";
import type { Lead as ApiLead } from "@/lib/types";
import { type Lead } from "../data";
import { GlassCard, Btn, TextArea, PriorityBadge, I } from "../ui";

const PLACEHOLDERS = ["{{first_name}}", "{{last_name}}", "{{company}}", "{{property_type}}"];

export function ViewSMS({ onToast }: { onToast: (m: string) => void }) {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [ctxLead, setCtxLead] = useState<Lead | null>(null);
  const [body, setBody] = useState("");
  const [sending, setSending] = useState(false);
  const [history, setHistory] = useState<{ body: string; sent_at: string }[]>([]);

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
        const res = await getSMSHistory(ctxLead.id);
        const list = (res.data?.messages ?? []) as { body: string; sent_at?: string; created_at?: string }[];
        setHistory(list.map((m) => ({ body: m.body, sent_at: m.sent_at ?? m.created_at ?? new Date().toISOString() })));
      } catch {
        setHistory([]);
      }
    };
    void load();
  }, [ctxLead]);

  const send = async () => {
    if (!ctxLead || !body.trim()) return;
    setSending(true);
    try {
      await sendSMS(ctxLead.id, body.trim(), true);
      setHistory((h) => [{ body: body.trim(), sent_at: new Date().toISOString() }, ...h]);
      onToast("SMS sent");
      setBody("");
    } catch {
      onToast("SMS failed — check lead has phone and Twilio is configured");
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
        <h3 style={{ fontSize: 12, fontWeight: 600, color: "var(--text-dim)", marginBottom: 12, textTransform: "uppercase", letterSpacing: "0.08em" }}>
          Leads {leads.some((l) => l.phone?.trim()) ? `(${leads.filter((l) => l.phone?.trim()).length} with phone)` : ""}
        </h3>
        {leads.length === 0 ? (
          <p style={{ fontSize: 12, color: "var(--text-dim)" }}>No leads yet. Upload CSV or add leads in the Leads section.</p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {leads.map((l) => {
              const hasPhone = Boolean(l.phone?.trim());
              return (
                <button
                  key={l.id}
                  onClick={() => setCtxLead(l)}
                  style={{
                    padding: "12px 14px",
                    borderRadius: "var(--radius-sm)",
                    border: "none",
                    background: ctxLead?.id === l.id ? "rgba(0,234,255,0.1)" : "rgba(255,255,255,0.04)",
                    color: hasPhone ? "var(--text)" : "var(--text-dim)",
                    cursor: "pointer",
                    textAlign: "left",
                    fontSize: 13,
                    opacity: hasPhone ? 1 : 0.85,
                  }}
                >
                  <div style={{ fontWeight: 600 }}>{l.first_name} {l.last_name}</div>
                  <div style={{ fontSize: 11, color: "var(--text-dim)" }}>
                    {hasPhone ? l.phone : "No phone — add in Leads"}
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </GlassCard>
      <GlassCard style={{ flex: 1, display: "flex", flexDirection: "column", gap: 20, minWidth: 0 }}>
        {ctxLead ? (
          <>
            {!ctxLead.phone?.trim() && (
              <div style={{ padding: "12px 14px", borderRadius: 8, background: "rgba(255,184,0,0.1)", border: "1px solid rgba(255,184,0,0.3)", fontSize: 13, color: "var(--amber)", marginBottom: 12 }}>
                <strong>No phone number.</strong> Add a phone for {ctxLead.first_name} in the <strong>Leads</strong> section to send SMS.
              </div>
            )}
            <div style={{ padding: "8px 12px", borderRadius: 8, background: "rgba(0,234,255,0.06)", border: "1px solid rgba(0,234,255,0.2)", fontSize: 12, color: "var(--text-secondary)", marginBottom: 12 }}>
              <strong style={{ color: "var(--cyan)" }}>SMS role:</strong> You send a text to the <strong>lead</strong> ({ctxLead.first_name}) at their phone. Use for reminders, follow-ups, or re-engagement. Placeholders get replaced with the lead’s data.
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontWeight: 600 }}>To: {ctxLead.first_name} {ctxLead.last_name}{ctxLead.phone?.trim() ? ` · ${ctxLead.phone}` : " (no phone)"}</span>
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
            <Btn primary icon={I.send} onClick={send} disabled={sending || !body.trim() || !ctxLead.phone?.trim()}>Send SMS</Btn>
            {history.length > 0 && (
              <div>
                <div style={{ fontSize: 11, color: "var(--text-dim)", marginBottom: 8 }}>History</div>
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  {history.slice(0, 10).map((h, i) => (
                    <div key={i} style={{ padding: 12, background: "rgba(255,255,255,0.04)", borderRadius: "var(--radius-sm)", fontSize: 12 }}>{h.body} <span style={{ color: "var(--text-dim)" }}>{new Date(h.sent_at).toLocaleString()}</span></div>
                  ))}
                </div>
              </div>
            )}
          </>
        ) : leads.length === 0 ? (
          <div style={{ color: "var(--text-dim)", fontSize: 14 }}>No leads yet. Go to <strong>Leads</strong> to upload or add leads.</div>
        ) : (
          <div style={{ color: "var(--text-dim)", fontSize: 14 }}>
            Select a lead to send SMS. If the list shows &quot;No phone&quot;, go to <strong>Leads</strong>, open that lead, and add a <strong>Phone</strong> number so you can send SMS.
          </div>
        )}
      </GlassCard>
    </div>
  );
}
