"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Tooltip, TooltipContent, TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  ArrowLeft, Brain, Mail, MessageSquare, Phone, Mic, Send, Calendar,
  User, Building, MapPin, DollarSign, Clock, Loader2, Info,
} from "lucide-react";
import {
  getLead, scoreLead, getEmailHistory,
  getSMSHistory, sendSMS, getVoiceHistory, startVoiceCall, getVoiceCall,
  getChatHistory, sendChatMessage, getConfig,
} from "@/lib/api";
import type {
  Lead, EmailSequence, SmsMessage, VoiceCall, ChatMessage, ChatbotResponse, AppConfig,
} from "@/lib/types";
import { toast } from "sonner";
import { format } from "date-fns";

const STATUS_COLORS: Record<string, string> = {
  uploaded: "bg-gray-500/20 text-gray-400",
  contacted: "bg-blue-500/20 text-blue-400",
  replied: "bg-yellow-500/20 text-yellow-400",
  interested: "bg-orange-500/20 text-orange-400",
  booked: "bg-green-500/20 text-green-400",
  closed: "bg-emerald-500/20 text-emerald-400",
};

const PRIORITY_COLORS: Record<string, string> = {
  Hot: "border-red-500/50 bg-red-500/10 text-red-400",
  Warm: "border-orange-500/50 bg-orange-500/10 text-orange-400",
  Cold: "border-blue-500/50 bg-blue-500/10 text-blue-400",
  Dead: "border-gray-500/50 bg-gray-500/10 text-gray-400",
};

const VOICE_STATUS_COLORS: Record<string, string> = {
  pending: "bg-gray-500/20 text-gray-400",
  calling: "bg-yellow-500/20 text-yellow-400",
  in_progress: "bg-blue-500/20 text-blue-400",
  completed: "bg-green-500/20 text-green-400",
  failed: "bg-red-500/20 text-red-400",
  no_answer: "bg-orange-500/20 text-orange-400",
  busy: "bg-orange-500/20 text-orange-400",
  voicemail: "bg-purple-500/20 text-purple-400",
};

const VOICE_OUTCOME_COLORS: Record<string, string> = {
  booked: "bg-green-500/20 text-green-400",
  interested: "bg-blue-500/20 text-blue-400",
  not_interested: "bg-red-500/20 text-red-400",
  callback: "bg-yellow-500/20 text-yellow-400",
  voicemail: "bg-purple-500/20 text-purple-400",
  no_outcome: "bg-gray-500/20 text-gray-400",
};

const SMS_STATUS_COLORS: Record<string, string> = {
  pending: "bg-gray-500/20 text-gray-400",
  sent: "bg-green-500/20 text-green-400",
  delivered: "bg-green-500/20 text-green-400",
  failed: "bg-red-500/20 text-red-400",
  undelivered: "bg-red-500/20 text-red-400",
  mock: "bg-yellow-500/20 text-yellow-400",
};

const ALL_SMS_PLACEHOLDERS = [
  "{{first_name}}", "{{last_name}}", "{{email}}", "{{phone}}",
  "{{address}}", "{{property_type}}", "{{estimated_value}}",
];

