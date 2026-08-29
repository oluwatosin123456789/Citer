"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Citation } from "@/lib/api";

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
};

export default function Message({ message }: { message: ChatMessage }) {
  return (
    <div className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
      <div className={`max-w-[85%] rounded-lg px-4 py-3 ${message.role === "user" ? "bg-blue-600" : "bg-zinc-800"}`}>
        {message.role === "assistant" ? (
          <>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
            {message.citations && message.citations.length > 0 && (
              <div className="mt-2 border-t border-zinc-700 pt-2">
                <div className="mb-1 text-xs font-semibold text-zinc-400">Citations</div>
                {message.citations.map((c, i) => (
                  <CitationBlock key={i} citation={c} />
                ))}
              </div>
            )}
          </>
        ) : (
          <p className="whitespace-pre-wrap">{message.content}</p>
        )}
      </div>
    </div>
  );
}

function CitationBlock({ citation }: { citation: Citation }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="mb-1">
      <button
        className="text-xs text-blue-400 underline hover:text-blue-300"
        onClick={() => setOpen((o) => !o)}
      >
        {citation.file_path}:{citation.start_line}-{citation.end_line}
      </button>
      {open && (
        <pre className="mt-1 overflow-x-auto rounded bg-zinc-900 p-2 text-xs text-zinc-300">
          {citation.snippet}
        </pre>
      )}
    </div>
  );
}