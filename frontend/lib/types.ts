export type Startup = {
  startup_id: string;
  name: string;
  domain: string;
  description: string;
  team: string;
  extras: string | null;
  created_at: string;
  updated_at: string;
  document_collections: string[];
};

export type StartupCreate = {
  name: string;
  domain?: string;
  description?: string;
  team?: string;
  extras?: string;
};

export type StartupUpdate = Partial<Omit<StartupCreate, "name">> & { name?: string };

export type Health = {
  status: string;
  service: string;
  version: string;
  qdrant_connected: boolean;
  embeddings_ready: boolean;
  llm_ready: boolean;
  docling_ready: boolean;
  startups_loaded: number;
  mca_api_configured: boolean;
};

export type DocumentUpload = {
  status: string;
  startup_id: string;
  collection_name: string | null;
  chunks_stored: number;
  message: string;
};

export type McaStatus = {
  startup_id: string;
  cin: string | null;
  mca_verified: boolean;
  company_status: string | null;
  company_name: string | null;
  directors: string[];
  flags: string[];
  last_checked: string | null;
  name_match?: boolean;
  message?: string;
};

export type AnalysisSections = {
  executiveSummary: string;
  marketAnalysis: string;
  teamAssessment: string;
  riskFactors: string;
  recommendation: string;
  score: number;
};

export type AnalysisStatus = {
  status: "not_started" | "processing" | "complete" | "failed";
  analysis?: AnalysisSections | null;
  error?: string;
};

export type ChatResponse = { answer: string; startup_name: string };

export type FinScopeResponse = {
  answer: string;
  agent_used: string;
  intent: string;
};

export type FinScopeDocumentResponse = {
  analysis: string;
  agent_used: string;
  intent: string;
};

export type Headline = {
  title?: string;
  url?: string;
  source?: string;
  publisher?: string;
  published_at?: string;
  date?: string;
  [key: string]: unknown;
};

export type LogEvent = { message: string };
