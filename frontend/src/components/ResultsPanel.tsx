import { FileText, Clock, Coins, Brain, Loader2, ExternalLink, Zap } from "lucide-react";
import { Markdown } from "./Markdown";
import type { NoteReference, StreamChunk } from "@/types";

interface ResultsPanelProps {
  answer: string;
  sources: NoteReference[];
  metadata: StreamChunk["metadata"] | null;
  isStreaming: boolean;
  error: string | null;
}

export function ResultsPanel({
  answer,
  sources,
  metadata,
  isStreaming,
  error,
}: ResultsPanelProps) {
  if (error) {
    return (
      <div className="card p-6 border-red-200 dark:border-red-900/50 bg-red-50 dark:bg-red-900/20 animate-fade-in">
        <h3 className="font-semibold text-red-800 dark:text-red-300 mb-2 flex items-center gap-2">
          <span className="p-1 rounded-full bg-red-100 dark:bg-red-900/50">
            <Zap className="h-4 w-4" />
          </span>
          Error
        </h3>
        <p className="text-red-700 dark:text-red-400">{error}</p>
      </div>
    );
  }

  if (!answer && !isStreaming) {
    return (
      <div className="card p-12 text-center animate-fade-in">
        <div className="relative inline-block mb-6">
          <Brain className="h-16 w-16 text-[rgb(var(--muted-foreground))]/30" />
          <div className="absolute inset-0 bg-obsidian-500/10 rounded-full blur-2xl" />
        </div>
        <p className="text-[rgb(var(--muted-foreground))] text-lg">
          Ask a question to search your notes
        </p>
        <p className="text-[rgb(var(--muted-foreground))]/60 text-sm mt-2">
          Your AI assistant will find relevant information across all your Obsidian notes
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Answer */}
      <div className="card p-6">
        <h3 className="font-semibold text-[rgb(var(--foreground))] mb-4 flex items-center gap-2">
          <span className="p-1.5 rounded-lg bg-obsidian-100 dark:bg-obsidian-900/50">
            <Brain className="h-4 w-4 text-obsidian-600 dark:text-obsidian-400" />
          </span>
          Answer
          {isStreaming && (
            <Loader2 className="h-4 w-4 animate-spin text-obsidian-500 ml-auto" />
          )}
        </h3>
        <div className="markdown-content">
          {answer ? (
            <div className="relative">
              <Markdown content={answer} />
              {isStreaming && (
                <span className="inline-block w-2 h-5 bg-obsidian-500 animate-pulse ml-0.5 rounded-sm align-middle" />
              )}
            </div>
          ) : (
            <span className="text-[rgb(var(--muted-foreground))] animate-pulse">
              Generating response...
            </span>
          )}
        </div>
      </div>

      {/* Sources */}
      {sources.length > 0 && (
        <div className="card p-6">
          <h3 className="font-semibold text-[rgb(var(--foreground))] mb-4 flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-obsidian-100 dark:bg-obsidian-900/50">
              <FileText className="h-4 w-4 text-obsidian-600 dark:text-obsidian-400" />
            </span>
            Sources
            <span className="badge-primary ml-1">{sources.length}</span>
          </h3>
          <div className="space-y-3">
            {sources.map((source, index) => (
              <div
                key={index}
                className="p-4 rounded-xl bg-[rgb(var(--muted))] border border-[rgb(var(--border))] hover:border-obsidian-300 dark:hover:border-obsidian-700 transition-all duration-200 group"
              >
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      {source.obsidian_url ? (
                        <a
                          href={source.obsidian_url}
                          className="font-medium text-obsidian-600 dark:text-obsidian-400 hover:text-obsidian-800 dark:hover:text-obsidian-300 flex items-center gap-1.5 group/link"
                          title="Open in Obsidian"
                        >
                          <span className="group-hover/link:underline">{source.title}</span>
                          <ExternalLink className="h-3.5 w-3.5 flex-shrink-0 opacity-60 group-hover/link:opacity-100" />
                        </a>
                      ) : (
                        <h4 className="font-medium text-[rgb(var(--foreground))]">
                          {source.title}
                        </h4>
                      )}
                    </div>
                    <p className="text-xs text-[rgb(var(--muted-foreground))] truncate mt-0.5">
                      {source.folder && (
                        <span className="text-obsidian-500 dark:text-obsidian-400">
                          {source.folder}
                        </span>
                      )}
                      {source.folder && " / "}
                      {source.note_path}
                    </p>
                  </div>
                  <span className="badge-primary flex-shrink-0">
                    {Math.round(source.similarity_score * 100)}%
                  </span>
                </div>
                <p className="text-sm text-[rgb(var(--muted-foreground))] line-clamp-3 leading-relaxed">
                  {source.relevant_excerpt}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Metadata */}
      {metadata && (
        <div className="card p-4">
          <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-sm">
            <div className="flex items-center gap-2 text-[rgb(var(--muted-foreground))]">
              <Brain className="h-4 w-4" />
              <span className="text-[rgb(var(--foreground))] font-medium">
                {metadata.model_used}
              </span>
              <span className="badge-primary text-xs">
                {metadata.complexity_used}
              </span>
            </div>
            <div className="flex items-center gap-2 text-[rgb(var(--muted-foreground))]">
              <Clock className="h-4 w-4" />
              <span className="text-[rgb(var(--foreground))] font-medium">
                {(metadata.latency_ms / 1000).toFixed(2)}s
              </span>
            </div>
            <div className="flex items-center gap-2 text-[rgb(var(--muted-foreground))]">
              <Coins className="h-4 w-4" />
              <span className="text-obsidian-600 dark:text-obsidian-400 font-medium">
                ${parseFloat(metadata.total_cost).toFixed(6)}
              </span>
            </div>
            <div className="text-[rgb(var(--muted-foreground))]">
              <span className="text-[rgb(var(--foreground))] font-medium">
                {(metadata.input_tokens + metadata.output_tokens).toLocaleString()}
              </span>
              {" "}tokens
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
