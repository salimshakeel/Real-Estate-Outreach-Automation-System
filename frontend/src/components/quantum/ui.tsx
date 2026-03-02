"use client";

import { useState, useEffect, useRef, type ReactNode } from "react";

const I = {
  grid: <svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}><rect x={3} y={3} width={7} height={7} rx={1.5} /><rect x={14} y={3} width={7} height={7} rx={1.5} /><rect x={3} y={14} width={7} height={7} rx={1.5} /><rect x={14} y={14} width={7} height={7} rx={1.5} /></svg>,
  users: <svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" /><circle cx={9} cy={7} r={4} /><path d="M23 21v-2a4 4 0 00-3-3.87" /><path d="M16 3.13a4 4 0 010 7.75" /></svg>,
  mail: <svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}><rect x={2} y={4} width={20} height={16} rx={2} /><path d="M22 7l-10 7L2 7" /></svg>,
  chat: <svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" /></svg>,
  phone: <svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}><rect x={5} y={2} width={14} height={20} rx={2} /><line x1={12} y1={18} x2={12.01} y2={18} /></svg>,
  call: <svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}><path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6A19.79 19.79 0 012.12 4.18 2 2 0 014.11 2h3a2 2 0 012 1.72c.127.96.361 1.903.7 2.81a2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0122 16.92z" /></svg>,
  spark: <svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" /></svg>,
  gear: <svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}><circle cx={12} cy={12} r={3} /><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" /></svg>,
  plus: <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}><line x1={12} y1={5} x2={12} y2={19} /><line x1={5} y1={12} x2={19} y2={12} /></svg>,
  search: <svg width={15} height={15} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}><circle cx={11} cy={11} r={8} /><path d="M21 21l-4.35-4.35" /></svg>,
  send: <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}><path d="M22 2L11 13" /><path d="M22 2l-7 20-4-9-9-4 20-7z" /></svg>,
  check: <svg width={13} height={13} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={3}><polyline points="20 6 9 17 4 12" /></svg>,
  x: <svg width={13} height={13} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}><line x1={18} y1={6} x2={6} y2={18} /><line x1={6} y1={6} x2={18} y2={18} /></svg>,
  up: <svg width={12} height={12} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}><polyline points="18 15 12 9 6 15" /></svg>,
  down: <svg width={12} height={12} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}><polyline points="6 9 12 15 18 9" /></svg>,
  refresh: <svg width={15} height={15} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}><polyline points="23 4 23 10 17 10" /><path d="M20.49 15a9 9 0 11-2.12-9.36L23 10" /></svg>,
  trophy: <svg width={15} height={15} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}><path d="M6 9H4.5a2.5 2.5 0 010-5H6M18 9h1.5a2.5 2.5 0 000-5H18M4 22h16M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 19.24 7 20h10c0-.76-.85-1.25-2.03-1.79C14.47 17.98 14 17.55 14 17v-2.34" /><path d="M18 2H6v7a6 6 0 1012 0V2z" /></svg>,
  brain: <svg width={15} height={15} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}><path d="M9.5 2A5.5 5.5 0 004 7.5c0 1.58.67 3 1.73 4.01L12 18l6.27-6.49A5.48 5.48 0 0020 7.5 5.5 5.5 0 0014.5 2c-1.52 0-2.87.62-3.86 1.61" /></svg>,
  zap: <svg width={15} height={15} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" /></svg>,
  bar: <svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}><path d="M12 20V10M18 20V4M6 20v-4" /></svg>,
  fileText: <svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" /><polyline points="14 2 14 8 20 8" /><line x1={16} y1={13} x2={8} y2={13} /><line x1={16} y1={17} x2={8} y2={17} /><polyline points="10 9 9 9 8 9" /></svg>,
};

export { I };

export function Badge({ children, color = "var(--cyan)", bg = "var(--cyan-dim)", style = {} }: { children: ReactNode; color?: string; bg?: string; style?: React.CSSProperties }) {
  return <span style={{ display: "inline-flex", alignItems: "center", gap: 4, padding: "4px 11px", borderRadius: 20, fontSize: 11, fontWeight: 600, color, background: bg, letterSpacing: "0.04em", whiteSpace: "nowrap", ...style }}>{children}</span>;
}

export function PriorityBadge({ p }: { p: string }) {
  const m: Record<string, [string, string]> = { Hot: ["var(--hot)", "rgba(255,71,87,0.12)"], Warm: ["var(--warm)", "rgba(255,165,2,0.12)"], Cold: ["var(--cold)", "rgba(59,130,246,0.12)"], Dead: ["var(--dead)", "rgba(90,98,120,0.12)"] };
  const [c, b] = m[p] ?? m.Cold;
  return <Badge color={c} bg={b}>{p}</Badge>;
}

export function GlassCard({ children, style = {}, className = "", glow = false, onClick }: { children: ReactNode; style?: React.CSSProperties; className?: string; glow?: boolean; onClick?: () => void }) {
  return <div className={`glass-card ${glow ? "glow-border" : ""} ${className}`} onClick={onClick} style={{ padding: 24, position: "relative", cursor: onClick ? "pointer" : "default", ...style }}>{children}</div>;
}

