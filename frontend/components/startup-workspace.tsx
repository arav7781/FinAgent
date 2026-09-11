"use client";

import { FormEvent, useEffect, useState } from "react";
import {
  AlertTriangle,
  ArrowDownToLine,
  Bot,
  Building2,
  Check,
  ChevronRight,
  CircleCheck,
  CircleDashed,
  FileText,
  Link2,
  MessageSquare,
  PenLine,
  Play,
  Plus,
  Search,
  Send,
  ShieldCheck,
  Upload,
  X,
} from "lucide-react";
import { api } from "@/lib/api";
import type { AnalysisStatus, ChatResponse, DocumentUpload, McaStatus, Startup, StartupCreate } from "@/lib/types";
import { EmptyState, Loader, errorMessage, formatDate } from "./ui";

type Tab = "profile" | "evidence" | "verification" | "analysis" | "chat";
type Notify = (message: string, kind?: "success" | "error") => void;

const tabs: Array<{ id: Tab; label: string; icon: React.ReactNode }> = [
  { id: "profile", label: "Profile", icon: <Building2 size={16} /> },
  { id: "evidence", label: "Evidence", icon: <FileText size={16} /> },
  { id: "verification", label: "Verification", icon: <ShieldCheck size={16} /> },
  { id: "analysis", label: "Analysis", icon: <Play size={16} /> },
  { id: "chat", label: "Investor Q&A", icon: <MessageSquare size={16} /> },
];

export function StartupWorkspace({ startups, refresh, notify, createSignal }: { startups: Startup[]; refresh: () => Promise<void>; notify: Notify; createSignal: number }) {
  const [selectedId, setSelectedId] = useState(startups[0]?.startup_id || "");
  const [selected, setSelected] = useState<Startup | null>(startups[0] || null);
  const [tab, setTab] = useState<Tab>("profile");
  const [showCreate, setShowCreate] = useState(false);
  const [search, setSearch] = useState("");
  const [fetching, setFetching] = useState(false);

  useEffect(() => {
    if (createSignal > 0) setShowCreate(true);
  }, [createSignal]);

  useEffect(() => {
    if (!selectedId && startups[0]) {
      setSelectedId(startups[0].startup_id);
      setSelected(startups[0]);
    } else if (selectedId) {
      const updated = startups.find((item) => item.startup_id === selectedId);
      if (updated) setSelected(updated);
    }
  }, [startups, selectedId]);

  const chooseStartup = async (startupId: string) => {
    setSelectedId(startupId);
    setFetching(true);
    try {
      setSelected(await api.getStartup(startupId));
      setTab("profile");
    } catch (error) {
      notify(errorMessage(error), "error");
    } finally {
      setFetching(false);
    }
  };

  const filtered = startups.filter((item) => `${item.name} ${item.domain}`.toLowerCase().includes(search.toLowerCase()));

  return (
    <div className="page-stack startup-page">
      <section className="page-title-row">
        <div><span className="eyebrow">Company diligence</span><h1>Startup desk</h1><p>Build an evidence-backed view of every company under review.</p></div>
        <button className="button primary" onClick={() => setShowCreate(true)}><Plus size={16} /> Register startup</button>
      </section>

      <section className="workspace-grid">
        <aside className="card startup-list-card">
          <div className="list-heading"><strong>Companies</strong><span>{startups.length}</span></div>
          <label className="search-field"><Search size={16} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search companies" /></label>
          <div className="startup-list">
            {filtered.map((startup) => (
              <button key={startup.startup_id} className={selectedId === startup.startup_id ? "active" : ""} onClick={() => void chooseStartup(startup.startup_id)}>
                <i>{startup.name.slice(0, 2).toUpperCase()}</i>
                <span><strong>{startup.name}</strong><small>{startup.domain || "Uncategorised"}</small></span>
                <ChevronRight size={15} />
              </button>
            ))}
            {!filtered.length && <p className="mini-empty">No matching startups.</p>}
          </div>
        </aside>

        <div className="card startup-detail-card">
          {selected ? (
            <>
              <div className="startup-detail-head">
                <div className="startup-monogram">{selected.name.slice(0, 2).toUpperCase()}</div>
                <div><span className="eyebrow">Active review</span><h2>{selected.name}</h2><p>{selected.domain || "Domain not set"} · Updated {formatDate(selected.updated_at)}</p></div>
                {fetching && <Loader label="Loading" />}
              </div>
              <div className="detail-tabs" role="tablist">
                {tabs.map((item) => <button key={item.id} className={tab === item.id ? "active" : ""} onClick={() => setTab(item.id)}>{item.icon}{item.label}</button>)}
              </div>
              <div className="detail-content">
                {tab === "profile" && <ProfilePanel startup={selected} refresh={refresh} notify={notify} />}
                {tab === "evidence" && <EvidencePanel startup={selected} refresh={refresh} notify={notify} />}
                {tab === "verification" && <VerificationPanel startup={selected} notify={notify} />}
                {tab === "analysis" && <AnalysisPanel startup={selected} notify={notify} />}
                {tab === "chat" && <InvestorChat startup={selected} notify={notify} />}
              </div>
            </>
          ) : (
            <EmptyState icon={<Building2 size={24} />} title="Select a company" copy="Choose a startup from the list or register a new one." />
          )}
        </div>
      </section>

      {showCreate && <CreateStartupModal onClose={() => setShowCreate(false)} onCreated={async (startup) => { await refresh(); setSelectedId(startup.startup_id); setSelected(startup); setShowCreate(false); notify(`${startup.name} added to the desk.`); }} notify={notify} />}
    </div>
  );
}

