"use client";

import { useState } from "react";
import { ask, type Citation } from "@/lib/api";
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

  async function send() {
    const question = input.trim();
    if (!question || loading) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", content: question }]);
    setLoading(true);

    try {
      const res = await ask(question, sessionId ?? undefined, repoUrl || undefined);
      onSessionChange(res.session_id);
      setMessages((m) => [...m, { role: "assistant", content: res.answer, citations: res.citations }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <div className="flex-1 space-y-4 overflow-y-auto py-4">
        {messages.map((m, i) => (
          <Message key={i} message={m} />
        ))}
        {loading && <div className="text-sm text-zinc-500">Thinking...</div>}
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