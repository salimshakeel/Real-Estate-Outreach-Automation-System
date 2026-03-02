"use client";

import { useState, useMemo } from "react";
import { LEADS, type Lead } from "../data";
import { api } from "../api";
import { GlassCard, Badge, PriorityBadge, Btn, Input, Modal, I } from "../ui";

export function ViewLeads({ leads, setLeads, onToast }: { leads: Lead[]; setLeads: (l: Lead[]) => void; onToast: (m: string) => void }) {
  const [search, setSearch] = useState("");
  const [scoreModal, setScoreModal] = useState(false);
  const [detailLead, setDetailLead] = useState<Lead | null>(null);
  const [scoring, setScoring] = useState(false);
  const list = useMemo(() => {
    if (!search.trim()) return leads;
    const q = search.toLowerCase();
    return leads.filter((l) =>
      [l.first_name, l.last_name, l.email, l.company].some((x) => x?.toLowerCase().includes(q))
    );
  }, [leads, search]);

  const runScore = async () => {
    setScoring(true);
    try {
      const res = await api.scoreBulk(leads.map((l) => l.id));
      const next = leads.map((l) => {
        const r = res.results.find((x) => x.lead_id === l.id);
        if (!r) return l;
        return { ...l, score: r.score, priority: r.priority };
      });
      setLeads(next);
      onToast(`Scored ${res.scored} leads`);
      setScoreModal(false);
    } finally {
      setScoring(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 16 }}>
        <h1 style={{ fontSize: 28, fontWeight: 800, letterSpacing: "-0.03em" }}>Leads</h1>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <div style={{ position: "relative" }}>
            <span style={{ position: "absolute", left: 14, top: "50%", transform: "translateY(-50%)", color: "var(--text-dim)" }}>{I.search}</span>
            <Input placeholder="Search leads..." value={search} onChange={(e) => setSearch(e.target.value)} style={{ paddingLeft: 40, width: 260 }} />
          </div>
          <Btn glass onClick={() => setScoreModal(true)} icon={I.spark}>Score all</Btn>
        </div>
      </div>
      <GlassCard style={{ overflow: "hidden", padding: 0 }}>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border)" }}>
                <th style={{ textAlign: "left", padding: "14px 20px", fontWeight: 600, color: "var(--text-dim)" }}>Name</th>
                <th style={{ textAlign: "left", padding: "14px 20px", fontWeight: 600, color: "var(--text-dim)" }}>Company</th>
                <th style={{ textAlign: "left", padding: "14px 20px", fontWeight: 600, color: "var(--text-dim)" }}>Status</th>
                <th style={{ textAlign: "left", padding: "14px 20px", fontWeight: 600, color: "var(--text-dim)" }}>Score</th>
                <th style={{ textAlign: "left", padding: "14px 20px", fontWeight: 600, color: "var(--text-dim)" }}>Priority</th>
                <th style={{ textAlign: "right", padding: "14px 20px", fontWeight: 600, color: "var(--text-dim)" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {list.map((l) => (
                <tr key={l.id} style={{ borderBottom: "1px solid var(--border)" }}>
                  <td style={{ padding: "14px 20px", fontWeight: 500 }}>{l.first_name} {l.last_name}</td>
                  <td style={{ padding: "14px 20px", color: "var(--text-secondary)" }}>{l.company}</td>
                  <td style={{ padding: "14px 20px" }}><Badge bg="rgba(255,255,255,0.08)" color="var(--text-secondary)">{l.status}</Badge></td>
                  <td style={{ padding: "14px 20px", fontWeight: 700, color: "var(--cyan)" }}>{l.score}</td>
                  <td style={{ padding: "14px 20px" }}><PriorityBadge p={l.priority} /></td>
                  <td style={{ padding: "14px 20px", textAlign: "right" }}>
                    <Btn sm glass onClick={() => setDetailLead(l)}>View</Btn>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </GlassCard>

      <Modal open={scoreModal} onClose={() => setScoreModal(false)} title="Bulk AI scoring">
        <p style={{ color: "var(--text-secondary)", fontSize: 13, marginBottom: 20 }}>Re-score all {leads.length} leads with AI. This may take a few seconds.</p>
        <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
          <Btn glass onClick={() => setScoreModal(false)}>Cancel</Btn>
          <Btn primary onClick={runScore} disabled={scoring}>{scoring ? "Scoring…" : "Run scoring"}</Btn>
        </div>
      </Modal>

      <Modal open={!!detailLead} onClose={() => setDetailLead(null)} title={detailLead ? `${detailLead.first_name} ${detailLead.last_name}` : ""} wide>
        {detailLead && (
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, fontSize: 13 }}>
              <div><span style={{ color: "var(--text-dim)" }}>Email</span><br />{detailLead.email}</div>
              <div><span style={{ color: "var(--text-dim)" }}>Phone</span><br />{detailLead.phone || "—"}</div>
              <div><span style={{ color: "var(--text-dim)" }}>Company</span><br />{detailLead.company}</div>
              <div><span style={{ color: "var(--text-dim)" }}>Address</span><br />{detailLead.address}</div>
              <div><span style={{ color: "var(--text-dim)" }}>Property type</span><br />{detailLead.property_type}</div>
              <div><span style={{ color: "var(--text-dim)" }}>Est. value</span><br />{detailLead.estimated_value}</div>
            </div>
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <PriorityBadge p={detailLead.priority} />
              <Badge bg="var(--cyan-dim)" color="var(--cyan)">Score {detailLead.score}</Badge>
              <Badge bg="rgba(255,255,255,0.08)" color="var(--text-secondary)">{detailLead.status}</Badge>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