function ProfilePanel({ startup, refresh, notify }: { startup: Startup; refresh: () => Promise<void>; notify: Notify }) {
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setSaving(true);
    try {
      await api.updateStartup(startup.startup_id, {
        name: String(form.get("name")), domain: String(form.get("domain")), description: String(form.get("description")), team: String(form.get("team")), extras: String(form.get("extras")),
      });
      await refresh(); setEditing(false); notify("Startup profile updated.");
    } catch (error) { notify(errorMessage(error), "error"); } finally { setSaving(false); }
  };

  if (editing) return (
    <form className="form-stack" onSubmit={submit}>
      <div className="section-heading"><div><h3>Edit company profile</h3><p>Keep inputs concrete so the analysis has better context.</p></div><button type="button" className="icon-button" onClick={() => setEditing(false)} title="Cancel"><X size={17} /></button></div>
      <div className="form-grid two"><Field label="Company name"><input name="name" defaultValue={startup.name} required /></Field><Field label="Domain"><input name="domain" defaultValue={startup.domain} /></Field></div>
      <Field label="Product or idea"><textarea name="description" rows={4} defaultValue={startup.description} /></Field>
      <Field label="Team"><textarea name="team" rows={3} defaultValue={startup.team} /></Field>
      <Field label="Additional context"><textarea name="extras" rows={3} defaultValue={startup.extras || ""} /></Field>
      <div className="form-actions"><button type="button" className="button secondary" onClick={() => setEditing(false)}>Cancel</button><button className="button primary" disabled={saving}>{saving ? <Loader label="Saving" /> : <><Check size={16} /> Save changes</>}</button></div>
    </form>
  );

  return (
    <div className="panel-stack">
      <div className="section-heading"><div><h3>Company profile</h3><p>The context used throughout the diligence workflow.</p></div><button className="button secondary compact" onClick={() => setEditing(true)}><PenLine size={15} /> Edit profile</button></div>
      <div className="profile-fields">
        <ProfileField label="Company" value={startup.name} />
        <ProfileField label="Domain" value={startup.domain || "Not provided"} />
        <ProfileField label="Product or idea" value={startup.description || "Not provided"} wide />
        <ProfileField label="Team" value={startup.team || "Not provided"} wide />
        <ProfileField label="Additional context" value={startup.extras || "Not provided"} wide />
      </div>
      <div className="record-meta"><span>Record ID</span><code>{startup.startup_id}</code><span>Created</span><strong>{formatDate(startup.created_at)}</strong></div>
    </div>
  );
}

