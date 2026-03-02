"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Building2, ArrowRight, Sparkles, Zap, Brain } from "lucide-react";
import { LiquidEffectAnimation } from "@/components/ui/liquid-effect-animation";

export default function Home() {
  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden">
      <LiquidEffectAnimation />
      <div className="absolute inset-0 bg-black/60" />

      <div className="relative z-10 mx-auto max-w-3xl px-6 text-center">
        <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-1.5 text-sm text-white/80 backdrop-blur-sm">
          <Sparkles className="h-4 w-4" />
          AI-Powered Real Estate Outreach
        </div>

        <h1 className="mb-4 text-5xl font-bold tracking-tight text-white md:text-7xl">
          Close More Deals,{" "}
          <span className="bg-gradient-to-r from-blue-400 to-violet-400 bg-clip-text text-transparent">
            Automatically
          </span>
        </h1>

        <p className="mb-8 text-lg text-white/70 md:text-xl">
          AI lead scoring, smart email campaigns with A/B testing, SMS, voice
          calls, and an intelligent chatbot — all in one platform.
        </p>

        <div className="mb-12 flex flex-col items-center justify-center gap-4 sm:flex-row">
          <Link href="/dashboard">
            <Button size="lg" className="gap-2 text-base">
              <Building2 className="h-5 w-5" />
              Enter Dashboard
              <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {[
            {
              icon: Brain,
              title: "AI Lead Scoring",
              desc: "Score & prioritize leads with GPT",
            },
            {
              icon: Zap,
              title: "A/B Testing",
              desc: "5 AI variations per campaign",
            },
            {
              icon: Sparkles,
              title: "Multi-Channel",
              desc: "Email, SMS, Voice & Chat",
            },
          ].map((feat) => (
            <div
              key={feat.title}
              className="rounded-xl border border-white/10 bg-white/5 p-4 text-left backdrop-blur-sm"
            >
              <feat.icon className="mb-2 h-6 w-6 text-blue-400" />
              <h3 className="text-sm font-semibold text-white">
                {feat.title}
              </h3>
              <p className="text-xs text-white/60">{feat.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
