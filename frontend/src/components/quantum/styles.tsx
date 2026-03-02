"use client";

export function QuantumStyles() {
  return (
    <style>{`
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&family=Source+Code+Pro:wght@400;500;600&display=swap');
    :root {
      --bg: #06080D;
      --bg-glass: rgba(14, 19, 30, 0.55);
      --border: rgba(255,255,255,0.06);
      --border-hover: rgba(255,255,255,0.12);
      --border-accent: rgba(0,234,255,0.2);
      --text: #E4E8F1;
      --text-secondary: #8892A8;
      --text-dim: #4A5268;
      --cyan: #00EAFF;
      --cyan-dim: rgba(0,234,255,0.15);
      --purple: #7B61FF;
      --green: #00E68A;
      --red: #FF5A65;
      --amber: #FFB800;
      --hot: #FF4757;
      --warm: #FFA502;
      --cold: #3B82F6;
      --dead: #5A6278;
      --font: 'Outfit', system-ui, sans-serif;
      --mono: 'Source Code Pro', monospace;
      --radius: 16px;
      --radius-sm: 10px;
      --radius-xs: 6px;
    }
    .quantum-dashboard * { margin:0; padding:0; box-sizing:border-box; }
    .quantum-dashboard { font-family: var(--font); background: var(--bg); color: var(--text); min-height: 100vh; overflow-x: hidden; }
    .quantum-dashboard input, .quantum-dashboard textarea, .quantum-dashboard select, .quantum-dashboard button { font-family: var(--font); }
    @keyframes meshFloat1 { 0%,100%{transform:translate(0,0) scale(1)} 33%{transform:translate(30px,-40px) scale(1.05)} 66%{transform:translate(-20px,20px) scale(0.95)} }
    @keyframes meshFloat2 { 0%,100%{transform:translate(0,0) scale(1)} 33%{transform:translate(-40px,30px) scale(1.08)} 66%{transform:translate(30px,-20px) scale(0.92)} }
    @keyframes meshFloat3 { 0%,100%{transform:translate(0,0) rotate(0deg)} 50%{transform:translate(40px,-30px) rotate(5deg)} }
    @keyframes fadeUp { from{opacity:0;transform:translateY(24px)} to{opacity:1;transform:translateY(0)} }
    @keyframes slideRight { from{opacity:0;transform:translateX(-20px)} to{opacity:1;transform:translateX(0)} }
    @keyframes scaleIn { from{opacity:0;transform:scale(0.92)} to{opacity:1;transform:scale(1)} }
    @keyframes glow { 0%,100%{box-shadow:0 0 20px rgba(0,234,255,0.1)} 50%{box-shadow:0 0 40px rgba(0,234,255,0.2)} }
    @keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.6;transform:scale(1.05)} }
    @keyframes borderGlow { 0%,100%{border-color:rgba(0,234,255,0.1)} 50%{border-color:rgba(0,234,255,0.3)} }
    @keyframes float { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-6px)} }
    @keyframes typewriter { 0%{opacity:0.2} 33%{opacity:1} 66%{opacity:0.2} }
    @keyframes ringPulse { 0%{box-shadow:0 0 0 0 rgba(0,234,255,0.4)} 70%{box-shadow:0 0 0 12px rgba(0,234,255,0)} 100%{box-shadow:0 0 0 0 rgba(0,234,255,0)} }
    @keyframes barGrow { from{width:0%} }
    .quantum-dashboard .glass-card { background: var(--bg-glass); backdrop-filter: blur(20px); border: 1px solid var(--border); border-radius: var(--radius); transition: all 0.35s ease; }
    .quantum-dashboard .glass-card:hover { border-color: var(--border-hover); box-shadow: 0 8px 40px rgba(0,0,0,0.3); }
    .quantum-dashboard .glow-border::before { content:''; position: absolute; inset: -1px; border-radius: inherit; padding: 1px; background: linear-gradient(135deg, rgba(0,234,255,0.2), transparent 40%, transparent 60%, rgba(123,97,255,0.15)); -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0); mask-composite: exclude; pointer-events: none; }
    .quantum-dashboard .btn-primary { background: linear-gradient(135deg, var(--cyan), #00B8D4); color: #000; font-weight: 600; border: none; cursor: pointer; transition: all 0.3s ease; }
    .quantum-dashboard .btn-primary:hover { transform: translateY(-1px); box-shadow: 0 4px 20px rgba(0,234,255,0.35); }
    .quantum-dashboard .btn-glass { background: rgba(255,255,255,0.04); color: var(--text); border: 1px solid var(--border); cursor: pointer; transition: all 0.25s ease; backdrop-filter: blur(8px); }
    .quantum-dashboard .btn-glass:hover { background: rgba(255,255,255,0.08); border-color: var(--border-hover); transform: translateY(-1px); }
    .quantum-dashboard .input-field { background: rgba(16,22,36,0.8); border: 1px solid var(--border); color: var(--text); outline: none; transition: all 0.3s ease; }
    .quantum-dashboard .input-field:focus { border-color: var(--cyan); box-shadow: 0 0 0 3px rgba(0,234,255,0.08); }
    .quantum-dashboard .stagger-1 { animation: fadeUp 0.6s ease 0.05s both; }
    .quantum-dashboard .stagger-2 { animation: fadeUp 0.6s ease 0.1s both; }
    .quantum-dashboard .stagger-3 { animation: fadeUp 0.6s ease 0.15s both; }
    .quantum-dashboard .stagger-4 { animation: fadeUp 0.6s ease 0.2s both; }
    .quantum-dashboard .stagger-5 { animation: fadeUp 0.6s ease 0.25s both; }
    .quantum-dashboard .stagger-6 { animation: fadeUp 0.6s ease 0.3s both; }
  `}</style>
  );
}
