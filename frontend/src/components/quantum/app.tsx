"use client";

import { useEffect, useState, useCallback } from "react";
import { QuantumStyles } from "./styles";
import { MeshGradient } from "./mesh-gradient";
import { ParticleField } from "./particle-field";
import { QuantumSidebar } from "./sidebar";
import { Toast } from "./ui";
import { LEADS, type Lead } from "./data";
import {
  ViewDashboard,
  ViewLeads,
  ViewCampaigns,
  ViewChatbot,
  ViewSMS,
  ViewVoice,
  ViewInsights,
  ViewDemo,
} from "./views";
import { getLeads } from "@/lib/api";
import type { Lead as ApiLead } from "@/lib/types";

const PAGES: Record<string, React.ComponentType<any>> = {
  dashboard: ViewDashboard,
  leads: ViewLeads,
  campaigns: ViewCampaigns,
  chatbot: ViewChatbot,
  sms: ViewSMS,
  voice: ViewVoice,
  insights: ViewInsights,
  demo: ViewDemo,
};

export function QuantumApp() {
  const [page, setPage] = useState("dashboard");
  const [leads, setLeads] = useState<Lead[]>(() => [...LEADS]);
  const [ctxLead, setCtxLead] = useState<Lead | null>(null);
  const [toast, setToast] = useState<{ msg: string; type?: "success" | "error" | "info" } | null>(null);
  const onToast = useCallback((msg: string, type: "success" | "error" | "info" = "success") => setToast({ msg, type }), []);

  // Replace mock leads with real leads from API when available
  useEffect(() => {
    const loadLeads = async () => {
      try {
        const res = await getLeads(1, 20);
        const apiItems = (res.data?.items ?? []) as ApiLead[];
        if (!apiItems.length) return;
        const mapped: Lead[] = apiItems.map((l) => {
          const score = l.ai_score?.score ?? 50;
          const priority = (l.ai_score?.priority ?? "Warm") as Lead["priority"];
          return {
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
            score,
            priority,
          };
        });
        setLeads(mapped);
        if (!ctxLead && mapped.length) {
          setCtxLead(mapped[0]);
        }
      } catch {
        // If API fails, keep using mock LEADS so UI still works
      }
    };
    void loadLeads();
  }, [ctxLead]);

  const View = PAGES[page] ?? ViewDashboard;
  const viewProps: Record<string, unknown> = {};
  if (page === "leads") Object.assign(viewProps, { leads, setLeads, onToast });
  if (page === "campaigns") Object.assign(viewProps, { onToast });
  if (page === "chatbot") Object.assign(viewProps, { ctxLead, setCtxLead, leads, setLeads, onToast });
  if (page === "sms" || page === "voice" || page === "demo") Object.assign(viewProps, { onToast });

  return (
    <div className="quantum-dashboard" style={{ position: "relative", minHeight: "100vh", display: "flex" }}>
      <QuantumStyles />
      <MeshGradient />
      <ParticleField />
      <QuantumSidebar page={page} setPage={setPage} />
      <main style={{ flex: 1, position: "relative", zIndex: 1, padding: "32px 40px", overflow: "auto" }}>
        <View {...viewProps} />
      </main>
      {toast && <Toast msg={toast.msg} type={toast.type} onClose={() => setToast(null)} />}
    </div>
  );
}