function EvidencePanel({ startup, refresh, notify }: { startup: Startup; refresh: () => Promise<void>; notify: Notify }) {
  const [url, setUrl] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState<"url" | "file" | "">("");
  const [result, setResult] = useState<DocumentUpload | null>(null);

  const ingestUrl = async (event: FormEvent) => {
    event.preventDefault(); setBusy("url");
    try { const next = await api.ingestDocumentUrl(startup.startup_id, url); setResult(next); setUrl(""); await refresh(); notify("Document URL processed."); }
    catch (error) { notify(errorMessage(error), "error"); } finally { setBusy(""); }
  };
  const upload = async () => {
    if (!file) return; setBusy("file");
    try { const next = await api.uploadStartupDocument(startup.startup_id, file); setResult(next); setFile(null); await refresh(); notify("Pitch deck uploaded and processed."); }
    catch (error) { notify(errorMessage(error), "error"); } finally { setBusy(""); }
  };

  return (
    <div className="panel-stack">
      <div className="section-heading"><div><h3>Evidence room</h3><p>Add a PDF or DOCX deck. Extracted material grounds chat and evaluation.</p></div><span className="count-badge">{startup.document_collections.length} indexed</span></div>
      <div className="evidence-grid">
        <div className="upload-box">
          <span className="upload-icon"><Upload size={22} /></span><strong>Upload a local document</strong><p>PDF or DOCX with readable text</p>
          <label className="file-picker"><input type="file" accept=".pdf,.docx" onChange={(event) => setFile(event.target.files?.[0] || null)} /><span>{file ? file.name : "Choose a file"}</span></label>
          <button className="button primary full" onClick={() => void upload()} disabled={!file || Boolean(busy)}>{busy === "file" ? <Loader label="Processing" /> : <><Upload size={16} /> Upload & index</>}</button>
        </div>
        <form className="upload-box" onSubmit={ingestUrl}>
          <span className="upload-icon"><Link2 size={22} /></span><strong>Import from a public URL</strong><p>Use a directly accessible document link</p>
          <input type="url" value={url} onChange={(event) => setUrl(event.target.value)} placeholder="https://example.com/deck.pdf" required />
          <button className="button secondary full" disabled={Boolean(busy)}>{busy === "url" ? <Loader label="Importing" /> : <><Link2 size={16} /> Import document</>}</button>
        </form>
      </div>
      {result && <div className="result-banner success"><CircleCheck size={19} /><div><strong>{result.chunks_stored} chunks available</strong><p>{result.message}</p></div></div>}
      <p className="hint"><CircleDashed size={15} /> If the vector store is unavailable, extracted text is still retained in memory and remains usable.</p>
    </div>
  );
}

function VerificationPanel({ startup, notify }: { startup: Startup; notify: Notify }) {
  const [status, setStatus] = useState<McaStatus | null>(null);
  const [cin, setCin] = useState("");
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState(false);

  useEffect(() => {
    setLoading(true);
    api.getMcaStatus(startup.startup_id).then(setStatus).catch((error) => notify(errorMessage(error), "error")).finally(() => setLoading(false));
  }, [startup.startup_id, notify]);

  const verify = async (event: FormEvent) => {
    event.preventDefault(); setVerifying(true);
    try { const next = await api.verifyMca(startup.startup_id, cin); setStatus(next); notify("MCA registry check complete."); }
    catch (error) { notify(errorMessage(error), "error"); try { setStatus(await api.getMcaStatus(startup.startup_id)); } catch {} }
    finally { setVerifying(false); }
  };

  return (
    <div className="panel-stack">
      <div className="section-heading"><div><h3>MCA registry verification</h3><p>Check company identity and status before forming an investment view.</p></div>{loading ? <Loader label="Checking" /> : <span className={`status-pill ${status?.mca_verified ? "verified" : "warning"}`}>{status?.mca_verified ? <Check size={13} /> : <AlertTriangle size={13} />}{status?.mca_verified ? "Verified" : "Not verified"}</span>}</div>
      <form className="verify-form" onSubmit={verify}><Field label="Company Identification Number (CIN)"><input value={cin} onChange={(event) => setCin(event.target.value.toUpperCase())} placeholder="U72900MH2021PTC123456" required /></Field><button className="button primary" disabled={verifying}>{verifying ? <Loader label="Verifying" /> : <><ShieldCheck size={16} /> Verify company</>}</button></form>
      {status && <div className="verification-card"><div className="verification-main"><span className={status.mca_verified ? "seal verified" : "seal"}><ShieldCheck size={27} /></span><div><small>Registry company</small><h4>{status.company_name || "No registry match on file"}</h4><p>{status.cin || "Submit a CIN to begin verification"}</p></div></div><div className="verification-facts"><ProfileField label="Company status" value={status.company_status || "Unknown"} /><ProfileField label="Last checked" value={formatDate(status.last_checked)} /><ProfileField label="Directors" value={status.directors.length ? status.directors.join(", ") : "Not available"} wide /></div>{status.flags.length > 0 && <div className="flag-row">{status.flags.map((flag) => <span key={flag}><AlertTriangle size={13} /> {flag.replaceAll("_", " ")}</span>)}</div>}</div>}
    </div>
  );
}

