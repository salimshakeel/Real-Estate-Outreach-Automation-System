"use client";

import { useEffect, useState, useCallback } from "react";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import {
  AlertTriangle, Database, Play, RotateCcw, Mail, Phone, Mic,
  Brain, Calendar, Circle, Trash2, Sparkles, Zap,
} from "lucide-react";
import api, {
  getConfig, seedData, resetData, simulateOpen,
  simulateReply, simulateBooking, getLeads,
} from "@/lib/api";
import { Textarea } from "@/components/ui/textarea";
import type { AppConfig, Lead } from "@/lib/types";
import { toast } from "sonner";

export default function SettingsPage() {
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [selectedLead, setSelectedLead] = useState("");
  const [sentiment, setSentiment] = useState("interested");
  const [replyText, setReplyText] = useState("");
  const [daysFromNow, setDaysFromNow] = useState(3);
  const [seeding, setSeeding] = useState(false);
  const [resetting, setResetting] = useState(false);

  const fetchConfig = useCallback(async () => {
    try {
      const res = await getConfig();
      setConfig(res.data);
    } catch {
      toast.error("Failed to load config");
    }
  }, []);

  const fetchLeads = useCallback(async () => {
    try {
      const res = await getLeads(1, 100);
      setLeads(res.data.items ?? []);
    } catch { /* no leads yet */ }
  }, []);

  useEffect(() => {
    fetchConfig();
    fetchLeads();
  }, [fetchConfig, fetchLeads]);

  const handleSeed = async () => {
    setSeeding(true);
    try {
      const res = await seedData();
      toast.success(res.data.message);
      fetchLeads();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Seed failed";
      toast.error(msg);
    } finally {
      setSeeding(false);
    }
  };

  const handleReset = async () => {
    if (!confirm("This will DELETE ALL data. Are you sure?")) return;
    setResetting(true);
    try {
      const res = await resetData();
      toast.success(res.data.message);
      fetchLeads();
    } catch {
      toast.error("Reset failed");
    } finally {
      setResetting(false);
    }
  };

  const handleSimOpen = async () => {
    if (!selectedLead) { toast.error("Select a lead"); return; }
    try {
      const res = await simulateOpen(Number(selectedLead));
      toast.success(res.data.message);
    } catch {
      toast.error("Simulation failed");
    }
  };

  const handleSimReply = async () => {
    if (!selectedLead) { toast.error("Select a lead"); return; }
    try {
      const body: Record<string, unknown> = { lead_id: Number(selectedLead), sentiment };
      if (replyText.trim()) body.reply_text = replyText;
      const res = await api.post("/api/demo/simulate/reply", body);
      toast.success(res.data.message);
    } catch {
      toast.error("Simulation failed");
    }
  };

  const handleSimBooking = async () => {
    if (!selectedLead) { toast.error("Select a lead"); return; }
    try {
      const res = await simulateBooking(Number(selectedLead), daysFromNow);
      toast.success(res.data.message);
    } catch {
      toast.error("Simulation failed");
    }
  };

  const SERVICE_ICONS: Record<string, React.ReactNode> = {
    database: <Database className="h-4 w-4" />,
    sendgrid: <Mail className="h-4 w-4" />,
    twilio_sms: <Phone className="h-4 w-4" />,
    retell_voice: <Mic className="h-4 w-4" />,
    openai: <Brain className="h-4 w-4" />,
    calendly: <Calendar className="h-4 w-4" />,
  };

  return (
    <>
      <Header title="Settings" />
      <div className="space-y-6 p-6">
        {/* Service Status */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Zap className="h-4 w-4" /> Service Status
            </CardTitle>
            <CardDescription>
              Check which services are connected and active
            </CardDescription>
          </CardHeader>
          <CardContent>
            {config ? (
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {Object.entries(config.services).map(([key, active]) => (
                  <div
                    key={key}
                    className={`flex items-center gap-3 rounded-lg border p-3 ${
                      active ? "border-green-500/20 bg-green-500/5" : "border-border bg-muted/30"
                    }`}
                  >
                    <span className={active ? "text-green-400" : "text-muted-foreground"}>
                      {SERVICE_ICONS[key] ?? <Circle className="h-4 w-4" />}
                    </span>
                    <div className="flex-1">
                      <p className="text-sm font-medium capitalize">{key.replace(/_/g, " ")}</p>
                      <p className="text-[10px] text-muted-foreground">
                        {active ? "Connected & Active" : "Not configured (demo mode)"}
                      </p>
                    </div>
                    <Badge variant={active ? "default" : "secondary"} className="text-[10px]">
                      {active ? "Live" : "Demo"}
                    </Badge>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">Loading...</p>
            )}

            {config && (
              <div className="mt-4 rounded-lg border border-border bg-muted/30 p-3">
                <p className="text-xs text-muted-foreground">
                  <strong>App:</strong> {config.app_name} v{config.version} | <strong>Env:</strong> {config.environment}
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Demo Controls */}
        <Card className="border-yellow-500/20">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Sparkles className="h-4 w-4 text-yellow-400" /> Demo Controls
            </CardTitle>
            <CardDescription>
              Simulate events and manage demo data
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Seed & Reset */}
            <div className="flex flex-wrap gap-3">
              <Button variant="outline" className="gap-1" onClick={handleSeed} disabled={seeding}>
                <Database className="h-4 w-4" />
                {seeding ? "Seeding..." : "Seed Demo Data"}
              </Button>
              <Button variant="destructive" className="gap-1" onClick={handleReset} disabled={resetting}>
                <Trash2 className="h-4 w-4" />
                {resetting ? "Resetting..." : "Reset All Data"}
              </Button>
            </div>

            <Separator />

            {/* Simulate Events */}
            <div className="space-y-4">
              <h3 className="text-sm font-medium">Simulate Events</h3>

              <div className="flex flex-wrap items-end gap-3">
                <div className="min-w-[200px]">
                  <Label className="text-xs">Select Lead</Label>
                  <Select value={selectedLead} onValueChange={setSelectedLead}>
                    <SelectTrigger>
                      <SelectValue placeholder="Choose a lead..." />
                    </SelectTrigger>
                    <SelectContent>
                      {leads.map((l) => (
                        <SelectItem key={l.id} value={String(l.id)}>
                          {l.first_name} {l.last_name || ""} ({l.email})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="min-w-[140px]">
                  <Label className="text-xs">Reply Sentiment</Label>
                  <Select value={sentiment} onValueChange={setSentiment}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="interested">Interested</SelectItem>
                      <SelectItem value="not_now">Not Now</SelectItem>
                      <SelectItem value="unsubscribe">Unsubscribe</SelectItem>
                      <SelectItem value="other">Other</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="min-w-[80px]">
                  <Label className="text-xs">Days from Now</Label>
                  <Input
                    type="number"
                    min={1}
                    max={30}
                    value={daysFromNow}
                    onChange={(e) => setDaysFromNow(Number(e.target.value) || 3)}
                    className="w-20"
                  />
                </div>
              </div>

              <div>
                <Label className="text-xs">Custom Reply Text (optional)</Label>
                <Textarea
                  placeholder="e.g. Yes, I'd love to chat about selling my property."
                  value={replyText}
                  onChange={(e) => setReplyText(e.target.value)}
                  rows={2}
                  className="mt-1"
                />
              </div>

              <div className="flex flex-wrap gap-2">
                <Button variant="outline" size="sm" className="gap-1" onClick={handleSimOpen} disabled={!selectedLead}>
                  <Mail className="h-3 w-3" /> Simulate Open
                </Button>
                <Button variant="outline" size="sm" className="gap-1" onClick={handleSimReply} disabled={!selectedLead}>
                  <Play className="h-3 w-3" /> Simulate Reply
                </Button>
                <Button variant="outline" size="sm" className="gap-1" onClick={handleSimBooking} disabled={!selectedLead}>
                  <Calendar className="h-3 w-3" /> Simulate Booking
                </Button>
              </div>

              {!selectedLead && leads.length === 0 && (
                <p className="flex items-center gap-2 text-xs text-muted-foreground">
                  <AlertTriangle className="h-3 w-3" />
                  No leads found. Seed demo data first.
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </>
  );
}
