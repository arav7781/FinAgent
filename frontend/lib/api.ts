import type {
  AnalysisStatus,
  ChatResponse,
  DocumentUpload,
  FinScopeDocumentResponse,
  FinScopeResponse,
  Headline,
  Health,
  McaStatus,
  Startup,
  StartupCreate,
  StartupUpdate,
} from "./types";

export const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:7860").replace(/\/$/, "");

export class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  if (init?.body && !(init.body instanceof FormData)) headers.set("Content-Type", "application/json");

  const response = await fetch(`${API_BASE}${path}`, { ...init, headers, cache: "no-store" });
  if (!response.ok) {
    let message = `${response.status} ${response.statusText}`;
    try {
      const body = (await response.json()) as { detail?: string | Array<{ msg: string }> };
      if (typeof body.detail === "string") message = body.detail;
      else if (Array.isArray(body.detail)) message = body.detail.map((item) => item.msg).join(", ");
    } catch {
      // Preserve the HTTP status message for non-JSON errors.
    }
    throw new ApiError(message, response.status);
  }
  return response.json() as Promise<T>;
}

const id = (value: string) => encodeURIComponent(value);

export const api = {
  health: () => request<Health>("/health"),

  listStartups: () => request<Startup[]>("/startups"),
  getStartup: (startupId: string) => request<Startup>(`/startups/${id(startupId)}`),
  createStartup: (body: StartupCreate) =>
    request<Startup>("/startups", { method: "POST", body: JSON.stringify(body) }),
  registerStartupLegacy: (body: StartupCreate) =>
    request<Startup>("/api/startups/register", { method: "POST", body: JSON.stringify(body) }),
  updateStartup: (startupId: string, body: StartupUpdate) =>
    request<Startup>(`/startups/${id(startupId)}`, { method: "PUT", body: JSON.stringify(body) }),

  ingestDocumentUrl: (startupId: string, documentUrl: string) =>
    request<DocumentUpload>(`/startups/${id(startupId)}/documents`, {
      method: "POST",
      body: JSON.stringify({ document_url: documentUrl }),
    }),
  uploadStartupDocument: (startupId: string, file: File) => {
    const body = new FormData();
    body.append("documents", file);
    return request<DocumentUpload>(`/api/startups/${id(startupId)}/documents/upload`, { method: "POST", body });
  },

  verifyMca: (startupId: string, cin: string) =>
    request<McaStatus>(`/startups/${id(startupId)}/verify/mca`, {
      method: "POST",
      body: JSON.stringify({ cin }),
    }),
  getMcaStatus: (startupId: string) => request<McaStatus>(`/startups/${id(startupId)}/verify/mca`),

  startAnalysis: (startupId: string) =>
    request<{ status: string; id: string }>(`/api/startups/${id(startupId)}/analyze`, { method: "POST" }),
  getAnalysisStatus: (startupId: string) =>
    request<AnalysisStatus>(`/api/startups/${id(startupId)}/report/status`),
  generateReport: async (startupId: string) => {
    const response = await fetch(`${API_BASE}/reports/${id(startupId)}`, { method: "POST" });
    if (!response.ok) {
      let message = `Report generation failed (${response.status})`;
      try {
        const body = (await response.json()) as { detail?: string };
        message = body.detail || message;
      } catch {}
      throw new ApiError(message, response.status);
    }
    return response.blob();
  },

  chatById: (startupId: string, question: string) =>
    request<ChatResponse>(`/chat/${id(startupId)}`, { method: "POST", body: JSON.stringify({ question }) }),
  chatByName: (startupName: string, question: string) =>
    request<ChatResponse>(`/chat/by-name/${id(startupName)}`, { method: "POST", body: JSON.stringify({ question }) }),

  finScopeChat: (question: string, userProfile: string, sessionId: string) =>
    request<FinScopeResponse>("/finscope/chat", {
      method: "POST",
      body: JSON.stringify({ question, user_profile: userProfile, session_id: sessionId }),
    }),
  analyzeFinScopeDocument: (file: File, sessionId: string, userProfile: string) => {
    const body = new FormData();
    body.append("document", file);
    body.append("session_id", sessionId);
    body.append("user_profile", userProfile);
    return request<FinScopeDocumentResponse>("/finscope/analyze-document", { method: "POST", body });
  },
  getHeadlines: (symbol: string, limit = 10) =>
    request<{ headlines: Headline[] }>(`/api/finance-news/headlines?symbol=${id(symbol)}&limit=${limit}`),
};
