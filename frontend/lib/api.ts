export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

export type Citation = {
  file_path: string;
  start_line: number;
  end_line: number;
  snippet: string;
};

export type AskResponse = {
  session_id: string;
  answer: string;
  citations: Citation[];
};

export async function indexRepo(repoUrl: string) {
  const res = await fetch(`${API_URL}/index`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repo_url: repoUrl }),
  });
  return res.json();
}

export async function ask(question: string, sessionId?: string, repoUrl?: string) {
  const res = await fetch(`${API_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, session_id: sessionId, repo_url: repoUrl }),
  });
  return (await res.json()) as AskResponse;
}

export async function getEvalRuns() {
  const res = await fetch(`${API_URL}/eval/runs`);
  return res.json();
}