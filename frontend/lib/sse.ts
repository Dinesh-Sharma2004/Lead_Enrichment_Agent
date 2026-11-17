import {
  SSEEventStarted,
  SSEEventDomainStarted,
  SSEEventDomainCompleted,
  SSEEventDomainFailed,
  SSEEventCompleted,
} from "./types";

export interface StreamCallbacks {
  onStarted?: (data: SSEEventStarted) => void;
  onDomainStarted?: (data: SSEEventDomainStarted) => void;
  onDomainCompleted?: (data: SSEEventDomainCompleted) => void;
  onDomainFailed?: (data: SSEEventDomainFailed) => void;
  onCompleted?: (data: SSEEventCompleted) => void;
  onError?: (errorMessage: string) => void;
}

/**
 * Connects to the SSE endpoint /api/enrich/stream using fetch and ReadableStream reader.
 * Correctly buffers incoming network chunks to parse SSE frames split across boundaries.
 */
export async function streamEnrichment(
  domains: string[],
  callbacks: StreamCallbacks,
  signal?: AbortSignal
): Promise<void> {
  let response: Response;

  try {
    response = await fetch("/api/enrich/stream", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ domains }),
      signal,
      cache: "no-store",
    });
  } catch (err: unknown) {
    if (signal?.aborted) {
      callbacks.onError?.("Enrichment request was cancelled by user.");
      return;
    }
    const msg = err instanceof Error ? err.message : "Failed to connect to backend.";
    callbacks.onError?.(`Network error: ${msg}`);
    return;
  }

  if (!response.ok) {
    let errorDetail = `Server returned HTTP ${response.status}`;
    try {
      const errJson = await response.json();
      if (errJson && errJson.detail) {
        errorDetail = errJson.detail;
      }
    } catch {
      // ignore JSON parse failure on non-JSON error
    }
    callbacks.onError?.(errorDetail);
    return;
  }

  if (!response.body) {
    callbacks.onError?.("Response body is empty or streaming is unsupported by client.");
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // SSE frames are delimited by double newline
      let delimiterIndex: number;
      while ((delimiterIndex = buffer.indexOf("\n\n")) !== -1) {
        const rawEvent = buffer.slice(0, delimiterIndex);
        buffer = buffer.slice(delimiterIndex + 2);

        parseAndDispatchEvent(rawEvent, callbacks);
      }
    }

    // Flush any remaining buffered frame
    if (buffer.trim()) {
      parseAndDispatchEvent(buffer, callbacks);
    }
  } catch (err: unknown) {
    if (signal?.aborted) {
      callbacks.onError?.("Enrichment stream aborted by user.");
    } else {
      const msg = err instanceof Error ? err.message : "Error reading response stream";
      callbacks.onError?.(`Streaming connection interrupted: ${msg}`);
    }
  } finally {
    try {
      reader.releaseLock();
    } catch {
      // reader might already be closed
    }
  }
}

function parseAndDispatchEvent(rawEvent: string, callbacks: StreamCallbacks) {
  const lines = rawEvent.split("\n");
  let eventType = "message";
  let dataStr = "";

  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith("event:")) {
      eventType = trimmed.slice(6).trim();
    } else if (trimmed.startsWith("data:")) {
      dataStr = trimmed.slice(5).trim();
    }
  }

  if (!dataStr) return;

  try {
    const data = JSON.parse(dataStr);

    switch (eventType) {
      case "started":
        callbacks.onStarted?.(data as SSEEventStarted);
        break;
      case "domain_started":
        callbacks.onDomainStarted?.(data as SSEEventDomainStarted);
        break;
      case "domain_completed":
        callbacks.onDomainCompleted?.(data as SSEEventDomainCompleted);
        break;
      case "domain_failed":
        callbacks.onDomainFailed?.(data as SSEEventDomainFailed);
        break;
      case "completed":
        callbacks.onCompleted?.(data as SSEEventCompleted);
        break;
      default:
        break;
    }
  } catch (parseError) {
    console.error("Failed to parse SSE JSON payload:", dataStr, parseError);
  }
}