function AnalysisPanel({ startup, notify }: { startup: Startup; notify: Notify }) {
  const [status, setStatus] = useState<AnalysisStatus>({ status: "not_started" });
  const [generating, setGenerating] = useState(false);

  const check = async () => { try { setStatus(await api.getAnalysisStatus(startup.startup_id)); } catch (error) { notify(errorMessage(error), "error"); } };
  useEffect(() => { void check(); /* startup-scoped initial status */ }, [startup.startup_id]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (status.status !== "processing") return;
    const timer = window.setInterval(() => void check(), 3000);
    return () => window.clearInterval(timer);
  }, [status.status]); // eslint-disable-line react-hooks/exhaustive-deps

  const start = async () => { try { await api.startAnalysis(startup.startup_id); setStatus({ status: "processing" }); notify("Analysis started. Live progress is available in Activity."); } catch (error) { notify(errorMessage(error), "error"); } };
  const pdf = async () => {
    setGenerating(true);
    try { const blob = await api.generateReport(startup.startup_id); const url = URL.createObjectURL(blob); const link = document.createElement("a"); link.href = url; link.download = `${startup.name.toLowerCase().replace(/\W+/g, "-")}-finagent-report.pdf`; link.click(); window.setTimeout(() => URL.revokeObjectURL(url), 1000); notify("Investment report downloaded."); }
    catch (error) { notify(errorMessage(error), "error"); } finally { setGenerating(false); }
  };

  return (
    <div className="panel-stack">
      <div className="section-heading"><div><h3>Investment analysis</h3><p>Run the evidence retrieval, grading, registry, and recommendation pipeline.</p></div><span className={`status-pill ${status.status}`}>{status.status === "processing" && <span className="pulse-dot" />}{status.status.replace("_", " ")}</span></div>
      <div className="analysis-actions"><button className="button primary" onClick={() => void start()} disabled={status.status === "processing"}><Play size={16} /> {status.status === "complete" ? "Run again" : "Start background analysis"}</button><button className="button secondary" onClick={() => void pdf()} disabled={generating}>{generating ? <Loader label="Building PDF (up to 90s)" /> : <><ArrowDownToLine size={16} /> Generate PDF report</>}</button></div>
      {status.status === "processing" && <div className="progress-card"><div className="progress-orbit"><Bot size={20} /></div><div><strong>Agents are evaluating {startup.name}</strong><p>Research, evidence grading, and report synthesis are running in the background.</p><div className="progress-line"><span /></div></div></div>}
      {status.status === "failed" && <div className="result-banner error"><AlertTriangle size={19} /><div><strong>Analysis failed</strong><p>{status.error}</p></div></div>}
      {status.status === "complete" && status.analysis && <div className="analysis-result"><div className="score-card"><span>FinAgent score</span><strong>{status.analysis.score}<small>/10</small></strong><p>{status.analysis.recommendation}</p></div><div className="analysis-sections">{Object.entries({ "Executive summary": status.analysis.executiveSummary, "Market analysis": status.analysis.marketAnalysis, "Team assessment": status.analysis.teamAssessment, "Risk factors": status.analysis.riskFactors }).map(([title, copy]) => <article key={title}><strong>{title}</strong><p>{copy || "No section returned."}</p></article>)}</div></div>}
      {status.status === "not_started" && <EmptyState icon={<Play size={22} />} title="Ready when you are" copy="Start a background analysis or generate the full PDF synchronously." />}
    </div>
  );
}

