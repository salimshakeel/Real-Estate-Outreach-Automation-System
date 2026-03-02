"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from "@/components/ui/dialog";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import {
  ArrowLeft, Sparkles, Trophy, Brain, BarChart3, Wand2, Edit, Save,
} from "lucide-react";
import {
  getCampaign, getVariations, generateVariations, analyzeABTest, getConfig,
  startCampaign,
} from "@/lib/api";
import type { Campaign, CampaignVariation, ABTestAnalysis, EmailVariation, AppConfig } from "@/lib/types";
import { toast } from "sonner";
import { format } from "date-fns";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip as RechartsTooltip,
  ResponsiveContainer, Legend,
} from "recharts";

const TRIGGER_COLORS: Record<string, string> = {
  curiosity: "bg-purple-500/20 text-purple-400",
  urgency: "bg-red-500/20 text-red-400",
  social_proof: "bg-green-500/20 text-green-400",
  fear_of_missing_out: "bg-orange-500/20 text-orange-400",
  authority: "bg-blue-500/20 text-blue-400",
};

function HighlightedBody({ text }: { text: string }) {
  const parts = text.split(/(\{\{[^}]+\}\})/g);
  return (
    <div className="whitespace-pre-wrap text-sm">
      {parts.map((part, i) =>
        /^\{\{[^}]+\}\}$/.test(part) ? (
          <span key={i} className="mx-0.5 inline-block rounded bg-primary/20 px-1 py-0.5 text-xs font-medium text-primary">
            {part}
          </span>
        ) : (
          <span key={i}>{part}</span>
        )
      )}
    </div>
  );
}

