"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity,
  ArrowRight,
  BarChart3,
  Bell,
  Bot,
  Building2,
  Check,
  ChevronRight,
  CircleDollarSign,
  FileCheck2,
  Gauge,
  LayoutDashboard,
  Menu,
  Plus,
  RefreshCw,
  Search,
  Sparkles,
  X,
} from "lucide-react";
import { io } from "socket.io-client";
import { API_BASE, api } from "@/lib/api";
import type { Health, LogEvent, Startup } from "@/lib/types";
import { ActivityPanel } from "./activity-panel";
import { FinScopeWorkspace } from "./finscope-workspace";
import { StartupWorkspace } from "./startup-workspace";
import { EmptyState, Toast, errorMessage, formatDate } from "./ui";

type View = "overview" | "startups" | "finscope" | "activity";
type ToastState = { message: string; kind: "success" | "error" } | null;

const navItems: Array<{ id: View; label: string; icon: React.ReactNode }> = [
  { id: "overview", label: "Overview", icon: <LayoutDashboard size={18} /> },
  { id: "startups", label: "Startup desk", icon: <Building2 size={18} /> },
  { id: "finscope", label: "FinScope", icon: <Sparkles size={18} /> },
  { id: "activity", label: "Live activity", icon: <Activity size={18} /> },
];