function InvestorChat({ startup, notify }: { startup: Startup; notify: Notify }) {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Array<{ role: "user" | "assistant"; text: string }>>([]);
  const [busy, setBusy] = useState(false);
  const [lookup, setLookup] = useState<"id" | "name">("id");
  const ask = async (event: FormEvent) => {
    event.preventDefault(); if (!question.trim()) return;
    const prompt = question.trim(); setQuestion(""); setMessages((current) => [...current, { role: "user", text: prompt }]); setBusy(true);
    try { const response: ChatResponse = lookup === "id" ? await api.chatById(startup.startup_id, prompt) : await api.chatByName(startup.name, prompt); setMessages((current) => [...current, { role: "assistant", text: response.answer }]); }
    catch (error) { notify(errorMessage(error), "error"); } finally { setBusy(false); }
  };
  return (
    <div className="chat-panel">
      <div className="section-heading"><div><h3>Investor Q&A</h3><p>Answers are grounded in {startup.name}&apos;s profile and evidence.</p></div><div className="segmented"><button className={lookup === "id" ? "active" : ""} onClick={() => setLookup("id")}>By ID</button><button className={lookup === "name" ? "active" : ""} onClick={() => setLookup("name")}>By name</button></div></div>
      <div className="message-list">{messages.length === 0 ? <EmptyState icon={<MessageSquare size={22} />} title="Pressure-test the opportunity" copy="Ask about risks, moat, team fit, market size, or missing evidence." /> : messages.map((message, index) => <div className={`message ${message.role}`} key={index}>{message.role === "assistant" && <span><Bot size={17} /></span>}<p>{message.text}</p></div>)}{busy && <div className="message assistant"><span><Bot size={17} /></span><p><Loader label="Reviewing the evidence" /></p></div>}</div>
      <form className="chat-composer" onSubmit={ask}><textarea rows={2} value={question} onChange={(event) => setQuestion(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); event.currentTarget.form?.requestSubmit(); } }} placeholder="What are the most material risks for an investor?" /><button className="send-button" disabled={busy || !question.trim()} aria-label="Send question" title="Send question"><Send size={18} /></button></form>
    </div>
  );
}

function CreateStartupModal({ onClose, onCreated, notify }: { onClose: () => void; onCreated: (startup: Startup) => Promise<void>; notify: Notify }) {
  const [saving, setSaving] = useState(false);
  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); const data = new FormData(event.currentTarget); setSaving(true);
    const body: StartupCreate = { name: String(data.get("name")), domain: String(data.get("domain")), description: String(data.get("description")), team: String(data.get("team")), extras: String(data.get("extras")) };
    try { await onCreated(await api.createStartup(body)); } catch (error) { notify(errorMessage(error), "error"); } finally { setSaving(false); }
  };
  return <div className="modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}><div className="modal"><div className="modal-head"><div><span className="eyebrow">New diligence record</span><h2>Register a startup</h2><p>Start with what you know. Everything can be refined later.</p></div><button className="icon-button" onClick={onClose} title="Close"><X size={19} /></button></div><form className="form-stack" onSubmit={submit}><div className="form-grid two"><Field label="Company name"><input name="name" placeholder="QuantumFleet AI" required autoFocus /></Field><Field label="Domain"><input name="domain" placeholder="Logistics AI" /></Field></div><Field label="Product or idea"><textarea name="description" rows={3} placeholder="What does the company make, and for whom?" /></Field><Field label="Team"><textarea name="team" rows={2} placeholder="Founders, experience, and current team" /></Field><Field label="Additional context"><textarea name="extras" rows={2} placeholder="Stage, raise, traction, or anything else" /></Field><div className="form-actions"><button type="button" className="button secondary" onClick={onClose}>Cancel</button><button className="button primary" disabled={saving}>{saving ? <Loader label="Registering" /> : <><Plus size={16} /> Add to workspace</>}</button></div></form></div></div>;
}

function Field({ label, children }: { label: string; children: React.ReactNode }) { return <label className="field"><span>{label}</span>{children}</label>; }
function ProfileField({ label, value, wide = false }: { label: string; value: string; wide?: boolean }) { return <div className={`profile-field ${wide ? "wide" : ""}`}><span>{label}</span><p>{value}</p></div>; }
