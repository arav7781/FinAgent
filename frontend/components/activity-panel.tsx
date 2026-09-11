"use client";

import { Activity, Box, BrainCircuit, CircleCheck, Database, FileCog, Radio, RefreshCw, Server } from "lucide-react";
import type { Health } from "@/lib/types";
import { EmptyState } from "./ui";

export function ActivityPanel({ health, logs, connected, refresh }: { health: Health | null; logs: string[]; connected: boolean; refresh: () => Promise<void> }) {
  const services = [
    { name: "Language model", detail: "Agent reasoning & synthesis", ready: health?.llm_ready, icon: <BrainCircuit size={18} /> },
    { name: "Vector store", detail: "Evidence retrieval with Qdrant", ready: health?.qdrant_connected, icon: <Database size={18} /> },
    { name: "Embeddings", detail: "Semantic document indexing", ready: health?.embeddings_ready, icon: <Box size={18} /> },
    { name: "Document engine", detail: "PDF and DOCX extraction", ready: health?.docling_ready, icon: <FileCog size={18} /> },
    { name: "MCA provider", detail: "Corporate registry verification", ready: health?.mca_api_configured, fallback: true, icon: <Server size={18} /> },
    { name: "Live event stream", detail: "Socket.IO agent progress", ready: connected, icon: <Radio size={18} /> },
  ];

  return (
    <div className="page-stack activity-page">
      <section className="page-title-row"><div><span className="eyebrow">Operations</span><h1>System & activity</h1><p>See dependency readiness and follow agent work as it happens.</p></div><button className="button secondary" onClick={() => void refresh()}><RefreshCw size={16} /> Refresh health</button></section>
      <section className="service-grid">{services.map((service) => <div className="card service-card" key={service.name}><span className={`service-icon ${service.ready ? "ready" : ""}`}>{service.icon}</span><div><strong>{service.name}</strong><small>{service.detail}</small></div><span className={`service-state ${service.ready ? "ready" : service.fallback ? "fallback" : "offline"}`}>{service.ready ? "Ready" : service.fallback ? "Sandbox" : "Unavailable"}</span></div>)}</section>
      <section className="card log-card">
        <div className="card-heading"><div><span className="eyebrow">Agent telemetry</span><h2>Live event stream</h2></div><span className={`live-chip ${connected ? "" : "offline"}`}><i /> {connected ? "Connected" : "Reconnecting"}</span></div>
        <div className="terminal-head"><span /><span /><span /><p>finagent · log_stream</p></div>
        <div className="terminal-body">
          {logs.length ? logs.map((message, index) => <div className="log-line" key={`${index}-${message}`}><span>{String(logs.length - index).padStart(2, "0")}</span><i><CircleCheck size={14} /></i><p>{message}</p></div>) : <EmptyState icon={<Activity size={21} />} title="Waiting for agent activity" copy="Start an analysis or ask FinScope a question to see backend progress here." />}
        </div>
      </section>
    </div>
  );
}
