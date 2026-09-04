import { describe, it, expect } from "vitest";
import { parseSSE } from "../lib/sse";

async function collect(chunks: string[]) {
  async function* feed() {
    for (const c of chunks) yield c;
  }
  const events = [];
  for await (const ev of parseSSE(feed())) events.push(ev);
  return events;
}

describe("parseSSE", () => {
  it("parses a single event", async () => {
    const events = await collect(["event: token\ndata: {\"text\":\"hi\"}\n\n"]);
    expect(events).toEqual([{ event: "token", data: { text: "hi" } }]);
  });

  it("parses multiple events in one chunk", async () => {
    const events = await collect([
      "event: node\ndata: {\"node\":\"planner\"}\n\nevent: token\ndata: {\"text\":\"a\"}\n\n",
    ]);
    expect(events.map((e) => e.event)).toEqual(["node", "token"]);
  });

  it("joins a split event across chunks", async () => {
    const events = await collect([
      'event: token\ndata: {"te',
      'xt":"world"}\n\n',
    ]);
    expect(events).toEqual([{ event: "token", data: { text: "world" } }]);
  });

  it("keeps non-JSON data as a raw string", async () => {
    const events = await collect(["event: message\ndata: plain text\n\n"]);
    expect(events).toEqual([{ event: "message", data: "plain text" }]);
  });

  it("trims leading space after data:", async () => {
    const events = await collect(["event: x\ndata: {\"a\":1}\n\n"]);
    expect(events[0].data).toEqual({ a: 1 });
  });

  it("emits pending event at stream end without trailing blank line", async () => {
    const events = await collect(['event: done\ndata: {"session_id":"s1"}']);
    expect(events).toEqual([{ event: "done", data: { session_id: "s1" } }]);
  });
});