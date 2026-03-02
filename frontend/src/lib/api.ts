import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

// ── Config ──
export const getConfig = () => api.get("/config");

// ── Dashboard ──
export const getDashboard = () => api.get("/api/dashboard");
export const getDashboardStats = () => api.get("/api/dashboard/stats");
export const getDashboardFunnel = () => api.get("/api/dashboard/funnel");
export const getDashboardActivity = () => api.get("/api/dashboard/activity");
export const getInsights = () => api.get("/api/dashboard/insights");

// ── Leads ──
export const getLeads = (page = 1, perPage = 20, search?: string, status?: string) => {
  const params: Record<string, string | number> = { page, per_page: perPage };
  if (search) params.search = search;
  if (status) params.status = status;
  return api.get("/api/leads", { params });
};
export const getLead = (id: number) => api.get(`/api/leads/${id}`);
export const createLead = (data: Record<string, unknown>) => api.post("/api/leads", data);
export const updateLead = (id: number, data: Record<string, unknown>) => api.put(`/api/leads/${id}`, data);
export const deleteLead = (id: number) => api.delete(`/api/leads/${id}`);
export const uploadLeadsCSV = (file: File) => {
  const formData = new FormData();
  formData.append("file", file);
  return api.post("/api/leads/upload/csv", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};

// ── AI Lead Scoring ──
export const scoreLead = (leadId: number, icpDescription: string | null = null) =>
  api.post("/api/leads/score", { lead_id: leadId, icp_description: icpDescription });

export const scoreBulkLeads = (leadIds: number[], icpDescription: string | null = null) =>
  api.post("/api/leads/score/bulk", { lead_ids: leadIds, icp_description: icpDescription });

// ── Templates ──
export const getTemplates = (page = 1, perPage = 20, search?: string) => {
  const params: Record<string, string | number> = { page, per_page: perPage };
  if (search?.trim()) params.search = search.trim();
  return api.get("/api/templates", { params });
};
export const getTemplate = (id: number) => api.get(`/api/templates/${id}`);
export const getDefaultTemplate = () => api.get("/api/templates/default/active");
export const createTemplate = (data: Record<string, unknown>) => api.post("/api/templates", data);
export const updateTemplate = (id: number, data: Record<string, unknown>) =>
  api.put(`/api/templates/${id}`, data);
export const deleteTemplate = (id: number) => api.delete(`/api/templates/${id}`);
export const previewTemplate = (templateId: number, sampleData?: Record<string, string>) =>
  api.post(`/api/templates/${templateId}/preview`, sampleData ?? undefined);
export const seedDefaultTemplates = () => api.post("/api/templates/seed/defaults");

// ── Campaigns ──
export const getCampaigns = (page = 1, perPage = 20) =>
  api.get("/api/campaigns", { params: { page, per_page: perPage } });
export const getCampaign = (id: number) => api.get(`/api/campaigns/${id}`);
export const createCampaign = (data: Record<string, unknown>) => api.post("/api/campaigns", data);
export const updateCampaign = (id: number, data: Record<string, unknown>) =>
  api.put(`/api/campaigns/${id}`, data);
export const deleteCampaign = (id: number) => api.delete(`/api/campaigns/${id}`);
export const startCampaign = (id: number, data: Record<string, unknown>) =>
  api.post(`/api/campaigns/${id}/start`, data);

// ── AI Campaign Generation & A/B Testing ──
export const generateVariations = (campaignId: number, brief: Record<string, unknown>) =>
  api.post(`/api/campaigns/${campaignId}/generate`, brief);

export const getVariations = (campaignId: number) =>
  api.get(`/api/campaigns/${campaignId}/variations`);

export const analyzeABTest = (campaignId: number) =>
  api.post(`/api/campaigns/${campaignId}/analyze`);

// ── Chatbot ──
export const sendChatMessage = (
  leadId: number,
  messages: { role: string; content: string }[],
  context: Record<string, unknown> = {}
) => api.post("/api/chatbot/message", { lead_id: leadId, messages, ...context });

export const getChatHistory = (leadId: number) => api.get(`/api/chatbot/history/${leadId}`);

// ── SMS ──
export const sendSMS = (leadId: number, body: string, personalize = true) =>
  api.post("/api/sms/send", { lead_id: leadId, body, personalize });

export const getSMSHistory = (leadId: number) => api.get(`/api/sms/history/${leadId}`);

// ── Voice ──
export const startVoiceCall = (leadId: number, dynamicVars: Record<string, string> | null = null) =>
  api.post("/api/voice/call", { lead_id: leadId, dynamic_variables: dynamicVars });

export const getVoiceHistory = (leadId: number) => api.get(`/api/voice/history/${leadId}`);
export const getVoiceCall = (callId: number) => api.get(`/api/voice/call/${callId}`);

// ── Email History ──
export const getEmailHistory = (leadId: number) => api.get(`/api/leads/${leadId}/emails`);

// ── Demo Utilities ──
export const simulateOpen = (leadId: number) =>
  api.post("/api/demo/simulate/open", { lead_id: leadId });

export const simulateReply = (leadId: number, sentiment = "interested") =>
  api.post("/api/demo/simulate/reply", { lead_id: leadId, sentiment });

export const simulateBooking = (leadId: number, daysFromNow = 3) =>
  api.post("/api/demo/simulate/booking", { lead_id: leadId, days_from_now: daysFromNow });

export const seedData = () => api.post("/api/demo/seed");
export const resetData = () => api.post("/api/demo/reset?confirm=true");

export default api;
