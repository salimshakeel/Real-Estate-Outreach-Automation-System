"use client";

import { useState } from "react";
import { CAMPAIGNS } from "../data";
import { api } from "../api";
import { GlassCard, Badge, Btn, Modal, I } from "../ui";

export function ViewCampaigns({ onToast }: { onToast?: (m: string) => void }) {
  const [generateOpen, setGenerateOpen] = useState(false);
  const [variationsOpen, setVariationsOpen] = useState(false);
  const [analyzeOpen, setAnalyzeOpen] = useState(false);
  const [variations, setVariations] = useState<Awaited<ReturnType<typeof api.getVariations>> | null>(null);
  const [analysis, setAnalysis] = useState<Awaited<ReturnType<typeof api.analyzeAB>> | null>(null);
  const [loading, setLoading] = useState<string | null>(null);

  const runGenerate = async () => {
    setLoading("generate");
    try {
      await api.generateVariations();
      onToast?.("Variations generated");
      setGenerateOpen(false);
    } finally {
      setLoading(null);
    }
  };

  const loadVariations = async () => {
    setLoading("variations");
    try {
      const v = await api.getVariations();
      setVariations(v);
      setVariationsOpen(true);
    } finally {
      setLoading(null);
    }
  };

  const runAnalyze = async () => {
    setLoading("analyze");
    try {
      const a = await api.analyzeAB();
      setAnalysis(a);
      setAnalyzeOpen(true);
    } finally {
      setLoading(null);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 16 }}>
        <h1 style={{ fontSize: 28, fontWeight: 800, letterSpacing: "-0.03em" }}>Campaigns</h1>
        <div style={{ display: "flex", gap: 10 }}>
          <Btn glass onClick={() => setGenerateOpen(true)} icon={I.plus} disabled={!!loading}>Generate variations</Btn>
          <Btn glass onClick={loadVariations} icon={I.bar} disabled={!!loading}>View results</Btn>
          <Btn glass onClick={runAnalyze} icon={I.spark} disabled={!!loading}>{loading === "analyze" ? "Analyzing…" : "Analyze A/B"}</Btn>
        </div>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        {CAMPAIGNS.map((c) => (
          <GlassCard key={c.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 16 }}>
            <div>
              <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 6 }}>{c.name}</div>
              <div style={{ display: "flex", gap: 16, fontSize: 12, color: "var(--text-secondary)" }}>
                <span>Leads: {c.leads_count}</span>
                <span>Sent: {c.emails_sent}</span>
                <span>Opens: {c.opens}</span>
                <span>Replies: {c.replies}</span>
              </div>
            </div>
            <Badge bg={c.status === "active" ? "var(--cyan-dim)" : c.status === "completed" ? "var(--green)" : "rgba(255,255,255,0.08)"} color={c.status === "active" ? "var(--cyan)" : c.status === "completed" ? "var(--green)" : "var(--text-dim)"}>{c.status}</Badge>
          </GlassCard>
        ))}
      </div>

      <Modal open={generateOpen} onClose={() => setGenerateOpen(false)} title="Generate A/B variations">
        <p style={{ color: "var(--text-secondary)", fontSize: 13, marginBottom: 20 }}>AI will generate subject/body variations for your campaign.</p>
        <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
          <Btn glass onClick={() => setGenerateOpen(false)}>Cancel</Btn>
          <Btn primary onClick={runGenerate} disabled={loading === "generate"}>{loading === "generate" ? "Generating…" : "Generate"}</Btn>
        </div>
      </Modal>

      <Modal open={variationsOpen} onClose={() => { setVariationsOpen(false); setVariations(null); }} title="A/B results" wide>
        {variations && (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border)" }}>
                  <th style={{ textAlign: "left", padding: "12px 16px", fontWeight: 600, color: "var(--text-dim)" }}>Var</th>
                  <th style={{ textAlign: "left", padding: "12px 16px", fontWeight: 600, color: "var(--text-dim)" }}>Sends</th>
                  <th style={{ textAlign: "left", padding: "12px 16px", fontWeight: 600, color: "var(--text-dim)" }}>Opens</th>
                  <th style={{ textAlign: "left", padding: "12px 16px", fontWeight: 600, color: "var(--text-dim)" }}>Replies</th>
                  <th style={{ textAlign: "left", padding: "12px 16px", fontWeight: 600, color: "var(--text-dim)" }}>Open %</th>
                  <th style={{ textAlign: "left", padding: "12px 16px", fontWeight: 600, color: "var(--text-dim)" }}>Reply %</th>
                  <th style={{ textAlign: "left", padding: "12px 16px", fontWeight: 600, color: "var(--text-dim)" }}>Winner</th>
                </tr>
              </thead>
              <tbody>
                {variations.map((v) => (
                  <tr key={v.label} style={{ borderBottom: "1px solid var(--border)" }}>
                    <td style={{ padding: "12px 16px", fontWeight: 600 }}>{v.label}</td>
                    <td style={{ padding: "12px 16px" }}>{v.sends}</td>
                    <td style={{ padding: "12px 16px" }}>{v.opens}</td>
                    <td style={{ padding: "12px 16px" }}>{v.replies}</td>
                    <td style={{ padding: "12px 16px" }}>{v.open_rate}%</td>
                    <td style={{ padding: "12px 16px" }}>{v.reply_rate}%</td>
                    <td style={{ padding: "12px 16px" }}>{v.is_winner ? <Badge color="var(--green)" bg="rgba(0,230,138,0.15)">Winner</Badge> : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Modal>

      <Modal open={analyzeOpen} onClose={() => { setAnalyzeOpen(false); setAnalysis(null); }} title="A/B analysis">
        {analysis && (
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <div><span style={{ color: "var(--text-dim)", fontSize: 12 }}>Winner</span><br /><span style={{ fontSize: 18, fontWeight: 700, color: "var(--cyan)" }}>Variation {analysis.winner}</span></div>
            <p style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.5 }}>{analysis.explanation}</p>
            <p style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.5 }}><strong>Pattern:</strong> {analysis.pattern}</p>
          </div>
        )}
      </Modal>
    </div>
  );
}