export default function CampaignDetailPage() {
  const params = useParams();
  const router = useRouter();
  const campaignId = Number(params.id);

  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [variations, setVariations] = useState<CampaignVariation[]>([]);
  const [analysis, setAnalysis] = useState<ABTestAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [showGenerate, setShowGenerate] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [config, setConfig] = useState<AppConfig | null>(null);

  const [generatedVariations, setGeneratedVariations] = useState<EmailVariation[]>([]);
  const [patternsUsed, setPatternsUsed] = useState(0);
  const [editingVariation, setEditingVariation] = useState<string | null>(null);
  const [editSubject, setEditSubject] = useState("");
  const [editBody, setEditBody] = useState("");

  const [brief, setBrief] = useState({
    target_audience: "",
    goal: "",
    pain_point: "",
    tone: "professional but conversational",
    max_word_count: 150,
  });

  const fetchData = useCallback(async () => {
    try {
      const [campRes, varRes] = await Promise.all([
        getCampaign(campaignId),
        getVariations(campaignId).catch(() => ({ data: [] })),
      ]);
      setCampaign(campRes.data);
      setVariations(Array.isArray(varRes.data) ? varRes.data : []);
    } catch {
      toast.error("Failed to load campaign");
    } finally {
      setLoading(false);
    }
  }, [campaignId]);

  useEffect(() => {
    fetchData();
    getConfig().then((r) => setConfig(r.data)).catch(() => {});
  }, [fetchData]);

  const handleGenerate = async () => {
    if (!brief.target_audience || !brief.goal) {
      toast.error("Target audience and goal are required");
      return;
    }
    setGenerating(true);
    try {
      const res = await generateVariations(campaignId, {
        campaign_id: campaignId,
        ...brief,
      });
      setGeneratedVariations(res.data.variations ?? []);
      setPatternsUsed(res.data.patterns_used ?? 0);
      toast.success("5 variations generated!");
      setShowGenerate(false);
      fetchData();
    } catch {
      toast.error("Generation failed");
    } finally {
      setGenerating(false);
    }
  };

  const handleAnalyze = async () => {
    setAnalyzing(true);
    try {
      const res = await analyzeABTest(campaignId);
      setAnalysis(res.data);
      toast.success(`Winner: Variation ${res.data.winner_label}`);
      fetchData();
    } catch {
      toast.error("Analysis failed");
    } finally {
      setAnalyzing(false);
    }
  };

  const startEditVariation = (v: CampaignVariation | EmailVariation) => {
    setEditingVariation(v.label);
    setEditSubject(v.subject);
    setEditBody(v.body);
  };

  const saveEditVariation = () => {
    if (editingVariation) {
      setGeneratedVariations((prev) =>
        prev.map((v) =>
          v.label === editingVariation
            ? { ...v, subject: editSubject, body: editBody }
            : v
        )
      );
      setEditingVariation(null);
      toast.success(`Variation ${editingVariation} updated`);
    }
  };

  if (loading) {
    return (
      <>
        <Header title="Campaign" />
        <div className="flex h-96 items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        </div>
      </>
    );
  }

  if (!campaign) return null;

  const isAiPowered = config?.services.openai ?? false;
  const hasVariations = variations.length > 0;
  const hasWinner = variations.some((v) => v.is_winner);

  const chartData = analysis
    ? Object.entries(analysis.stats).map(([label, s]) => ({
        label,
        sends: s.sends,
        opens: s.opens,
        replies: s.replies,
      }))
    : variations.map((v) => ({
        label: v.label,
        sends: v.sends,
        opens: v.opens,
        replies: v.replies,
      }));

  return (
    <>
      <Header title={campaign.name} />
      <div className="space-y-6 p-6">
        <div className="flex items-center justify-between">
          <Button variant="ghost" size="sm" className="gap-1" onClick={() => router.push("/campaigns")}>
            <ArrowLeft className="h-4 w-4" /> Back
          </Button>
          <div className="flex items-center gap-2">
            <Badge variant="secondary" className="text-[10px]">
              {isAiPowered ? "AI-Powered" : "Demo Mode"}
            </Badge>
            {!hasVariations && (
              <Button size="sm" className="gap-1" onClick={() => setShowGenerate(true)}>
                <Wand2 className="h-4 w-4" /> Generate with AI
              </Button>
            )}
            {hasVariations && !hasWinner && (
              <Button size="sm" variant="outline" className="gap-1" onClick={handleAnalyze} disabled={analyzing}>
                <BarChart3 className="h-4 w-4" />
                {analyzing ? "Analyzing..." : "Analyze A/B Results"}
              </Button>
            )}
          </div>
        </div>

        {/* Campaign Info */}
        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground">Status</p>
              <Badge variant="secondary" className="mt-1">{campaign.status}</Badge>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground">Created</p>
              <p className="mt-1 text-sm font-medium">{format(new Date(campaign.created_at), "MMM d, yyyy")}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground">Description</p>
              <p className="mt-1 line-clamp-2 text-sm">{campaign.description || "No description"}</p>
            </CardContent>
          </Card>
        </div>

        {/* A/B Analysis Result */}
        {analysis && (
          <Card className="border-yellow-500/20 bg-gradient-to-br from-yellow-500/5 to-transparent">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Trophy className="h-5 w-5 text-yellow-400" />
                A/B Test Winner: Variation {analysis.winner_label}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm">{analysis.explanation}</p>
              <div className="rounded-lg border border-border bg-muted/50 p-3">
                <div className="flex items-center gap-2 text-sm font-medium">
                  <Brain className="h-4 w-4 text-primary" /> New AI Learning
                </div>
                <p className="mt-1 text-xs text-muted-foreground">{analysis.pattern_learned}</p>
              </div>
              {chartData.length > 0 && (
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={chartData} barSize={20}>
                    <XAxis dataKey="label" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <RechartsTooltip contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 8, fontSize: 12 }} />
                    <Legend />
                    <Bar dataKey="sends" fill="#6366f1" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="opens" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="replies" fill="#22c55e" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        )}

        {/* Stored Variations with stats */}
        {hasVariations && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Email Variations</CardTitle>
              <CardDescription>AI-generated A/B test variants</CardDescription>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue={variations[0]?.label ?? "A"}>
                <TabsList>
                  {variations.map((v) => (
                    <TabsTrigger key={v.label} value={v.label} className="gap-1">
                      {v.is_winner && <Trophy className="h-3 w-3 text-yellow-400" />}
                      Variant {v.label}
                    </TabsTrigger>
                  ))}
                </TabsList>
                {variations.map((v) => (
                  <TabsContent key={v.label} value={v.label} className="space-y-4">
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary" className={TRIGGER_COLORS[v.psychological_trigger ?? ""] ?? "bg-muted"}>
                        {v.psychological_trigger}
                      </Badge>
                      {v.is_winner && (
                        <Badge className="bg-yellow-500/20 text-yellow-400">Winner</Badge>
                      )}
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Subject</p>
                      <HighlightedBody text={v.subject} />
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Body</p>
                      <div className="mt-1 rounded-lg border border-border bg-muted/50 p-3">
                        <HighlightedBody text={v.body} />
                      </div>
                    </div>
                    <div className="grid grid-cols-4 gap-3">
                      <MetricBox label="Sends" value={v.sends} />
                      <MetricBox label="Opens" value={v.opens} rate={v.open_rate} />
                      <MetricBox label="Clicks" value={v.clicks} />
                      <MetricBox label="Replies" value={v.replies} rate={v.reply_rate} />
                    </div>
                  </TabsContent>
                ))}
              </Tabs>

              {/* Comparison Table */}
              <div className="mt-6">
                <p className="mb-2 text-sm font-medium">Variation Comparison</p>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Var</TableHead>
                      <TableHead>Subject</TableHead>
                      <TableHead>Sends</TableHead>
                      <TableHead>Opens</TableHead>
                      <TableHead>Open Rate</TableHead>
                      <TableHead>Replies</TableHead>
                      <TableHead>Reply Rate</TableHead>
                      <TableHead></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {variations.map((v) => (
                      <TableRow key={v.label} className={v.is_winner ? "bg-yellow-500/5 border-yellow-500/20" : ""}>
                        <TableCell className="font-medium">{v.label}</TableCell>
                        <TableCell className="max-w-[200px] truncate text-xs">{v.subject}</TableCell>
                        <TableCell>{v.sends}</TableCell>
                        <TableCell>{v.opens}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Progress value={v.open_rate} className="h-1.5 w-16" />
                            <span className="text-xs">{v.open_rate.toFixed(1)}%</span>
                          </div>
                        </TableCell>
                        <TableCell>{v.replies}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Progress value={v.reply_rate} className="h-1.5 w-16" />
                            <span className="text-xs">{v.reply_rate.toFixed(1)}%</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          {v.is_winner && <Trophy className="h-4 w-4 text-yellow-400" />}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Generated Variations Preview (editable) */}
        {generatedVariations.length > 0 && !hasVariations && (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Sparkles className="h-4 w-4" /> Generated Variations
                  </CardTitle>
                  <CardDescription>
                    AI used {patternsUsed} learned patterns from past campaigns. Edit before starting the campaign.
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="A">
                <TabsList>
                  {generatedVariations.map((v) => (
                    <TabsTrigger key={v.label} value={v.label}>
                      Variant {v.label}
                    </TabsTrigger>
                  ))}
                </TabsList>
                {generatedVariations.map((v) => (
                  <TabsContent key={v.label} value={v.label} className="space-y-3">
                    <div className="flex items-center justify-between">
                      <Badge variant="secondary" className={TRIGGER_COLORS[v.psychological_trigger] ?? ""}>
                        {v.psychological_trigger}
                      </Badge>
                      {editingVariation === v.label ? (
                        <Button size="sm" variant="outline" className="gap-1" onClick={saveEditVariation}>
                          <Save className="h-3 w-3" /> Save
                        </Button>
                      ) : (
                        <Button size="sm" variant="ghost" className="gap-1" onClick={() => startEditVariation(v)}>
                          <Edit className="h-3 w-3" /> Edit
                        </Button>
                      )}
                    </div>
                    {editingVariation === v.label ? (
                      <>
                        <div>
                          <Label className="text-xs">Subject</Label>
                          <Input value={editSubject} onChange={(e) => setEditSubject(e.target.value)} />
                        </div>
                        <div>
                          <Label className="text-xs">Body</Label>
                          <div className="mb-1 flex flex-wrap gap-1">
                            {["{{first_name}}", "{{last_name}}", "{{address}}", "{{property_type}}"].map((p) => (
                              <Button
                                key={p}
                                variant="outline"
                                size="sm"
                                className="h-5 text-[9px]"
                                onClick={() => setEditBody((prev) => prev + " " + p)}
                              >
                                {p}
                              </Button>
                            ))}
                          </div>
                          <Textarea value={editBody} onChange={(e) => setEditBody(e.target.value)} rows={6} />
                        </div>
                      </>
                    ) : (
                      <>
                        <div>
                          <p className="text-xs text-muted-foreground">Subject</p>
                          <HighlightedBody text={v.subject} />
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">Body</p>
                          <div className="mt-1 rounded-lg border border-border bg-muted/50 p-3">
                            <HighlightedBody text={v.body} />
                          </div>
                        </div>
                      </>
                    )}
                  </TabsContent>
                ))}
              </Tabs>
            </CardContent>
          </Card>
        )}

        {!hasVariations && generatedVariations.length === 0 && (
          <Card className="flex flex-col items-center justify-center py-16">
            <Wand2 className="mb-3 h-10 w-10 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">No AI variations yet.</p>
            <Button className="mt-3 gap-1" onClick={() => setShowGenerate(true)}>
              <Sparkles className="h-4 w-4" /> Generate with AI
            </Button>
          </Card>
        )}
      </div>

      {/* Generate Dialog */}
      <Dialog open={showGenerate} onOpenChange={setShowGenerate}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Wand2 className="h-5 w-5" /> AI Campaign Generator
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <div>
              <Label>Target Audience *</Label>
              <Input
                placeholder="e.g. Property managers in South Florida with portfolios above $500K"
                value={brief.target_audience}
                onChange={(e) => setBrief({ ...brief, target_audience: e.target.value })}
              />
            </div>
            <div>
              <Label>Goal *</Label>
              <Input
                placeholder="e.g. Book a 15-minute discovery call"
                value={brief.goal}
                onChange={(e) => setBrief({ ...brief, goal: e.target.value })}
              />
            </div>
            <div>
              <Label>Pain Point</Label>
              <Input
                placeholder="e.g. Low response rates from cold outreach"
                value={brief.pain_point}
                onChange={(e) => setBrief({ ...brief, pain_point: e.target.value })}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Tone</Label>
                <Input
                  value={brief.tone}
                  onChange={(e) => setBrief({ ...brief, tone: e.target.value })}
                />
              </div>
              <div>
                <Label>Max Words</Label>
                <Input
                  type="number"
                  value={brief.max_word_count}
                  onChange={(e) => setBrief({ ...brief, max_word_count: Number(e.target.value) })}
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowGenerate(false)}>Cancel</Button>
            <Button onClick={handleGenerate} disabled={generating} className="gap-1">
              <Sparkles className="h-4 w-4" />
              {generating ? "Generating..." : "Generate 5 Variations"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

function MetricBox({ label, value, rate }: { label: string; value: number; rate?: number }) {
  return (
    <div className="rounded-lg border border-border p-3 text-center">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-lg font-bold">{value}</p>
      {rate !== undefined && (
        <p className="text-xs text-muted-foreground">{rate.toFixed(1)}%</p>
      )}
    </div>
  );
}
