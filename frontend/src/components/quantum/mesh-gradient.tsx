"use client";

export function MeshGradient() {
  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 0,
        overflow: "hidden",
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          position: "absolute",
          width: 800,
          height: 800,
          top: "-20%",
          right: "-10%",
          background: "radial-gradient(circle, rgba(0,234,255,0.07) 0%, transparent 70%)",
          filter: "blur(80px)",
          animation: "meshFloat1 20s ease-in-out infinite",
        }}
      />
      <div
        style={{
          position: "absolute",
          width: 600,
          height: 600,
          bottom: "-10%",
          left: "-5%",
          background: "radial-gradient(circle, rgba(123,97,255,0.06) 0%, transparent 70%)",
          filter: "blur(80px)",
          animation: "meshFloat2 25s ease-in-out infinite",
        }}
      />
      <div
        style={{
          position: "absolute",
          width: 400,
          height: 400,
          top: "40%",
          left: "30%",
          background: "radial-gradient(circle, rgba(0,234,255,0.04) 0%, transparent 70%)",
          filter: "blur(60px)",
          animation: "meshFloat3 18s ease-in-out infinite",
        }}
      />
    </div>
  );
}
