import { useCallback, useRef, useState } from "react";
import type { NavigationMetrics, NavigationStep, ThoughtEvent } from "../types/navigation";

interface SSEState {
  steps: NavigationStep[];
  thoughts: ThoughtEvent[];
  status: "idle" | "connecting" | "running" | "completed" | "error";
  metrics: NavigationMetrics | null;
  error: string | null;
}

export function useSSE() {
  const [state, setState] = useState<SSEState>({
    steps: [],
    thoughts: [],
    status: "idle",
    metrics: null,
    error: null,
  });
  const abortRef = useRef<AbortController | null>(null);

  const start = useCallback((sessionId: string) => {
    // Abort any existing connection
    if (abortRef.current) {
      abortRef.current.abort();
    }
    const controller = new AbortController();
    abortRef.current = controller;

    setState({ steps: [], thoughts: [], status: "connecting", metrics: null, error: null });

    (async () => {
      try {
        const response = await fetch(`/api/navigate/${sessionId}/start`, {
          method: "POST",
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        if (!response.body) {
          throw new Error("No response body");
        }

        setState((prev) => ({ ...prev, status: "running" }));

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        // Iterative read loop — no recursion
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });

          // SSE messages are separated by double newlines
          let boundary = buffer.indexOf("\n\n");
          while (boundary !== -1) {
            const message = buffer.slice(0, boundary);
            buffer = buffer.slice(boundary + 2);

            // Process each line in the message
            for (const line of message.split("\n")) {
              if (!line.startsWith("data: ")) continue;
              try {
                const data = JSON.parse(line.slice(6));

                if (data.type === "complete") {
                  setState((prev) => ({
                    ...prev,
                    status: "completed",
                    metrics: data.metrics,
                  }));
                } else if (data.type === "error") {
                  setState((prev) => ({
                    ...prev,
                    status: "error",
                    error: data.message,
                  }));
                } else if (data.type === "thought") {
                  setState((prev) => ({
                    ...prev,
                    thoughts: [...prev.thoughts, data as ThoughtEvent],
                  }));
                } else if (data.step_number !== undefined) {
                  setState((prev) => ({
                    ...prev,
                    steps: [...prev.steps, data as NavigationStep],
                  }));
                }
              } catch {
                // Skip malformed JSON lines
              }
            }

            boundary = buffer.indexOf("\n\n");
          }
        }

        // Stream ended — mark completed if still running
        setState((prev) => ({
          ...prev,
          status: prev.status === "running" ? "completed" : prev.status,
        }));
      } catch (err: unknown) {
        if (err instanceof DOMException && err.name === "AbortError") return;
        setState((prev) => ({
          ...prev,
          status: "error",
          error: err instanceof Error ? err.message : "Stream failed",
        }));
      }
    })();
  }, []);

  const stop = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
    setState((prev) => ({ ...prev, status: "completed" }));
  }, []);

  return { ...state, start, stop };
}