export default function LeadDetailPage() {
  const params = useParams();
  const router = useRouter();
  const leadId = Number(params.id);

  const [lead, setLead] = useState<Lead | null>(null);
  const [loading, setLoading] = useState(true);
  const [scoring, setScoring] = useState(false);
  const [config, setConfig] = useState<AppConfig | null>(null);

  const [emails, setEmails] = useState<EmailSequence[]>([]);
  const [smsMessages, setSmsMessages] = useState<SmsMessage[]>([]);
  const [voiceCalls, setVoiceCalls] = useState<VoiceCall[]>([]);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [chatAction, setChatAction] = useState<string | null>(null);

  const [showSmsDialog, setShowSmsDialog] = useState(false);
  const [smsBody, setSmsBody] = useState("");
  const [smsSending, setSmsSending] = useState(false);

  const [showVoiceDialog, setShowVoiceDialog] = useState(false);
  const [dynamicVars, setDynamicVars] = useState<Record<string, string>>({});
  const [callingInProgress, setCallingInProgress] = useState(false);
  const [activeCallId, setActiveCallId] = useState<number | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchLead = useCallback(async () => {
    try {
      const res = await getLead(leadId);
      setLead(res.data);
    } catch {
      toast.error("Failed to load lead");
    } finally {
      setLoading(false);
    }
  }, [leadId]);

  useEffect(() => {
    fetchLead();
    getConfig().then((r) => setConfig(r.data)).catch(() => {});
  }, [fetchLead]);

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const handleTabChange = async (tab: string) => {
    try {
      if (tab === "emails") {
        const res = await getEmailHistory(leadId);
        setEmails(res.data.items ?? res.data ?? []);
      } else if (tab === "sms") {
        const res = await getSMSHistory(leadId);
        setSmsMessages(res.data.messages ?? []);
      } else if (tab === "voice") {
        const res = await getVoiceHistory(leadId);
        setVoiceCalls(res.data.calls ?? []);
      } else if (tab === "chat") {
        const res = await getChatHistory(leadId);
        setChatMessages(res.data.messages ?? []);
      }
    } catch { /* silently handle */ }
  };

  const handleScore = async () => {
    setScoring(true);
    try {
      const res = await scoreLead(leadId);
      toast.success(`Score: ${res.data.result.score} — ${res.data.result.priority}`);
      fetchLead();
    } catch {
      toast.error("Scoring failed");
    } finally {
      setScoring(false);
    }
  };

  const handleSendSms = async () => {
    if (!smsBody.trim()) return;
    setSmsSending(true);
    try {
      const res = await sendSMS(leadId, smsBody);
      const toNum = lead?.phone ? ` to ${lead.phone}` : "";
      if (res.data.status === "mock") {
        toast.success(`SMS sent${toNum} (Demo Mode)`);
      } else {
        toast.success(`SMS sent${toNum}`);
      }
      setSmsBody("");
      setShowSmsDialog(false);
      const hist = await getSMSHistory(leadId);
      setSmsMessages(hist.data.messages ?? []);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "SMS failed";
      toast.error(msg);
    } finally {
      setSmsSending(false);
    }
  };

  const handleStartVoiceCall = async () => {
    const vars = Object.fromEntries(
      Object.entries(dynamicVars).filter(([, v]) => v.trim())
    );
    setCallingInProgress(true);
    setShowVoiceDialog(false);
    try {
      const res = await startVoiceCall(leadId, Object.keys(vars).length > 0 ? vars : null);
      toast.success(res.data.message);
      const callId = res.data.voice_call_id;
      if (callId) {
        setActiveCallId(callId);
        pollRef.current = setInterval(async () => {
          try {
            const pollRes = await getVoiceCall(callId);
            const status = pollRes.data.status;
            if (["completed", "failed", "no_answer", "busy", "voicemail"].includes(status)) {
              if (pollRef.current) clearInterval(pollRef.current);
              pollRef.current = null;
              setCallingInProgress(false);
              setActiveCallId(null);
              toast.info(`Call ${status === "completed" ? "completed" : status}`);
              const hist = await getVoiceHistory(leadId);
              setVoiceCalls(hist.data.calls ?? []);
            }
          } catch { /* keep polling */ }
        }, 12000);
      } else {
        setCallingInProgress(false);
      }
      const hist = await getVoiceHistory(leadId);
      setVoiceCalls(hist.data.calls ?? []);
    } catch {
      toast.error("Failed to start call");
      setCallingInProgress(false);
    }
  };

  const handleChatSend = async () => {
    if (!chatInput.trim() || chatAction === "end") return;
    const userMsg: ChatMessage = { role: "user", content: chatInput };
    const updated = [...chatMessages, userMsg];
    setChatMessages(updated);
    setChatInput("");
    setChatLoading(true);
    try {
      const res = await sendChatMessage(leadId, updated, {
        lead_score: lead?.ai_score?.score,
        industry: "real_estate",
        source: "manual",
        last_email_summary: emails.length > 0
          ? `${emails[emails.length - 1]?.email_subject ?? "Email"} sent to lead`
          : undefined,
      });
      const data: ChatbotResponse = res.data;
      setChatMessages([...updated, { role: "assistant", content: data.reply }]);
      setChatAction(data.next_action.type);
      if (data.updated_lead_score != null && lead?.ai_score) {
        setLead((prev) =>
          prev
            ? {
                ...prev,
                ai_score: prev.ai_score
                  ? { ...prev.ai_score, score: data.updated_lead_score! }
                  : prev.ai_score,
              }
            : prev
        );
      }
    } catch {
      toast.error("Chat failed");
    } finally {
      setChatLoading(false);
    }
  };

  if (loading) {
    return (
      <>
        <Header title="Lead Details" />
        <div className="flex h-96 items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        </div>
      </>
    );
  }

  if (!lead) {
    return (
      <>
        <Header title="Lead Not Found" />
        <div className="flex h-96 flex-col items-center justify-center gap-4">
          <p className="text-muted-foreground">Lead not found.</p>
          <Button onClick={() => router.push("/leads")}>Back to Leads</Button>
        </div>
      </>
    );
  }

  const isAiPowered = config?.services.openai ?? false;
  const isTwilioLive = config?.services.twilio_sms ?? false;
  const isVoiceLive = config?.services.retell_voice ?? false;

  return (
    <>
      <Header title={`${lead.first_name} ${lead.last_name || ""}`} />
      <div className="space-y-6 p-6">
        <Button variant="ghost" size="sm" className="gap-1" onClick={() => router.push("/leads")}>
          <ArrowLeft className="h-4 w-4" /> Back to Leads
        </Button>

        <div className="grid gap-6 lg:grid-cols-3">
          {/* Lead Info Card */}
          <Card className="lg:col-span-1">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">Lead Info</CardTitle>
                <Badge variant="secondary" className={STATUS_COLORS[lead.status] ?? ""}>
                  {lead.status}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <InfoRow icon={<User className="h-4 w-4" />} label="Name" value={`${lead.first_name} ${lead.last_name || ""}`} />
              <InfoRow icon={<Mail className="h-4 w-4" />} label="Email" value={lead.email} />
              <InfoRow icon={<Phone className="h-4 w-4" />} label="Phone" value={lead.phone || "—"} />
              <InfoRow icon={<Building className="h-4 w-4" />} label="Company" value={lead.company || "—"} />
              <InfoRow icon={<MapPin className="h-4 w-4" />} label="Address" value={lead.address || "—"} />
              <InfoRow icon={<DollarSign className="h-4 w-4" />} label="Est. Value" value={lead.estimated_value || "—"} />
              {lead.property_type && (
                <InfoRow icon={<Building className="h-4 w-4" />} label="Type" value={lead.property_type} />
              )}
              <InfoRow icon={<Clock className="h-4 w-4" />} label="Added" value={format(new Date(lead.created_at), "MMM d, yyyy")} />
            </CardContent>
          </Card>

          {/* AI Score Card */}
          <Card className="lg:col-span-1">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2 text-base">
                  <Brain className="h-4 w-4" /> AI Score
                  <Badge variant="secondary" className="text-[9px]">
                    {isAiPowered ? "AI-Powered" : "Demo Mode"}
                  </Badge>
                </CardTitle>
                <Button variant="outline" size="sm" onClick={handleScore} disabled={scoring}>
                  {scoring ? "Scoring..." : "Re-score"}
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {lead.ai_score ? (
                <div className="space-y-4">
                  <div className="flex items-center gap-4">
                    <div className={`flex h-16 w-16 items-center justify-center rounded-xl border-2 text-2xl font-bold ${PRIORITY_COLORS[lead.ai_score.priority]}`}>
                      {lead.ai_score.score}
                    </div>
                    <div>
                      <Badge className={PRIORITY_COLORS[lead.ai_score.priority]}>
                        {lead.ai_score.priority}
                      </Badge>
                      {lead.ai_score.recommended_campaign && (
                        <Badge variant="outline" className="ml-1 text-[10px]">
                          {lead.ai_score.recommended_campaign}
                        </Badge>
                      )}
                    </div>
                  </div>
                  {lead.ai_score.reasoning && (
                    <p className="text-sm text-muted-foreground">{lead.ai_score.reasoning}</p>
                  )}
                  {lead.ai_score.personalization_hints && (
                    <div className="rounded-lg border border-border bg-muted/50 p-3">
                      <div className="flex items-center gap-1">
                        <Info className="h-3 w-3 text-primary" />
                        <p className="text-xs font-medium">Personalization Hints</p>
                      </div>
                      <p className="mt-1 text-xs text-muted-foreground">{lead.ai_score.personalization_hints}</p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex flex-col items-center gap-3 py-8 text-center">
                  <Brain className="h-10 w-10 text-muted-foreground" />
                  <p className="text-sm text-muted-foreground">Not scored yet</p>
                  <Button size="sm" onClick={handleScore} disabled={scoring}>
                    Score with AI
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle className="text-base">Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button variant="outline" className="w-full justify-start gap-2" onClick={() => setShowSmsDialog(true)} disabled={!lead.phone}>
                <MessageSquare className="h-4 w-4" /> Send SMS
                {!isTwilioLive && <Badge variant="secondary" className="ml-auto text-[9px]">Demo</Badge>}
              </Button>
              <Button
                variant="outline"
                className="w-full justify-start gap-2"
                onClick={() => setShowVoiceDialog(true)}
                disabled={!lead.phone || callingInProgress}
              >
                {callingInProgress ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span className="animate-pulse">Call in progress...</span>
                  </>
                ) : (
                  <>
                    <Mic className="h-4 w-4" /> Start AI Call
                    {!isVoiceLive && <Badge variant="secondary" className="ml-auto text-[9px]">Demo</Badge>}
                  </>
                )}
              </Button>
              {!lead.phone && (
                <p className="text-xs text-muted-foreground">Phone number required for SMS and Voice</p>
              )}
              {lead.ai_score?.personalization_hints && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <div className="mt-2 rounded-md border border-dashed border-primary/30 bg-primary/5 p-2 text-xs text-muted-foreground">
                      <span className="font-medium text-primary">Tip:</span> {lead.ai_score.personalization_hints.slice(0, 100)}...
                    </div>
                  </TooltipTrigger>
                  <TooltipContent className="max-w-xs">
                    <p className="text-xs">{lead.ai_score.personalization_hints}</p>
                  </TooltipContent>
                </Tooltip>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Call in progress indicator */}
        {callingInProgress && (
          <div className="flex items-center gap-3 rounded-lg border border-blue-500/20 bg-blue-500/5 p-4">
            <div className="relative">
              <Phone className="h-5 w-5 text-blue-400" />
              <span className="absolute -right-0.5 -top-0.5 h-2.5 w-2.5 animate-ping rounded-full bg-blue-400" />
              <span className="absolute -right-0.5 -top-0.5 h-2.5 w-2.5 rounded-full bg-blue-400" />
            </div>
            <div>
              <p className="text-sm font-medium">AI Call in Progress</p>
              <p className="text-xs text-muted-foreground">Polling every 12 seconds for updates...</p>
            </div>
          </div>
        )}

        {/* Tabs */}
        <Tabs defaultValue="emails" onValueChange={handleTabChange}>
          <TabsList>
            <TabsTrigger value="emails" className="gap-1"><Mail className="h-3.5 w-3.5" /> Emails</TabsTrigger>
            <TabsTrigger value="sms" className="gap-1"><MessageSquare className="h-3.5 w-3.5" /> SMS</TabsTrigger>
            <TabsTrigger value="voice" className="gap-1"><Mic className="h-3.5 w-3.5" /> Voice</TabsTrigger>
            <TabsTrigger value="chat" className="gap-1">
              <MessageSquare className="h-3.5 w-3.5" /> Chat
              <Badge variant="secondary" className="ml-1 text-[9px]">
                {isAiPowered ? "AI" : "Demo"}
              </Badge>
            </TabsTrigger>
          </TabsList>

          {/* Email Tab */}
          <TabsContent value="emails">
            <Card>
              <CardContent className="p-4">
                {emails.length === 0 ? (
                  <p className="py-8 text-center text-sm text-muted-foreground">No emails yet.</p>
                ) : (
                  <div className="space-y-3">
                    {emails.map((e) => (
                      <div key={e.id} className="rounded-lg border border-border p-3">
                        <div className="flex items-center justify-between">
                          <p className="text-sm font-medium">{e.email_subject || "No subject"}</p>
                          <Badge variant="secondary" className="text-[10px]">{e.status}</Badge>
                        </div>
                        <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">{e.email_body}</p>
                        <div className="mt-2 flex flex-wrap gap-3 text-[10px] text-muted-foreground">
                          {e.sent_at && <span>Sent: {format(new Date(e.sent_at), "MMM d, HH:mm")}</span>}
                          {e.opened_at && <span className="text-green-400">Opened: {format(new Date(e.opened_at), "MMM d, HH:mm")}</span>}
                          {e.clicked_at && <span className="text-yellow-400">Clicked: {format(new Date(e.clicked_at), "MMM d, HH:mm")}</span>}
                          {e.replied_at && <span className="text-blue-400">Replied: {format(new Date(e.replied_at), "MMM d, HH:mm")}</span>}
                          {e.bounce_reason && <span className="text-red-400">Bounced: {e.bounce_reason}</span>}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* SMS Tab */}
          <TabsContent value="sms">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm">SMS History</CardTitle>
                <Button size="sm" onClick={() => setShowSmsDialog(true)} disabled={!lead.phone}>
                  <Send className="mr-1 h-3 w-3" /> Send SMS
                </Button>
              </CardHeader>
              <CardContent>
                {smsMessages.length === 0 ? (
                  <p className="py-8 text-center text-sm text-muted-foreground">No SMS sent yet.</p>
                ) : (
                  <div className="space-y-3">
                    {smsMessages.map((m) => (
                      <div key={m.id} className="rounded-lg border border-border p-3">
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-muted-foreground">To: {m.to_number}</span>
                          <Badge variant="secondary" className={`text-[10px] ${SMS_STATUS_COLORS[m.status] ?? ""}`}>
                            {m.status}
                          </Badge>
                        </div>
                        <p className="mt-1 text-sm">{m.body}</p>
                        {m.sent_at && (
                          <p className="mt-1 text-[10px] text-muted-foreground">
                            {format(new Date(m.sent_at), "MMM d, yyyy HH:mm")}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Voice Tab */}
          <TabsContent value="voice">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm">Voice Calls</CardTitle>
                <Button size="sm" onClick={() => setShowVoiceDialog(true)} disabled={!lead.phone || callingInProgress}>
                  {callingInProgress ? (
                    <><Loader2 className="mr-1 h-3 w-3 animate-spin" /> Calling...</>
                  ) : (
                    <><Phone className="mr-1 h-3 w-3" /> Start AI Call</>
                  )}
                </Button>
              </CardHeader>
              <CardContent>
                {voiceCalls.length === 0 ? (
                  <p className="py-8 text-center text-sm text-muted-foreground">No voice calls yet.</p>
                ) : (
                  <div className="space-y-3">
                    {voiceCalls.map((c) => (
                      <div key={c.id} className="rounded-lg border border-border p-3">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Badge variant="secondary" className={`text-[10px] ${VOICE_STATUS_COLORS[c.status] ?? ""}`}>
                              {c.status}
                            </Badge>
                            {c.call_outcome && (
                              <Badge variant="outline" className={`text-[10px] ${VOICE_OUTCOME_COLORS[c.call_outcome] ?? ""}`}>
                                {c.call_outcome}
                              </Badge>
                            )}
                          </div>
                          {c.duration_seconds != null && (
                            <span className="text-xs text-muted-foreground">
                              {Math.floor(c.duration_seconds / 60)}m {c.duration_seconds % 60}s
                            </span>
                          )}
                        </div>
                        {c.call_summary && (
                          <div className="mt-2 rounded-md bg-muted/50 p-2">
                            <p className="text-xs font-medium">AI Summary</p>
                            <p className="mt-0.5 text-sm">{c.call_summary}</p>
                          </div>
                        )}
                        {c.transcript && (
                          <details className="mt-2">
                            <summary className="cursor-pointer text-xs text-muted-foreground hover:text-foreground">
                              View Full Transcript
                            </summary>
                            <pre className="mt-1 whitespace-pre-wrap rounded bg-muted p-2 text-xs">{c.transcript}</pre>
                          </details>
                        )}
                        {c.recording_url && (
                          <div className="mt-2">
                            <p className="mb-1 text-xs text-muted-foreground">Recording</p>
                            <audio controls src={c.recording_url} className="w-full" />
                          </div>
                        )}
                        {c.created_at && (
                          <p className="mt-2 text-[10px] text-muted-foreground">
                            {format(new Date(c.created_at), "MMM d, yyyy HH:mm")}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Chat Tab */}
          <TabsContent value="chat">
            <Card className="flex h-[500px] flex-col">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">AI Chatbot</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-1 flex-col overflow-hidden p-4 pt-0">
                <ScrollArea className="flex-1 pr-4">
                  <div className="space-y-3 pb-4">
                    {chatMessages.length === 0 && (
                      <p className="py-12 text-center text-sm text-muted-foreground">
                        Start a conversation with the AI chatbot for this lead.
                      </p>
                    )}
                    {chatMessages.map((msg, i) => (
                      <div
                        key={i}
                        className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                      >
                        <div
                          className={`max-w-[80%] rounded-xl px-3 py-2 text-sm ${
                            msg.role === "user"
                              ? "bg-primary text-primary-foreground"
                              : "bg-muted"
                          }`}
                        >
                          {msg.content}
                        </div>
                      </div>
                    ))}
                    {chatLoading && (
                      <div className="flex justify-start">
                        <div className="flex items-center gap-2 rounded-xl bg-muted px-4 py-2 text-sm text-muted-foreground">
                          <Loader2 className="h-3 w-3 animate-spin" /> Typing...
                        </div>
                      </div>
                    )}
                    {chatAction === "book_meeting" && (
                      <div className="flex justify-center">
                        <Button size="sm" className="gap-1">
                          <Calendar className="h-3 w-3" /> Book a Demo
                        </Button>
                      </div>
                    )}
                    {chatAction === "escalate_human" && (
                      <div className="flex justify-center">
                        <Button variant="outline" size="sm" className="gap-1">
                          <User className="h-3 w-3" /> Connect with Human
                        </Button>
                      </div>
                    )}
                    {chatAction === "end" && (
                      <p className="text-center text-xs text-muted-foreground">Conversation ended</p>
                    )}
                  </div>
                </ScrollArea>
                <div className="flex gap-2 border-t border-border pt-3">
                  <Input
                    placeholder="Type a message..."
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleChatSend()}
                    disabled={chatAction === "end"}
                  />
                  <Button size="icon" onClick={handleChatSend} disabled={chatLoading || chatAction === "end"}>
                    <Send className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>

      {/* SMS Compose Dialog */}
      <Dialog open={showSmsDialog} onOpenChange={setShowSmsDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Send SMS to {lead.first_name}</DialogTitle>
            <DialogDescription>
              {!isTwilioLive && "Twilio not configured — SMS will be sent in demo mode."}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            {lead.ai_score?.personalization_hints && (
              <div className="rounded-md border border-dashed border-primary/30 bg-primary/5 p-2 text-xs text-muted-foreground">
                <span className="font-medium text-primary">AI Hint:</span> {lead.ai_score.personalization_hints}
              </div>
            )}
            <div className="flex flex-wrap gap-1">
              {ALL_SMS_PLACEHOLDERS.map((p) => (
                <Button
                  key={p}
                  variant="outline"
                  size="sm"
                  className="h-6 text-[10px]"
                  onClick={() => setSmsBody((prev) => prev + (prev.endsWith(" ") || prev === "" ? "" : " ") + p)}
                >
                  {p}
                </Button>
              ))}
            </div>
            <Textarea
              placeholder="Type your message..."
              value={smsBody}
              onChange={(e) => setSmsBody(e.target.value)}
              rows={4}
              maxLength={1600}
            />
            <p className="text-xs text-muted-foreground">{smsBody.length}/1600</p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSmsDialog(false)}>Cancel</Button>
            <Button onClick={handleSendSms} disabled={smsSending || !smsBody.trim()}>
              {smsSending ? "Sending..." : "Send SMS"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Voice Call Dialog */}
      <Dialog open={showVoiceDialog} onOpenChange={setShowVoiceDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Start AI Voice Call</DialogTitle>
            <DialogDescription>
              Call {lead.first_name} at {lead.phone}.{" "}
              {!isVoiceLive && "Retell AI not configured — call will be mocked."}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <p className="text-xs text-muted-foreground">
              The AI agent will automatically know the lead&apos;s name, company, address, and property type.
              Add any extra variables below (optional):
            </p>
            <div className="grid gap-2 sm:grid-cols-2">
              <div>
                <Label className="text-xs">Property Address</Label>
                <Input
                  placeholder="e.g. 123 Oak Street"
                  value={dynamicVars.property_address ?? ""}
                  onChange={(e) => setDynamicVars({ ...dynamicVars, property_address: e.target.value })}
                />
              </div>
              <div>
                <Label className="text-xs">Caller Name</Label>
                <Input
                  placeholder="e.g. Sarah from Outreach Team"
                  value={dynamicVars.caller_name ?? ""}
                  onChange={(e) => setDynamicVars({ ...dynamicVars, caller_name: e.target.value })}
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowVoiceDialog(false)}>Cancel</Button>
            <Button onClick={handleStartVoiceCall} className="gap-1">
              <Phone className="h-4 w-4" /> Start Call
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

function InfoRow({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="flex items-center gap-3">
      <span className="text-muted-foreground">{icon}</span>
      <div>
        <p className="text-[10px] uppercase text-muted-foreground">{label}</p>
        <p className="text-sm">{value}</p>
      </div>
    </div>
  );
}
