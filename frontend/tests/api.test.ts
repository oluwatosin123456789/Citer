import { describe, it, expect, vi, afterEach } from "vitest";
import { ask, askStream, pollIndex } from "../lib/api";

function sseResponse(text: string): Response {
  const stream = new ReadableStream({
    start(controller) {
      controller.enqueue(new TextEncoder().encode(text));
      controller.close();
    },
  });
  return new Response(stream, { status: 200, headers: { "content-type": "text/event-stream" } });
}

function jsonResponse(body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "content-type": "application/json" },
  });
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("askStream", () => {
  it("yields parsed SSE events in order", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        sseResponse(
          'event: node\ndata: {"node":"planner"}\n\nevent: token\ndata: {"text":"hi"}\n\nevent: done\ndata: {"session_id":"s1"}\n\n',
        ),
      ),
    );

    const events = [];
    for await (const ev of askStream("question")) events.push(ev);
    expect(events.map((e) => e.event)).toEqual(["node", "token", "done"]);
  });

  it("throws when the server responds with an error status", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(null, { status: 500 })));
    await expect(async () => {
      for await (const _ of askStream("q")) {
        // drain
      }
    }).rejects.toThrow(/500/);
  });

  it("sends the expected JSON body", async () => {
    const fetchMock = vi.fn().mockResolvedValue(sseResponse("event: done\ndata: {\"session_id\":\"s\"}\n\n"));
    vi.stubGlobal("fetch", fetchMock);

    for await (const _ of askStream("q1", "sess", "https://github.com/x/y")) {
      // drain
    }

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toContain("/ask");
    expect(JSON.parse(init.body)).toEqual({
      question: "q1",
      session_id: "sess",
      repo_url: "https://github.com/x/y",
    });
  });
});

describe("ask", () => {
  it("collapses the stream into a final answer", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        sseResponse(
          'event: token\ndata: {"text":"Hel"}\n\nevent: token\ndata: {"text":"lo"}\n\nevent: done\ndata: {"session_id":"s1"}\n\n',
        ),
      ),
    );
    const result = await ask("q");
    expect(result).toEqual({ session_id: "s1", answer: "Hello", citations: [] });
  });
});

describe("pollIndex", () => {
  it("polls status until done and reports progress", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(jsonResponse({ task_id: "t1", status: "queued" }))
        .mockResolvedValueOnce(jsonResponse({ task_id: "t1", status: "embedding", progress: 0.5 }))
        .mockResolvedValueOnce(jsonResponse({ task_id: "t1", status: "done", progress: 1.0 })),
    );

    const onProgress = vi.fn();
    const result = await pollIndex("https://github.com/x/y", onProgress);

    expect(result.status).toBe("done");
    expect(onProgress).toHaveBeenCalledTimes(2);
    expect(onProgress.mock.calls[0][0].status).toBe("embedding");
  });

  it("stops polling on failure", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(jsonResponse({ task_id: "t2", status: "queued" }))
        .mockResolvedValueOnce(jsonResponse({ task_id: "t2", status: "failed", message: "boom" })),
    );
    const result = await pollIndex("https://github.com/x/y");
    expect(result.status).toBe("failed");
  });
});