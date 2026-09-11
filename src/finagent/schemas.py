"""Request and response models.

Several fields exist purely for compatibility with an older Express frontend
(``startupId``, ``idea``, ``teamSize`` …). They are optional and normalised into
the canonical fields by :func:`finagent.services.startups.build_record`.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl

# ─── Startups ─────────────────────────────────────────────────────────────────

class StartupCreate(BaseModel):
    name: str = Field(..., description="Startup name")
    domain: str | None = Field(None, description="Industry / domain")
    description: str | None = Field(None, description="Idea or product description")
    team: str | None = Field(None, description="Team details and relevant experience")
    extras: str | None = Field(None, description="Any additional information")

    # Legacy frontend field names, normalised on write.
    startupId: str | None = None
    idea: str | None = None
    fundingRequired: str | None = None
    stage: str | None = None
    teamSize: int | None = None


class StartupUpdate(BaseModel):
    name: str | None = None
    domain: str | None = None
    description: str | None = None
    team: str | None = None
    extras: str | None = None


class StartupResponse(BaseModel):
    startup_id: str
    name: str
    domain: str
    description: str
    team: str
    extras: str | None
    created_at: str
    updated_at: str
    document_collections: list[str] = []


# ─── Documents ────────────────────────────────────────────────────────────────

class DocumentUploadRequest(BaseModel):
    document_url: HttpUrl = Field(..., description="Publicly reachable PDF or DOCX URL")


class DocumentUploadResponse(BaseModel):
    status: str
    startup_id: str
    collection_name: str | None = None
    chunks_stored: int
    message: str


# ─── Investor chat ────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    question: str = Field(..., description="Investor question about the startup")


class ChatResponse(BaseModel):
    answer: str = Field(..., description="AI-generated answer")
    startup_name: str


# ─── FinScope ─────────────────────────────────────────────────────────────────

class FinScopeChatRequest(BaseModel):
    question: str
    user_profile: str = "beginner"
    session_id: str = ""


class FinScopeChatResponse(BaseModel):
    answer: str
    agent_used: str
    intent: str


# ─── Registry verification ────────────────────────────────────────────────────

class MCAVerificationRequest(BaseModel):
    cin: str = Field(..., description="Company Identification Number (CIN)")


class MCAVerificationResponse(BaseModel):
    startup_id: str
    cin: str
    mca_verified: bool
    company_status: str | None
    company_name: str | None
    directors: list[str]
    name_match: bool
    flags: list[str]
    last_checked: str
    message: str


class MCAStatusResponse(BaseModel):
    startup_id: str
    cin: str | None
    mca_verified: bool
    company_status: str | None
    company_name: str | None
    directors: list[str]
    flags: list[str]
    last_checked: str | None


# ─── Health ───────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    qdrant_connected: bool
    embeddings_ready: bool
    llm_ready: bool
    docling_ready: bool
    startups_loaded: int
    mca_api_configured: bool
