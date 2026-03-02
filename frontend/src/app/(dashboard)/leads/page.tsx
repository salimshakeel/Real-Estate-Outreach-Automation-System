"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { Header } from "@/components/layout/header";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import {
  Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import {
  Users, Plus, Upload, Search, Brain, ChevronLeft, ChevronRight, Trash2, Eye,
} from "lucide-react";
import {
  getLeads, createLead, deleteLead, uploadLeadsCSV, scoreBulkLeads, getConfig,
} from "@/lib/api";
import type { Lead, AppConfig } from "@/lib/types";
import { toast } from "sonner";
import { ArrowUpDown } from "lucide-react";

const STATUS_COLORS: Record<string, string> = {
  uploaded: "bg-gray-500/20 text-gray-400",
  contacted: "bg-blue-500/20 text-blue-400",
  replied: "bg-yellow-500/20 text-yellow-400",
  interested: "bg-orange-500/20 text-orange-400",
  booked: "bg-green-500/20 text-green-400",
  closed: "bg-emerald-500/20 text-emerald-400",
};

const PRIORITY_COLORS: Record<string, string> = {
  Hot: "bg-red-500/20 text-red-400",
  Warm: "bg-orange-500/20 text-orange-400",
  Cold: "bg-blue-500/20 text-blue-400",
  Dead: "bg-gray-500/20 text-gray-400",
};

const PRIORITY_ORDER: Record<string, number> = { Hot: 0, Warm: 1, Cold: 2, Dead: 3 };

