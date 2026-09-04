// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ChatWindow from "../app/chat/components/ChatWindow";
import * as api from "@/lib/api";

vi.mock("@/lib/api", () => ({
  askStream: vi.fn(),
  ask: vi.fn(),
  indexRepo: vi.fn(),
  indexStatus: vi.fn(),
  pollIndex: vi.fn(),
  getEvalRuns: vi.fn(),
}));

beforeEach(() => {
  vi.mocked(api.askStream).mockImplementation(async function* () {
    yield { event: "node", data: { node: "planner" } };
    await new Promise((r) => setTimeout(r, 50));
    yield { event: "node", data: { node: "retrieve" } };
    yield { event: "token", data: { text: "Auth is " } };
    yield { event: "token", data: { text: "here" } };
    yield {
      event: "citations",
      data: [{ file_path: "src/auth/login.py", start_line: 1, end_line: 2, snippet: "def login" }],
    };
    yield { event: "done", data: { session_id: "s1" } };
  });
});

describe("ChatWindow", () => {
  it("streams tokens into the chat and reports the session", async () => {
    const onSession = vi.fn();
    render(
      <ChatWindow repoUrl="https://github.com/x/y" sessionId={null} onSessionChange={onSession} />,
    );

    const input = screen.getByPlaceholderText("Ask about the codebase...");
    await userEvent.type(input, "Where is auth?");
    fireEvent.click(screen.getByText("Send"));

    await waitFor(() => expect(screen.getByText(/planner/)).toBeTruthy());

    await waitFor(() => expect(screen.getByText("Auth is here")).toBeTruthy());
    expect(onSession).toHaveBeenCalledWith("s1");

    await waitFor(() => expect(screen.getByText("src/auth/login.py:1-2")).toBeTruthy());
  });
});