"use client";

import { useState } from "react";
import ChatWindow from "./components/ChatWindow";
import RepoInput from "./components/RepoInput";

export default function ChatPage() {
  const [repoUrl, setRepoUrl] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);

  return (
    <main className="mx-auto flex h-screen max-w-5xl flex-col p-4">
      <header className="flex items-center justify-between py-2">
        <h1 className="text-xl font-bold">Codebase Q&A</h1>
        <RepoInput value={repoUrl} onChange={setRepoUrl} />
      </header>
      <ChatWindow repoUrl={repoUrl} sessionId={sessionId} onSessionChange={setSessionId} />
    </main>
  );
}