export default function LeadsPage() {
  const router = useRouter();
  const [leads, setLeads] = useState<Lead[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [sortByPriority, setSortByPriority] = useState(false);
  const [config, setConfig] = useState<AppConfig | null>(null);

  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showScoreDialog, setShowScoreDialog] = useState(false);
  const [icpText, setIcpText] = useState("");
  const [scoring, setScoring] = useState(false);

  const fileRef = useRef<HTMLInputElement>(null);

  const fetchLeads = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getLeads(page, 15, search || undefined, statusFilter === "all" ? undefined : statusFilter);
      setLeads(res.data.items ?? []);
      setTotal(res.data.total ?? 0);
      setTotalPages(res.data.total_pages ?? 1);
    } catch {
      toast.error("Failed to load leads");
    } finally {
      setLoading(false);
    }
  }, [page, search, statusFilter]);

  useEffect(() => {
    fetchLeads();
  }, [fetchLeads]);

  useEffect(() => {
    getConfig().then((r) => setConfig(r.data)).catch(() => {});
  }, []);

  const sortedLeads = sortByPriority
    ? [...leads].sort((a, b) => {
        const pa = a.ai_score ? (PRIORITY_ORDER[a.ai_score.priority] ?? 99) : 99;
        const pb = b.ai_score ? (PRIORITY_ORDER[b.ai_score.priority] ?? 99) : 99;
        return pa - pb;
      })
    : leads;

  const isAiPowered = config?.services.openai ?? false;

  const handleCSVUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const res = await uploadLeadsCSV(file);
      toast.success(`Uploaded: ${res.data.created} leads created, ${res.data.duplicates} duplicates`);
      fetchLeads();
    } catch {
      toast.error("CSV upload failed");
    }
    if (fileRef.current) fileRef.current.value = "";
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this lead?")) return;
    try {
      await deleteLead(id);
      toast.success("Lead deleted");
      fetchLeads();
    } catch {
      toast.error("Failed to delete lead");
    }
  };

  const handleBulkScore = async () => {
    setScoring(true);
    const ids = leads.map((l) => l.id);
    try {
      const res = await scoreBulkLeads(ids, icpText || null);
      const results = res.data.results ?? [];
      const hot = results.filter((r: { priority: string }) => r.priority === "Hot").length;
      const warm = results.filter((r: { priority: string }) => r.priority === "Warm").length;
      const cold = results.filter((r: { priority: string }) => r.priority === "Cold").length;
      toast.success(`${results.length} leads scored — ${hot} Hot, ${warm} Warm, ${cold} Cold`);
      setShowScoreDialog(false);
      fetchLeads();
    } catch {
      toast.error("Scoring failed");
    } finally {
      setScoring(false);
    }
  };

  return (
    <>
      <Header title="Leads" />
      <div className="space-y-4 p-6">
        {/* Controls */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search leads..."
                value={search}
                onChange={(e) => { setSearch(e.target.value); setPage(1); }}
                className="pl-9 w-64"
              />
            </div>
            <Select value={statusFilter} onValueChange={(v) => { setStatusFilter(v); setPage(1); }}>
              <SelectTrigger className="w-36">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="uploaded">Uploaded</SelectItem>
                <SelectItem value="contacted">Contacted</SelectItem>
                <SelectItem value="replied">Replied</SelectItem>
                <SelectItem value="interested">Interested</SelectItem>
                <SelectItem value="booked">Booked</SelectItem>
                <SelectItem value="closed">Closed</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" className="gap-1" onClick={() => setShowScoreDialog(true)}>
              <Brain className="h-4 w-4" /> Score All with AI
              <Badge variant="secondary" className="ml-1 text-[9px]">
                {isAiPowered ? "AI" : "Demo"}
              </Badge>
            </Button>
            <Button variant="outline" size="sm" className="gap-1" onClick={() => fileRef.current?.click()}>
              <Upload className="h-4 w-4" /> Upload CSV
            </Button>
            <input ref={fileRef} type="file" accept=".csv" className="hidden" onChange={handleCSVUpload} />
            <Button size="sm" className="gap-1" onClick={() => setShowCreateDialog(true)}>
              <Plus className="h-4 w-4" /> Add Lead
            </Button>
          </div>
        </div>

        {/* Total count */}
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Users className="h-4 w-4" />
          {total} leads total
        </div>

        {/* Table */}
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Phone</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>
                    <button
                      className="flex items-center gap-1 hover:text-foreground"
                      onClick={() => setSortByPriority(!sortByPriority)}
                    >
                      Priority <ArrowUpDown className="h-3 w-3" />
                    </button>
                  </TableHead>
                  <TableHead>Property</TableHead>
                  <TableHead>Value</TableHead>
                  <TableHead className="w-20"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={8} className="h-32 text-center text-muted-foreground">
                      Loading...
                    </TableCell>
                  </TableRow>
                ) : leads.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} className="h-32 text-center text-muted-foreground">
                      No leads found. Upload a CSV or add one manually.
                    </TableCell>
                  </TableRow>
                ) : (
                  sortedLeads.map((lead) => (
                    <TableRow
                      key={lead.id}
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => router.push(`/leads/${lead.id}`)}
                    >
                      <TableCell className="font-medium">
                        {lead.first_name} {lead.last_name || ""}
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">{lead.email}</TableCell>
                      <TableCell className="text-xs">{lead.phone || "—"}</TableCell>
                      <TableCell>
                        <Badge variant="secondary" className={STATUS_COLORS[lead.status] ?? ""}>
                          {lead.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {lead.ai_score ? (
                          <div className="flex items-center gap-1.5">
                            <Badge variant="secondary" className={PRIORITY_COLORS[lead.ai_score.priority] ?? ""}>
                              {lead.ai_score.priority}
                            </Badge>
                            <span className="text-xs font-medium">{lead.ai_score.score}</span>
                          </div>
                        ) : (
                          <span className="text-xs text-muted-foreground">—</span>
                        )}
                      </TableCell>
                      <TableCell className="text-xs">{lead.property_type || "—"}</TableCell>
                      <TableCell className="text-xs">{lead.estimated_value || "—"}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => router.push(`/leads/${lead.id}`)}>
                            <Eye className="h-3.5 w-3.5" />
                          </Button>
                          <Button variant="ghost" size="icon" className="h-7 w-7 text-destructive" onClick={() => handleDelete(lead.id)}>
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-2">
            <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <span className="text-sm text-muted-foreground">
              Page {page} of {totalPages}
            </span>
            <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage(page + 1)}>
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        )}
      </div>

      {/* Create Lead Dialog */}
      <CreateLeadDialog
        open={showCreateDialog}
        onClose={() => setShowCreateDialog(false)}
        onCreated={fetchLeads}
      />

      {/* Bulk Score Dialog */}
      <Dialog open={showScoreDialog} onOpenChange={setShowScoreDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Brain className="h-5 w-5" /> Score Leads with AI
            </DialogTitle>
            <DialogDescription>
              Describe your ideal customer profile for more accurate scoring.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <Label>Ideal Customer Profile (optional)</Label>
            <Textarea
              placeholder="e.g. Commercial property managers in South Florida with portfolios above $500K"
              value={icpText}
              onChange={(e) => setIcpText(e.target.value)}
              rows={3}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowScoreDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleBulkScore} disabled={scoring} className="gap-1">
              {scoring ? "Scoring..." : "Score All Leads"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

function CreateLeadDialog({
  open,
  onClose,
  onCreated,
}: {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}) {
  const [form, setForm] = useState({
    email: "",
    first_name: "",
    last_name: "",
    company: "",
    phone: "",
    address: "",
    property_type: "",
    estimated_value: "",
    notes: "",
  });
  const [saving, setSaving] = useState(false);

  const handleSubmit = async () => {
    if (!form.email || !form.first_name) {
      toast.error("Email and first name are required");
      return;
    }
    setSaving(true);
    try {
      await createLead(form);
      toast.success("Lead created");
      onClose();
      onCreated();
      setForm({ email: "", first_name: "", last_name: "", company: "", phone: "", address: "", property_type: "", estimated_value: "", notes: "" });
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Failed to create lead";
      toast.error(msg);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Add New Lead</DialogTitle>
        </DialogHeader>
        <div className="grid gap-3 sm:grid-cols-2">
          <div>
            <Label>First Name *</Label>
            <Input value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} />
          </div>
          <div>
            <Label>Last Name</Label>
            <Input value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} />
          </div>
          <div className="sm:col-span-2">
            <Label>Email *</Label>
            <Input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          </div>
          <div>
            <Label>Phone</Label>
            <Input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
          </div>
          <div>
            <Label>Company</Label>
            <Input value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} />
          </div>
          <div className="sm:col-span-2">
            <Label>Address</Label>
            <Input value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} />
          </div>
          <div>
            <Label>Property Type</Label>
            <Input value={form.property_type} onChange={(e) => setForm({ ...form, property_type: e.target.value })} />
          </div>
          <div>
            <Label>Estimated Value</Label>
            <Input value={form.estimated_value} onChange={(e) => setForm({ ...form, estimated_value: e.target.value })} />
          </div>
          <div className="sm:col-span-2">
            <Label>Notes</Label>
            <Textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} rows={2} />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button onClick={handleSubmit} disabled={saving}>
            {saving ? "Creating..." : "Create Lead"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
