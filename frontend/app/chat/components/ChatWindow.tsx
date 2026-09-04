"use client";

import { useState } from "react";
import { askStream, type Citation } from "@/lib/api";
import Message, { type ChatMessage } from "./Message";

export default function ChatWindow({
  repoUrl,
  sessionId,
  onSessionChange,
}: {
  repoUrl: string;
  sessionId: string | null;
  onSessionChange: (id: string) => void;
}) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [steps, setSteps] = useState<string[]>([]);
  const [liveAnswer, setLiveAnswer] = useState("");
  const [liveCitations, setLiveCitations] = useState<Citation[]>([]);

  async function send() {
    const question = input.trim();
    if (!question || loading) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", content: question }]);
    setLoading(true);
    setSteps([]);
    setLiveAnswer("");
    setLiveCitations([]);

    let answer = "";
    let citations: Citation[] = [];
    try {
      for await (const ev of askStream(question, sessionId ?? undefined, repoUrl || undefined)) {
        if (ev.event === "node") {
          setSteps((s) => [...s, (ev.data as { node: string }).node]);
        } else if (ev.event === "token") {
          answer += (ev.data as { text: string }).text;
          setLiveAnswer(answer);
        } else if (ev.event === "citations") {
          citations = ev.data as Citation[];
          setLiveCitations(citations);
        } else if (ev.event === "done") {
          onSessionChange((ev.data as { session_id: string }).session_id);
        }
      }
      setMessages((m) => [...m, { role: "assistant", content: answer, citations }]);
    } finally {
      setLiveAnswer("");
      setLiveCitations([]);
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <div className="flex-1 space-y-4 overflow-y-auto py-4">
        {messages.map((m, i) => (
          <Message key={i} message={m} />
        ))}
        {loading && (
          <div className="rounded-lg bg-zinc-800 px-4 py-3">
            {steps.length > 0 && (
              <div className="mb-1 text-xs text-zinc-400">
                {steps.map((s) => (
                  <span key={s} className="mr-2">
                    <span className="text-blue-400">▸</span> {s}
                  </span>
                ))}
              </div>
            )}
            <p className="whitespace-pre-wrap text-zinc-100">{liveAnswer}</p>
            {liveAnswer === "" && <span className="text-sm text-zinc-500">Thinking...</span>}
          </div>
        )}
      </div>
      <div className="flex gap-2 border-t border-zinc-800 py-3">
        <input
          className="flex-1 rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm"
          placeholder="Ask about the codebase..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
        />
        <button
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium hover:bg-blue-500"
          onClick={send}
          disabled={loading}
        >
          Send
        </button>
      </div>
    </div>
  );
}