"use client";

import { useEffect, useRef, useState } from "react";

export function LiquidEffectAnimation() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    if (!canvasRef.current || failed) return;

    const script = document.createElement("script");
    script.type = "module";
    script.textContent = `
      (async function() {
        try {
          const mod = await import('https://cdn.jsdelivr.net/npm/threejs-components@0.0.22/build/backgrounds/liquid1.min.js');
          const LiquidBackground = mod.default || mod;
          const canvas = document.getElementById('liquid-canvas');
          if (!canvas) return;
          const app = LiquidBackground(canvas);
          if (app && app.loadImage) app.loadImage('https://i.pinimg.com/1200x/38/71/c9/3871c9c7a6066df6763c97dc3285c907.jpg');
          if (app && app.liquidPlane && app.liquidPlane.material) {
            app.liquidPlane.material.metalness = 0.75;
            app.liquidPlane.material.roughness = 0.25;
          }
          if (app && app.liquidPlane && app.liquidPlane.uniforms && app.liquidPlane.uniforms.displacementScale)
            app.liquidPlane.uniforms.displacementScale.value = 5;
          if (app && typeof app.setRain === 'function') app.setRain(false);
          if (typeof window !== 'undefined') window.__liquidApp = app;
        } catch (e) {
          console.warn('Liquid effect failed to load:', e);
          window.dispatchEvent(new Event('liquid-effect-failed'));
        }
      })();
    `;
    const onFail = () => setFailed(true);
    window.addEventListener("liquid-effect-failed", onFail);
    script.onerror = onFail;
    document.head.appendChild(script);

    return () => {
      window.removeEventListener("liquid-effect-failed", onFail);
      try {
        if (script.parentNode) document.head.removeChild(script);
      } catch (_) {}
    };
  }, [failed]);

  return (
    <canvas
      ref={canvasRef}
      id="liquid-canvas"
      className="absolute inset-0 h-full w-full"
      style={failed ? { background: "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)" } : undefined}
    />
  );
}
