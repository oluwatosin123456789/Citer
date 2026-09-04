export type SSEEvent = {
  event: string;
  data: unknown;
};

/**
 * Parse Server-Sent Events from a stream of text chunks.
 *
 * SSE wire format (per event):
 *   event: node
 *   data: {"node":"planner"}
 *   <blank line>
 *
 * Chunks may split lines at any byte boundary, so a buffer reassembles
 * partial lines before they are processed. A `data:` payload is
 * JSON-parsed when possible, otherwise kept as a raw string.
 */
export async function* parseSSE(chunks: AsyncIterable<string>): AsyncGenerator<SSEEvent> {
  let event = "message";
  let dataLines: string[] = [];
  let buffer = "";

  const processLine = (line: string) => {
    if (line === "") {
      if (dataLines.length > 0) {
        const raw = dataLines.join("\n");
        let data: unknown = raw;
        try {
          data = JSON.parse(raw);
        } catch {
          // keep raw string
        }
        const emitted: SSEEvent = { event, data };
        dataLines = [];
        event = "message";
        return emitted;
      }
    } else if (line.startsWith("event:")) {
      event = line.slice("event:".length).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice("data:".length).trimStart());
    }
    return undefined;
  };

  for await (const chunk of chunks) {
    buffer += chunk;
    let newline: number;
    while ((newline = buffer.indexOf("\n")) !== -1) {
      const line = buffer.slice(0, newline);
      buffer = buffer.slice(newline + 1);
      const emitted = processLine(line);
      if (emitted) yield emitted;
    }
  }

  if (buffer !== "") {
    const emitted = processLine(buffer);
    if (emitted) yield emitted;
  }

  if (dataLines.length > 0) {
    const raw = dataLines.join("\n");
    let data: unknown = raw;
    try {
      data = JSON.parse(raw);
    } catch {
      // keep raw string
    }
    yield { event, data };
  }
}