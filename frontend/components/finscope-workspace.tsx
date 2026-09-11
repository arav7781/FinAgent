"use client";

import { FormEvent, useMemo, useState } from "react";
import {
  ArrowUpRight,
  Bot,
  BriefcaseBusiness,
  FileSearch,
  GraduationCap,
  Newspaper,
  Search,
  Send,
  Sparkles,
  Upload,
} from "lucide-react";
import { api } from "@/lib/api";
import type { Headline } from "@/lib/types";
import { EmptyState, Loader, errorMessage } from "./ui";

type Notify = (message: string, kind?: "success" | "error") => void;
type Message = { role: "user" | "assistant"; text: string; agent?: string; intent?: string };

const starters = [
  { icon: <GraduationCap size={18} />, title: "Learn a concept", prompt: "Explain the difference between enterprise value and equity value." },
  { icon: <Search size={18} />, title: "Research a market", prompt: "How should I think about market sizing for vertical SaaS?" },
  { icon: <BriefcaseBusiness size={18} />, title: "Shape a portfolio", prompt: "Help me think through concentration risk in my startup portfolio." },
  { icon: <Newspaper size={18} />, title: "Review the news", prompt: "What are the latest material updates for NVIDIA?" },
];

export function FinScopeWorkspace({ notify }: { notify: Notify }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState("");
  const [profile, setProfile] = useState("beginner");
  const [sessionId] = useState(() => `web-${Date.now().toString(36)}`);
  const [busy, setBusy] = useState(false);
  const [documentFile, setDocumentFile] = useState<File | null>(null);
  const [documentBusy, setDocumentBusy] = useState(false);
  const [symbol, setSymbol] = useState("INFY:NSE");
  const [headlines, setHeadlines] = useState<Headline[]>([]);
  const [newsBusy, setNewsBusy] = useState(false);

  const ask = async (event?: FormEvent, suggested?: string) => {
    event?.preventDefault();
    const prompt = (suggested || question).trim();
    if (!prompt || busy) return;
    setQuestion("");
    setMessages((current) => [...current, { role: "user", text: prompt }]);
    setBusy(true);
    try {
      const result = await api.finScopeChat(prompt, profile, sessionId);
      setMessages((current) => [...current, { role: "assistant", text: result.answer, agent: result.agent_used, intent: result.intent }]);
    } catch (error) {
      notify(errorMessage(error), "error");
    } finally {
      setBusy(false);
    }
  };

  const analyzeDocument = async () => {
    if (!documentFile) return;
    setDocumentBusy(true);
    setMessages((current) => [...current, { role: "user", text: `Analyze the uploaded document: ${documentFile.name}` }]);
    try {
      const result = await api.analyzeFinScopeDocument(documentFile, sessionId, profile);
      setMessages((current) => [...current, { role: "assistant", text: result.analysis, agent: result.agent_used, intent: result.intent }]);
      notify("Document analyzed and attached to this session.");
      setDocumentFile(null);
    } catch (error) {
      notify(errorMessage(error), "error");
    } finally {
      setDocumentBusy(false);
    }
  };

  const loadNews = async (event: FormEvent) => {
    event.preventDefault(); setNewsBusy(true);
    try {
      const result = await api.getHeadlines(symbol, 8);
      setHeadlines(result.headlines);
      if (!result.headlines.length) notify("No live headlines returned. Check RAPIDAPI_KEY on the backend.", "error");
    } catch (error) { notify(errorMessage(error), "error"); } finally { setNewsBusy(false); }
  };

  return (
    <div className="page-stack finscope-page">
      <section className="page-title-row">
        <div><span className="eyebrow">Adaptive financial guidance</span><h1>FinScope</h1><p>One conversation, routed to the specialist best suited to each question.</p></div>
        <label className="profile-select"><span>Answer for</span><select value={profile} onChange={(event) => setProfile(event.target.value)}><option value="beginner">Beginner investor</option><option value="intermediate">Intermediate investor</option><option value="expert">Expert investor</option></select></label>
      </section>

      <section className="finscope-grid">
        <div className="card assistant-card">
          <div className="assistant-head">
            <div className="assistant-identity"><span><Sparkles size={20} /></span><div><strong>FinScope advisor</strong><small><i /> Online · auto-routing</small></div></div>
            <span className="session-tag">Session {sessionId.slice(-6)}</span>
          </div>

          <div className="advisor-messages">
            {!messages.length && (
              <div className="conversation-start">
                <span className="conversation-orb"><Sparkles size={27} /></span>
                <h2>What are you evaluating today?</h2>
                <p>Ask a question or start with one of these common research paths.</p>
                <div className="starter-grid">{starters.map((starter) => <button key={starter.title} onClick={() => void ask(undefined, starter.prompt)}>{starter.icon}<span><strong>{starter.title}</strong><small>{starter.prompt}</small></span></button>)}</div>
              </div>
            )}
            {messages.map((message, index) => (
              <div className={`advisor-message ${message.role}`} key={index}>
                {message.role === "assistant" && <span className="message-avatar"><Bot size={17} /></span>}
                <div>{message.agent && <small>{message.agent}<em>{message.intent}</em></small>}<p>{message.text}</p></div>
              </div>
            ))}
            {busy && <div className="advisor-message assistant"><span className="message-avatar"><Bot size={17} /></span><div><small>Routing your question</small><p><Loader label="Specialist agent is thinking" /></p></div></div>}
          </div>

          <form className="advisor-composer" onSubmit={(event) => void ask(event)}>
            <textarea value={question} onChange={(event) => setQuestion(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); event.currentTarget.form?.requestSubmit(); } }} placeholder="Ask about a company, market, document, or portfolio…" rows={2} />
            <div><span>FinScope may make mistakes. Verify material financial decisions.</span><button className="send-button" disabled={busy || !question.trim()} aria-label="Send question" title="Send question"><Send size={18} /></button></div>
          </form>
        </div>

        <aside className="finscope-tools">
          <div className="card tool-card">
            <div className="tool-heading"><span><FileSearch size={18} /></span><div><strong>Document analyzer</strong><small>PDF or DOCX → structured insights</small></div></div>
            <label className="compact-file"><input type="file" accept=".pdf,.docx" onChange={(event) => setDocumentFile(event.target.files?.[0] || null)} /><Upload size={18} /><span>{documentFile ? documentFile.name : "Choose document"}</span></label>
            <button className="button primary full" disabled={!documentFile || documentBusy} onClick={() => void analyzeDocument()}>{documentBusy ? <Loader label="Analyzing" /> : "Analyze in this session"}</button>
          </div>

          <div className="card tool-card news-tool">
            <div className="tool-heading"><span><Newspaper size={18} /></span><div><strong>Market wire</strong><small>Raw headlines, no model</small></div></div>
            <form className="symbol-form" onSubmit={loadNews}><input value={symbol} onChange={(event) => setSymbol(event.target.value.toUpperCase())} placeholder="AAPL:NASDAQ" /><button className="icon-button" title="Fetch headlines" disabled={newsBusy}>{newsBusy ? <span className="mini-spinner" /> : <Search size={17} />}</button></form>
            <div className="headline-list">{headlines.length ? headlines.slice(0, 5).map((headline, index) => <HeadlineItem key={index} item={headline} />) : <EmptyState icon={<Newspaper size={20} />} title="Your market wire" copy="Enter an exchange-qualified symbol to fetch live headlines." />}</div>
          </div>
        </aside>
      </section>
    </div>
  );
}

function HeadlineItem({ item }: { item: Headline }) {
  const title = String(item.article_title || item.title || "Market update");
  const source = String(item.source || item.publisher || "Market wire");
  const url = String(item.article_url || item.url || "");
  const timestamp = String(item.post_time_utc || item.published_at || item.date || "");
  const time = useMemo(() => { if (!timestamp) return "Latest"; const parsed = new Date(timestamp); return Number.isNaN(parsed.valueOf()) ? timestamp : parsed.toLocaleDateString("en", { month: "short", day: "numeric" }); }, [timestamp]);
  const body = <><span><strong>{title}</strong><small>{source} · {time}</small></span>{url && <ArrowUpRight size={15} />}</>;
  return url ? <a href={url} target="_blank" rel="noreferrer">{body}</a> : <div>{body}</div>;
}
