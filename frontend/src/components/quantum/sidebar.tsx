"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { I } from "./ui";
import { CONFIG } from "./data";

const NAV = [
  { id: "dashboard", label: "Dashboard", icon: I.grid },
  { id: "leads", label: "Leads", icon: I.users },
  { id: "campaigns", label: "Campaigns", icon: I.mail },
  { id: "templates", label: "Templates", icon: I.fileText, href: "/templates" },
  { id: "chatbot", label: "Chatbot", icon: I.chat },
  { id: "sms", label: "SMS", icon: I.phone },
  { id: "voice", label: "Voice", icon: I.call },
  { id: "insights", label: "AI Insights", icon: I.spark },
  { id: "demo", label: "Demo Tools", icon: I.gear },
] as const;

export function QuantumSidebar({ page, setPage }: { page: string; setPage: (p: string) => void }) {
  const pathname = usePathname();
  const isTemplates = pathname === "/templates";

  return (
    <aside className="quantum-sidebar" style={{ width: 260, minHeight: "100vh", padding: "28px 0", borderRight: "1px solid var(--border)", display: "flex", flexDirection: "column", gap: 24 }}>
      <div style={{ padding: "0 24px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 36, height: 36, borderRadius: 10, background: "linear-gradient(135deg, var(--cyan), var(--purple))", display: "flex", alignItems: "center", justifyContent: "center", color: "#000", fontWeight: 800, fontSize: 16 }}>Q</div>
          <span style={{ fontSize: 18, fontWeight: 700, letterSpacing: "-0.03em" }}>Quantum Outreach</span>
        </div>
      </div>
      <nav style={{ flex: 1, display: "flex", flexDirection: "column", gap: 4 }}>
        {NAV.map((item) => {
          const isActive = "href" in item && item.href ? isTemplates && item.id === "templates" : page === item.id;
          if ("href" in item && item.href) {
            return (
              <Link
                key={item.id}
                href={item.href}
                style={{
                  display: "flex", alignItems: "center", gap: 12, padding: "12px 24px", margin: "0 12px", borderRadius: "var(--radius-sm)",
                  background: isActive ? "rgba(0,234,255,0.08)" : "transparent", color: isActive ? "var(--cyan)" : "var(--text-secondary)",
                  textDecoration: "none", fontSize: 13, fontWeight: 500, transition: "all 0.2s ease",
                }}
              >
                {item.icon}
                {item.label}
              </Link>
            );
          }
          return (
            <button
              key={item.id}
              onClick={() => setPage(item.id)}
              style={{
                display: "flex", alignItems: "center", gap: 12, padding: "12px 24px", margin: "0 12px", borderRadius: "var(--radius-sm)",
                background: page === item.id ? "rgba(0,234,255,0.08)" : "transparent", color: page === item.id ? "var(--cyan)" : "var(--text-secondary)",
                border: "none", cursor: "pointer", fontSize: 13, fontWeight: 500, textAlign: "left", transition: "all 0.2s ease",
              }}
            >
              {item.icon}
              {item.label}
            </button>
          );
        })}
      </nav>
      {CONFIG && (
        <div style={{ padding: "0 24px", display: "flex", flexWrap: "wrap", gap: 8 }}>
          {CONFIG.ai_powered && <span style={{ fontSize: 10, padding: "4px 8px", borderRadius: 6, background: "var(--cyan-dim)", color: "var(--cyan)", fontWeight: 600 }}>AI-Powered</span>}
          {CONFIG.demo_mode && <span style={{ fontSize: 10, padding: "4px 8px", borderRadius: 6, background: "rgba(255,184,0,0.15)", color: "var(--amber)", fontWeight: 600 }}>Demo</span>}
        </div>
      )}
    </aside>
  );
}
