import { useState, useCallback } from "react";
import { streamQuery } from "@/services/api";
import type { QueryRequest, NoteReference, StreamChunk } from "@/types";

interface StreamingQueryState {
  answer: string;
  sources: NoteReference[];
  metadata: StreamChunk["metadata"] | null;
  isStreaming: boolean;
  error: string | null;
}

export function useStreamingQuery() {
  const [state, setState] = useState<StreamingQueryState>({
    answer: "",
    sources: [],
    metadata: null,
    isStreaming: false,
    error: null,
  });

  const execute = useCallback(async (request: QueryRequest) => {
    setState({
      answer: "",
      sources: [],
      metadata: null,
      isStreaming: true,
      error: null,
    });

    try {
      for await (const chunk of streamQuery(request)) {
        switch (chunk.type) {
          case "content":
            if (chunk.content) {
              setState((prev) => ({
                ...prev,
                answer: prev.answer + chunk.content,
              }));
            }
            break;

          case "sources":
            if (chunk.sources) {
              setState((prev) => ({
                ...prev,
                sources: chunk.sources!,
              }));
            }
            break;

          case "metadata":
            if (chunk.metadata) {
              setState((prev) => ({
                ...prev,
                metadata: chunk.metadata,
              }));
            }
            break;

          case "error":
            setState((prev) => ({
              ...prev,
              error: chunk.error || "Unknown error",
              isStreaming: false,
            }));
            return;

          case "done":
            setState((prev) => ({
              ...prev,
              isStreaming: false,
            }));
            return;
        }
      }
    } catch (error) {
      setState((prev) => ({
        ...prev,
        error: error instanceof Error ? error.message : "Query failed",
        isStreaming: false,
      }));
    }
  }, []);

  const reset = useCallback(() => {
    setState({
      answer: "",
      sources: [],
      metadata: null,
      isStreaming: false,
      error: null,
    });
  }, []);

  return {
    ...state,
    execute,
    reset,
  };
}