export function Btn({ children, primary, glass, sm, icon, disabled, onClick, style = {}, className = "" }: { children: ReactNode; primary?: boolean; glass?: boolean; sm?: boolean; icon?: ReactNode; disabled?: boolean; onClick?: () => void; style?: React.CSSProperties; className?: string }) {
  return (
    <button
      className={primary ? "btn-primary" : glass ? "btn-glass" : ""}
      disabled={disabled}
      onClick={onClick}
      style={{
        display: "inline-flex", alignItems: "center", gap: 7,
        padding: sm ? "7px 14px" : "11px 20px",
        fontSize: sm ? 12 : 13, fontWeight: 600, borderRadius: sm ? "var(--radius-xs)" : "var(--radius-sm)",
        opacity: disabled ? 0.4 : 1, cursor: disabled ? "not-allowed" : "pointer",
        letterSpacing: "0.02em", ...style,
      }}
    >
      {icon}{children}
    </button>
  );
}

export function Input({ style = {}, className = "", ...props }: React.InputHTMLAttributes<HTMLInputElement> & { style?: React.CSSProperties; className?: string }) {
  return <input className={`input-field ${className}`} {...props} style={{ width: "100%", padding: "11px 15px", borderRadius: "var(--radius-sm)", fontSize: 13, ...style }} />;
}

export function TextArea({ style = {}, ...props }: React.TextareaHTMLAttributes<HTMLTextAreaElement> & { style?: React.CSSProperties }) {
  return <textarea className="input-field" {...props} style={{ width: "100%", padding: "11px 15px", borderRadius: "var(--radius-sm)", fontSize: 13, resize: "vertical", minHeight: 90, ...style }} />;
}

export function Modal({ open, onClose, title, children, wide }: { open: boolean; onClose: () => void; title: string; children: ReactNode; wide?: boolean }) {
  if (!open) return null;
  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center", background: "rgba(0,0,0,0.65)", backdropFilter: "blur(8px)" }} onClick={onClose}>
      <div className="glass-card glow-border" style={{ width: "92%", maxWidth: wide ? 760 : 540, maxHeight: "88vh", overflow: "auto", padding: 32, animation: "scaleIn 0.35s ease" }} onClick={(e) => e.stopPropagation()}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
          <h3 style={{ fontSize: 18, fontWeight: 700, letterSpacing: "-0.02em" }}>{title}</h3>
          <button onClick={onClose} style={{ background: "none", border: "none", color: "var(--text-secondary)", cursor: "pointer", padding: 6, borderRadius: 8 }}>{I.x}</button>
        </div>
        {children}
      </div>
    </div>
  );
}

export function AnimatedNumber({ value, suffix = "" }: { value: number | string; suffix?: string }) {
  const [display, setDisplay] = useState(0);
  useEffect(() => {
    const target = parseFloat(String(value)) || 0;
    const duration = 800;
    const start = performance.now();
    const anim = (now: number) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(eased * target);
      if (progress < 1) requestAnimationFrame(anim);
    };
    requestAnimationFrame(anim);
  }, [value]);
  return <span>{Number.isInteger(parseFloat(String(value))) ? Math.round(display) : display.toFixed(1)}{suffix}</span>;
}

export function MetricCard({ label, value, suffix = "", change, icon, color = "var(--cyan)", delay = 0 }: { label: string; value: number | string; suffix?: string; change?: number; icon: ReactNode; color?: string; delay?: number }) {
  return (
    <GlassCard style={{ flex: 1, minWidth: 170, animation: `fadeUp 0.6s ease ${delay}s both` }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <div style={{ fontSize: 11, color: "var(--text-dim)", marginBottom: 10, textTransform: "uppercase", letterSpacing: "0.1em", fontWeight: 500 }}>{label}</div>
          <div style={{ fontSize: 30, fontWeight: 800, color, letterSpacing: "-0.03em", lineHeight: 1 }}>
            <AnimatedNumber value={value} suffix={suffix} />
          </div>
          {change !== undefined && (
            <div style={{ fontSize: 11, color: change >= 0 ? "var(--green)" : "var(--red)", marginTop: 10, display: "flex", alignItems: "center", gap: 3, fontWeight: 500 }}>
              {change >= 0 ? I.up : I.down}
              {Math.abs(change).toFixed(1)}% vs last week
            </div>
          )}
        </div>
        <div style={{ color, opacity: 0.2, transform: "scale(1.4)" }}>{icon}</div>
      </div>
    </GlassCard>
  );
}

export function GlowBar({ value, max = 100, color = "var(--cyan)", height = 5, delay = 0 }: { value: number; max?: number; color?: string; height?: number; delay?: number }) {
  return (
    <div style={{ width: "100%", height, background: "rgba(255,255,255,0.04)", borderRadius: height, overflow: "hidden" }}>
      <div style={{ width: `${Math.min((value / max) * 100, 100)}%`, height: "100%", borderRadius: height, background: `linear-gradient(90deg, ${color}, ${color}88)`, boxShadow: `0 0 12px ${color}40`, animation: `barGrow 0.8s ease ${delay}s both` }} />
    </div>
  );
}

export function Toast({ msg, type = "success", onClose }: { msg: string; type?: "success" | "error" | "info"; onClose: () => void }) {
  useEffect(() => {
    const t = setTimeout(onClose, 3500);
    return () => clearTimeout(t);
  }, [onClose]);
  const c: Record<string, string> = { success: "var(--green)", error: "var(--red)", info: "var(--cyan)" };
  return (
    <div style={{ position: "fixed", bottom: 28, right: 28, zIndex: 2000, animation: "fadeUp 0.4s ease" }}>
      <GlassCard style={{ padding: "14px 22px", display: "flex", alignItems: "center", gap: 10, borderColor: `${c[type]}40` }}>
        <div style={{ width: 8, height: 8, borderRadius: "50%", background: c[type], boxShadow: `0 0 12px ${c[type]}` }} />
        <span style={{ fontSize: 13, fontWeight: 500 }}>{msg}</span>
      </GlassCard>
    </div>
  );
}