export function FinAgentApp() {
  const [view, setView] = useState<View>("overview");
  const [mobileNav, setMobileNav] = useState(false);
  const [health, setHealth] = useState<Health | null>(null);
  const [startups, setStartups] = useState<Startup[]>([]);
  const [loading, setLoading] = useState(true);
  const [backendError, setBackendError] = useState("");
  const [logs, setLogs] = useState<string[]>([]);
  const [socketConnected, setSocketConnected] = useState(false);
  const [toast, setToast] = useState<ToastState>(null);
  const [createSignal, setCreateSignal] = useState(0);

  const notify = useCallback((message: string, kind: "success" | "error" = "success") => {
    setToast({ message, kind });
  }, []);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [nextHealth, nextStartups] = await Promise.all([api.health(), api.listStartups()]);
      setHealth(nextHealth);
      setStartups(nextStartups);
      setBackendError("");
    } catch (error) {
      setBackendError(errorMessage(error));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void refresh(); }, [refresh]);

  useEffect(() => {
    const socket = io(API_BASE, { transports: ["websocket", "polling"] });
    socket.on("connect", () => setSocketConnected(true));
    socket.on("disconnect", () => setSocketConnected(false));
    socket.on("log_stream", (event: LogEvent) => {
      if (!event?.message) return;
      setLogs((current) => [event.message, ...current].slice(0, 80));
    });
    return () => { socket.disconnect(); };
  }, []);

  useEffect(() => {
    if (!toast) return;
    const timer = window.setTimeout(() => setToast(null), 4500);
    return () => window.clearTimeout(timer);
  }, [toast]);

  const navigate = (next: View) => {
    setView(next);
    setMobileNav(false);
  };

  const openCreate = () => {
    setView("startups");
    setCreateSignal((value) => value + 1);
    setMobileNav(false);
  };

  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileNav ? "open" : ""}`}>
        <div className="brand">
          <span className="brand-mark"><BarChart3 size={21} strokeWidth={2.4} /></span>
          <div><strong>FinAgent</strong><span>INVESTMENT OS</span></div>
        </div>

        <nav className="nav-list" aria-label="Main navigation">
          <p className="nav-label">Workspace</p>
          {navItems.map((item) => (
            <button key={item.id} className={view === item.id ? "active" : ""} onClick={() => navigate(item.id)}>
              {item.icon}<span>{item.label}</span>
              {item.id === "activity" && logs.length > 0 && <em>{Math.min(logs.length, 9)}</em>}
            </button>
          ))}
        </nav>

        <div className="sidebar-spacer" />
        <div className="system-card">
          <div className="system-card-head">
            <span className={`pulse-dot ${backendError ? "danger" : ""}`} />
            <strong>{backendError ? "Backend offline" : "System operational"}</strong>
          </div>
          <p>{health ? `${health.startups_loaded} startups · v${health.version}` : "Checking service status…"}</p>
          <button onClick={() => navigate("activity")}>View system health <ArrowRight size={14} /></button>
        </div>
        <div className="sidebar-footer">
          <div className="avatar">ML</div>
          <div><strong>Investment team</strong><span>Analyst workspace</span></div>
        </div>
      </aside>

      {mobileNav && <button className="sidebar-scrim" onClick={() => setMobileNav(false)} aria-label="Close menu" />}

      <main className="main">
        <header className="topbar">
          <button className="mobile-menu" onClick={() => setMobileNav(!mobileNav)} aria-label="Open menu"><Menu size={20} /></button>
          <div className="breadcrumb"><span>FinAgent</span><ChevronRight size={14} /><strong>{navItems.find((item) => item.id === view)?.label}</strong></div>
          <div className="top-actions">
            <button className="icon-button bell" title="Activity" onClick={() => setView("activity")}><Bell size={18} />{logs.length > 0 && <i />}</button>
            <button className="button primary compact" onClick={openCreate}><Plus size={16} /> New startup</button>
          </div>
        </header>

        <div className="content">
          {backendError && (
            <div className="connection-banner">
              <div><span><X size={16} /></span><p><strong>Can’t reach the FinAgent API</strong>{backendError} · Expected at {API_BASE}</p></div>
              <button className="button secondary compact" onClick={() => void refresh()}><RefreshCw size={15} /> Retry</button>
            </div>
          )}

          {view === "overview" && (
            <Overview
              health={health}
              startups={startups}
              loading={loading}
              onRefresh={refresh}
              onOpenStartup={() => setView("startups")}
              onOpenFinScope={() => setView("finscope")}
              onCreate={openCreate}
            />
          )}
          {view === "startups" && (
            <StartupWorkspace startups={startups} refresh={refresh} notify={notify} createSignal={createSignal} />
          )}
          {view === "finscope" && <FinScopeWorkspace notify={notify} />}
          {view === "activity" && <ActivityPanel health={health} logs={logs} connected={socketConnected} refresh={refresh} />}
        </div>
      </main>

      {toast && <Toast message={toast.message} kind={toast.kind} onClose={() => setToast(null)} />}
    </div>
  );
}

function Overview({
  health,
  startups,
  loading,
  onRefresh,
  onOpenStartup,
  onOpenFinScope,
  onCreate,
}: {
  health: Health | null;
  startups: Startup[];
  loading: boolean;
  onRefresh: () => Promise<void>;
  onOpenStartup: () => void;
  onOpenFinScope: () => void;
  onCreate: () => void;
}) {
  const readiness = health ? [health.llm_ready, health.qdrant_connected, health.embeddings_ready, health.docling_ready].filter(Boolean).length : 0;
  const recent = useMemo(() => [...startups].sort((a, b) => Date.parse(b.updated_at) - Date.parse(a.updated_at)).slice(0, 4), [startups]);

  return (
    <div className="page-stack">
      <section className="welcome-row">
        <div>
          <span className="eyebrow">Investment intelligence</span>
          <h1>Good morning, analyst.</h1>
          <p>Your diligence workspace is ready. Move from first look to investment memo with evidence in the loop.</p>
        </div>
        <button className="button secondary" onClick={() => void onRefresh()} disabled={loading} title="Refresh dashboard">
          <RefreshCw size={16} className={loading ? "spin" : ""} /> Refresh data
        </button>
      </section>

      <section className="metrics-grid">
        <Metric icon={<Building2 size={20} />} label="Startups tracked" value={String(startups.length)} note="In active workspace" tone="violet" />
        <Metric icon={<FileCheck2 size={20} />} label="Document-ready" value={String(startups.filter((item) => item.document_collections.length).length)} note="Profiles with evidence" tone="cyan" />
        <Metric icon={<Gauge size={20} />} label="Services ready" value={`${readiness}/4`} note={health?.llm_ready ? "AI pipeline available" : "Fallback mode active"} tone="green" />
        <Metric icon={<Activity size={20} />} label="Backend" value={health?.status === "healthy" ? "Healthy" : "Checking"} note={health ? `FinAgent v${health.version}` : "Connecting…"} tone="amber" />
      </section>

      <section className="overview-grid">
        <div className="card pipeline-card">
          <div className="card-heading"><div><span className="eyebrow">Due diligence pipeline</span><h2>From pitch to decision</h2></div><span className="live-chip"><i /> Agentic workflow</span></div>
          <div className="pipeline-track">
            {[
              ["01", "Register", "Capture the company profile", <Building2 key="i" size={18} />],
              ["02", "Ground", "Add decks and evidence", <FileCheck2 key="i" size={18} />],
              ["03", "Verify", "Check the MCA registry", <Check key="i" size={18} />],
              ["04", "Evaluate", "Generate the investment view", <BarChart3 key="i" size={18} />],
            ].map(([index, title, copy, icon], position) => (
              <div className="pipeline-step" key={String(title)}>
                <div className="pipeline-index">{icon}<small>{index}</small></div>
                <div><strong>{title}</strong><span>{copy}</span></div>
                {position < 3 && <ChevronRight className="pipeline-arrow" size={16} />}
              </div>
            ))}
          </div>
          <div className="pipeline-actions">
            <button className="button primary" onClick={onCreate}><Plus size={16} /> Start an evaluation</button>
            <button className="text-button" onClick={onOpenStartup}>Open startup desk <ArrowRight size={15} /></button>
          </div>
        </div>

        <button className="card advisor-card" onClick={onOpenFinScope}>
          <div className="advisor-glow" />
          <span className="advisor-icon"><Sparkles size={23} /></span>
          <span className="eyebrow">FinScope advisor</span>
          <h2>Ask a sharper financial question.</h2>
          <p>Route research, education, documents, portfolio questions, and live news to a specialist agent.</p>
          <span className="advisor-cta">Open a conversation <ArrowRight size={16} /></span>
        </button>
      </section>

      <section className="card table-card">
        <div className="card-heading"><div><span className="eyebrow">Portfolio coverage</span><h2>Recently updated</h2></div><button className="text-button" onClick={onOpenStartup}>View all <ArrowRight size={15} /></button></div>
        {recent.length ? (
          <div className="data-table">
            <div className="table-row table-header"><span>Company</span><span>Domain</span><span>Evidence</span><span>Updated</span><span>Status</span></div>
            {recent.map((startup) => (
              <button className="table-row" key={startup.startup_id} onClick={onOpenStartup}>
                <span className="company-cell"><i>{startup.name.slice(0, 2).toUpperCase()}</i><strong>{startup.name}</strong></span>
                <span>{startup.domain || "Uncategorised"}</span>
                <span>{startup.document_collections.length ? `${startup.document_collections.length} collection` : "Profile only"}</span>
                <span>{formatDate(startup.updated_at)}</span>
                <span><em className="status-pill active">Active</em></span>
              </button>
            ))}
          </div>
        ) : (
          <EmptyState icon={<Search size={22} />} title="No companies on your desk" copy="Register the first startup to begin a structured evaluation." />
        )}
      </section>
    </div>
  );
}

function Metric({ icon, label, value, note, tone }: { icon: React.ReactNode; label: string; value: string; note: string; tone: string }) {
  return (
    <div className="metric-card">
      <div className={`metric-icon ${tone}`}>{icon}</div>
      <div><span>{label}</span><strong>{value}</strong><small>{note}</small></div>
    </div>
  );
}
