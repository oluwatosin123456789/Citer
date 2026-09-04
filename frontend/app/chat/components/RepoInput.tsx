"use client";

import { useState } from "react";
import { pollIndex } from "@/lib/api";

export default function RepoInput({
  value,
  onChange,
}: {
  value: string;
  onChange: (v: string) => void;
}) {
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleIndex() {
    setBusy(true);
    setStatus("starting...");
    try {
      await pollIndex(value, (t) => {
        const msg = t.message ? ` - ${t.message}` : "";
        setStatus(`${t.status}${msg}`);
      });
    } catch {
      setStatus("failed to index");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex items-center gap-2">
      <input
        className="w-80 rounded-md border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-sm"
        placeholder="https://github.com/owner/repo"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
      <button
        className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium hover:bg-blue-500 disabled:opacity-50"
        onClick={handleIndex}
        disabled={busy || !value}
      >
        Index
      </button>
      {status && <span className="text-xs text-zinc-400">{status}</span>}
    </div>
  );
}