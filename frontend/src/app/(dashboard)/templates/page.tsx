"use client";

import { useEffect, useState, useCallback } from "react";
import { Header } from "@/components/layout/header";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from "@/components/ui/dialog";
import {
  Plus, Mail, Trash2, Edit, Star, ChevronLeft, ChevronRight, Eye, Search,
} from "lucide-react";
import { getTemplates, createTemplate, updateTemplate, deleteTemplate, previewTemplate, seedDefaultTemplates } from "@/lib/api";
import type { EmailTemplate } from "@/lib/types";
import { toast } from "sonner";
import { format } from "date-fns";

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [editing, setEditing] = useState<EmailTemplate | null>(null);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [previewData, setPreviewData] = useState<{
    template_name: string;
    personalized: { subject: string; body: string };
    placeholders_found: string[];
  } | null>(null);
  const [seeding, setSeeding] = useState(false);

  const fetchTemplates = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getTemplates(page, 20, search || undefined);
      setTemplates(res.data.items ?? []);
      setTotal(res.data.total ?? 0);
      setTotalPages(res.data.total_pages ?? 1);
    } catch {
      toast.error("Failed to load templates");
    } finally {
      setLoading(false);
    }
  }, [page, search]);

  useEffect(() => {
    fetchTemplates();
  }, [fetchTemplates]);

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this template?")) return;
    try {
      await deleteTemplate(id);
      toast.success("Template deleted");
      fetchTemplates();
    } catch {
      toast.error("Failed to delete");
    }
  };

  const openEdit = (t: EmailTemplate) => {
    setEditing(t);
    setShowDialog(true);
  };

  const openCreate = () => {
    setEditing(null);
    setShowDialog(true);
  };

  const handlePreview = async (t: EmailTemplate) => {
    try {
      const res = await previewTemplate(t.id);
      const d = res.data as {
        template_name: string;
        personalized: { subject: string; body: string };
        placeholders_found: string[];
      };
      setPreviewData(d);
    } catch {
      toast.error("Failed to load preview");
    }
  };

  const handleSeedDefaults = async () => {
    setSeeding(true);
    try {
      const res = await seedDefaultTemplates();
      const msg = (res.data as { message?: string })?.message ?? "Default templates created";
      toast.success(msg);
      fetchTemplates();
    } catch {
      toast.error("Failed to seed default templates");
    } finally {
      setSeeding(false);
    }
  };

  return (
    <>
      <Header title="Email Templates" />
      <div className="space-y-4 p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search by name..."
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && setSearch(searchInput)}
                className="pl-8 w-56"
              />
            </div>
            <Button size="sm" variant="secondary" onClick={() => setSearch(searchInput)}>
              Search
            </Button>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Mail className="h-4 w-4" />
              {total} templates
            </div>
          </div>
          <div className="flex gap-2">
            <Button size="sm" variant="outline" onClick={handleSeedDefaults} disabled={seeding}>
              {seeding ? "Seeding..." : "Seed default templates"}
            </Button>
            <Button size="sm" className="gap-1" onClick={openCreate}>
              <Plus className="h-4 w-4" /> New Template
            </Button>
          </div>
        </div>

        {loading ? (
          <div className="flex h-48 items-center justify-center">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          </div>
        ) : templates.length === 0 ? (
          <Card className="flex flex-col items-center justify-center py-16">
            <Mail className="mb-3 h-10 w-10 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">No templates yet.</p>
            <Button className="mt-3" size="sm" onClick={openCreate}>
              Create First Template
            </Button>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {templates.map((t) => (
              <Card key={t.id} className="group relative">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="text-sm font-medium">{t.name}</h3>
                        {t.is_default && (
                          <Star className="h-3.5 w-3.5 fill-yellow-400 text-yellow-400" />
                        )}
                      </div>
                      <p className="mt-1 text-xs text-muted-foreground">Subject: {t.subject}</p>
                    </div>
                  </div>
                  <div className="mt-3 rounded-lg bg-muted/50 p-2">
                    <p className="line-clamp-3 text-xs text-muted-foreground whitespace-pre-wrap">
                      {t.body}
                    </p>
                  </div>
                  <div className="mt-3 flex items-center justify-between">
                    <p className="text-[10px] text-muted-foreground">
                      {format(new Date(t.created_at), "MMM d, yyyy")}
                    </p>
                    <div className="flex items-center gap-1">
                      <Button variant="ghost" size="icon" className="h-7 w-7" title="Preview" onClick={() => handlePreview(t)}>
                        <Eye className="h-3.5 w-3.5" />
                      </Button>
                      <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => openEdit(t)}>
                        <Edit className="h-3.5 w-3.5" />
                      </Button>
                      <Button variant="ghost" size="icon" className="h-7 w-7 text-destructive" onClick={() => handleDelete(t.id)}>
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-2">
            <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <span className="text-sm text-muted-foreground">Page {page} of {totalPages}</span>
            <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage(page + 1)}>
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        )}
      </div>

      <TemplateDialog
        open={showDialog}
        editing={editing}
        onClose={() => { setShowDialog(false); setEditing(null); }}
        onSaved={() => { setShowDialog(false); setEditing(null); fetchTemplates(); }}
      />

      <Dialog open={!!previewData} onOpenChange={() => setPreviewData(null)}>
        <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Preview: {previewData?.template_name}</DialogTitle>
          </DialogHeader>
          {previewData && (
            <div className="space-y-4">
              <div>
                <Label className="text-muted-foreground">Subject (with sample data)</Label>
                <p className="mt-1 rounded-md bg-muted px-3 py-2 text-sm">{previewData.personalized.subject}</p>
              </div>
              <div>
                <Label className="text-muted-foreground">Body (with sample data)</Label>
                <pre className="mt-1 whitespace-pre-wrap rounded-md bg-muted p-3 text-sm">{previewData.personalized.body}</pre>
              </div>
              {previewData.placeholders_found?.length > 0 && (
                <p className="text-xs text-muted-foreground">
                  Placeholders: {previewData.placeholders_found.join(", ")}
                </p>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}

function TemplateDialog({
  open,
  editing,
  onClose,
  onSaved,
}: {
  open: boolean;
  editing: EmailTemplate | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [form, setForm] = useState({
    name: "",
    subject: "",
    body: "",
    is_default: false,
  });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (editing) {
      setForm({
        name: editing.name,
        subject: editing.subject,
        body: editing.body,
        is_default: editing.is_default,
      });
    } else {
      setForm({ name: "", subject: "", body: "", is_default: false });
    }
  }, [editing]);

  const handleSubmit = async () => {
    if (!form.name || !form.subject || !form.body) {
      toast.error("All fields are required");
      return;
    }
    setSaving(true);
    try {
      if (editing) {
        await updateTemplate(editing.id, form);
        toast.success("Template updated");
      } else {
        await createTemplate(form);
        toast.success("Template created");
      }
      onSaved();
    } catch {
      toast.error("Failed to save template");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>{editing ? "Edit Template" : "New Template"}</DialogTitle>
        </DialogHeader>
        <div className="space-y-3">
          <div>
            <Label>Template Name</Label>
            <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </div>
          <div>
            <Label>Subject Line</Label>
            <Input value={form.subject} onChange={(e) => setForm({ ...form, subject: e.target.value })} />
          </div>
          <div>
            <Label>Email Body</Label>
            <div className="mb-1 flex flex-wrap gap-1">
              {["{{first_name}}", "{{last_name}}", "{{email}}", "{{address}}", "{{property_type}}", "{{estimated_value}}"].map((p) => (
                <Button
                  key={p}
                  variant="outline"
                  size="sm"
                  className="h-5 text-[9px]"
                  onClick={() => setForm({ ...form, body: form.body + " " + p })}
                >
                  {p}
                </Button>
              ))}
            </div>
            <Textarea value={form.body} onChange={(e) => setForm({ ...form, body: e.target.value })} rows={6} />
          </div>
          <div className="flex items-center gap-2">
            <Switch
              checked={form.is_default}
              onCheckedChange={(v) => setForm({ ...form, is_default: v })}
            />
            <Label>Set as default template</Label>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button onClick={handleSubmit} disabled={saving}>
            {saving ? "Saving..." : editing ? "Update" : "Create"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
