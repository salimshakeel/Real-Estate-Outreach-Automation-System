"use client";

import { useEffect, useState } from "react";
import type { Lead } from "../data";
import { GlassCard, Btn, Input, PriorityBadge, I } from "../ui";
import { getChatHistory, sendChatMessage } from "@/lib/api";
import type { ChatMessage, ChatbotResponse } from "@/lib/types";

export function ViewChatbot({
  ctxLead,
  setCtxLead,
  leads,
  setLeads,
  onToast,
}: {
  ctxLead: Lead | null;
  setCtxLead: (l: Lead | null) => void;
  leads: Lead[];
  setLeads: (l: Lead[]) => void;
  onToast: (m: string) => void;
}) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // Load history when switching leads
  useEffect(() => {
    const load = async () => {
      if (!ctxLead) {
        setMessages([]);
        return;
      }
      setLoadingHistory(true);
      try {
        const res = await getChatHistory(ctxLead.id);
        const history = (res.data?.messages ?? []) as ChatMessage[];
        setMessages(history);
      } catch {
        // Fallback: start fresh if history fails
        setMessages([]);
      } finally {
        setLoadingHistory(false);
      }
    };
    void load();
  }, [ctxLead]);

  const send = async () => {
    if (!ctxLead || !input.trim()) return;
    const userMsg: ChatMessage = { role: "user", content: input.trim() };
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInput("");
    setSending(true);
    try {
      const res = await sendChatMessage(ctxLead.id, newMessages);
      const data = res.data as ChatbotResponse;
      setMessages((m) => [...m, { role: "assistant", content: data.reply }]);
      if (data.updated_lead_score !== null && data.updated_lead_score !== undefined) {
        setLeads(
          leads.map((l) =>
            l.id === ctxLead.id ? { ...l, score: data.updated_lead_score! } : l,
          ),
        );
        setCtxLead({ ...ctxLead, score: data.updated_lead_score });
      }
      if (data.next_action?.type === "book_meeting") onToast("Lead ready to book");
    } catch {
      onToast("Chatbot request failed");
    } finally {
      setSending(false);
    }
  };

  return (
    <div style={{ display: "flex", gap: 24, height: "calc(100vh - 120px)", minHeight: 400 }}>
      <GlassCard style={{ width: 280, flexShrink: 0, display: "flex", flexDirection: "column", overflow: "hidden" }}>
        <h3 style={{ fontSize: 12, fontWeight: 600, color: "var(--text-dim)", marginBottom: 12, textTransform: "uppercase", letterSpacing: "0.08em" }}>Leads</h3>
        <div style={{ flex: 1, overflow: "auto", display: "flex", flexDirection: "column", gap: 6 }}>
          {leads.map((l) => (
            <button
              key={l.id}
              onClick={() => { setCtxLead(l); setMessages([]); }}
              style={{
                padding: "12px 14px", borderRadius: "var(--radius-sm)", border: "none", background: ctxLead?.id === l.id ? "rgba(0,234,255,0.1)" : "rgba(255,255,255,0.04)", color: "var(--text)", cursor: "pointer", textAlign: "left", fontSize: 13,
              }}
            >
              <div style={{ fontWeight: 600 }}>{l.first_name} {l.last_name}</div>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 4 }}>
                <PriorityBadge p={l.priority} />
                <span style={{ fontSize: 11, color: "var(--text-dim)" }}>{l.score}</span>
              </div>
            </button>
          ))}
        </div>
      </GlassCard>
      <GlassCard style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", minWidth: 0 }}>
        {ctxLead ? (
          <>
            <div style={{ borderBottom: "1px solid var(--border)", padding: "14px 20px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <span style={{ fontWeight: 700, fontSize: 15 }}>{ctxLead.first_name} {ctxLead.last_name}</span>
                <span style={{ color: "var(--text-dim)", marginLeft: 12, fontSize: 13 }}>{ctxLead.company}</span>
              </div>
              <PriorityBadge p={ctxLead.priority} />
            </div>
            <div style={{ flex: 1, overflow: "auto", padding: 20, display: "flex", flexDirection: "column", gap: 16 }}>
              <div style={{ padding: "8px 12px", borderRadius: 8, background: "rgba(0,234,255,0.06)", border: "1px solid rgba(0,234,255,0.2)", fontSize: 12, color: "var(--text-secondary)", marginBottom: 8 }}>
                <strong style={{ color: "var(--cyan)" }}>How this works:</strong> You’re simulating the <strong>lead</strong> ({ctxLead.first_name}). Messages you type are treated as if {ctxLead.first_name} said them. The AI replies as your <strong>sales assistant</strong> to qualify and book meetings.
              </div>
              {loadingHistory && (
                <div style={{ color: "var(--text-dim)", fontSize: 13 }}>Loading history…</div>
              )}
              {!loadingHistory && messages.length === 0 && (
                <div style={{ color: "var(--text-dim)", fontSize: 13 }}>Type what the lead might say (e.g. “What’s the pricing?” or “I’d like a demo”). The AI will respond as the sales assistant.</div>
              )}
              {messages.map((msg, i) => (
                <div key={i} style={{ alignSelf: msg.role === "user" ? "flex-end" : "flex-start", maxWidth: "85%", padding: "12px 16px", borderRadius: 12, background: msg.role === "user" ? "var(--cyan-dim)" : "rgba(255,255,255,0.06)", fontSize: 13 }}>
                  {msg.content}
                </div>
              ))}
            </div>
            <div style={{ padding: 16, borderTop: "1px solid var(--border)", display: "flex", gap: 10 }}>
              <Input placeholder={`What would ${ctxLead.first_name} say? (simulate lead)`} value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === "Enter" && send()} style={{ flex: 1 }} />
              <Btn primary icon={I.send} onClick={send} disabled={sending || !input.trim()}>Send</Btn>
            </div>
          </>
        ) : (
          <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", color: "var(--text-dim)", fontSize: 14 }}>Select a lead to start chatting</div>
        )}
      </GlassCard>
    </div>
  );
}
