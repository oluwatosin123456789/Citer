import { parseSSE, type SSEEvent } from "./sse";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

export type Citation = {
  file_path: string;
  start_line: number;
  end_line: number;
  snippet: string;
};

export type IndexTask = {
  task_id: string;
  status: string;
  progress: number;
  message?: string;
};

type EventMap = {
  node: { node: string };
  token: { text: string };
  done: { session_id: string };
  error: { message: string };
};

/**
 * Stream a question answer. Yields one SSEEvent per server message:
 * `node` (agent step), `token` (answer text), `done` (final, with session_id).
 */
export async function* askStream(
  question: string,
  sessionId?: string,
  repoUrl?: string,
): AsyncGenerator<SSEEvent> {
  const res = await fetch(`${API_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, session_id: sessionId, repo_url: repoUrl }),
  });

  if (!res.ok || !res.body) {
    throw new Error(`ask failed with status ${res.status}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();

  async function* readChunks(): AsyncGenerator<string> {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      yield decoder.decode(value, { stream: true });
    }
  }

  yield* parseSSE(readChunks());
}

/** Collapse a stream into the final AskResult (for non-streaming callers/tests). */
export async function ask(question: string, sessionId?: string, repoUrl?: string) {
  let answer = "";
  let citations: Citation[] = [];
  let doneSessionId: string | undefined;
  for await (const ev of askStream(question, sessionId, repoUrl)) {
    if (ev.event === "token") {
      answer += (ev.data as EventMap["token"]).text;
    } else if (ev.event === "done") {
      doneSessionId = (ev.data as EventMap["done"]).session_id;
    }
  }
  return { session_id: doneSessionId ?? "", answer, citations };
}

export async function indexRepo(repoUrl: string): Promise<IndexTask> {
  const res = await fetch(`${API_URL}/index`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repo_url: repoUrl }),
  });
  return res.json();
}

export async function indexStatus(taskId: string): Promise<IndexTask> {
  const res = await fetch(`${API_URL}/index/status/${taskId}`);
  return res.json();
}

/** Poll indexing until done/failed (used by the UI to show progress). */
export async function pollIndex(repoUrl: string, onProgress?: (task: IndexTask) => void) {
  const task = await indexRepo(repoUrl);
  for (;;) {
    const current = await indexStatus(task.task_id);
    onProgress?.(current);
    if (current.status === "done" || current.status === "failed") {
      return current;
    }
    await new Promise((r) => setTimeout(r, 1000));
  }
}

export async function getEvalRuns() {
  const res = await fetch(`${API_URL}/eval/runs`);
  return res.json();
}