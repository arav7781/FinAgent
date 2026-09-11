"use client";

import { LoaderCircle, X } from "lucide-react";

export function Loader({ label = "Working" }: { label?: string }) {
  return (
    <span className="loader-label">
      <LoaderCircle size={15} className="spin" /> {label}
    </span>
  );
}

export function EmptyState({ icon, title, copy }: { icon: React.ReactNode; title: string; copy: string }) {
  return (
    <div className="empty-state">
      <span className="empty-icon">{icon}</span>
      <strong>{title}</strong>
      <p>{copy}</p>
    </div>
  );
}

export function Toast({ message, kind = "success", onClose }: { message: string; kind?: "success" | "error"; onClose: () => void }) {
  return (
    <div className={`toast ${kind}`} role="status">
      <span className="toast-dot" />
      <span>{message}</span>
      <button className="icon-button" onClick={onClose} aria-label="Dismiss notification" title="Dismiss">
        <X size={16} />
      </button>
    </div>
  );
}

export const formatDate = (value?: string | null) => {
  if (!value) return "Not yet";
  return new Intl.DateTimeFormat("en", { month: "short", day: "numeric", year: "numeric" }).format(new Date(value));
};

export const errorMessage = (error: unknown) => error instanceof Error ? error.message : "Something went wrong";
