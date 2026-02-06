import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Settings, BarChart3, Database, Sparkles } from "lucide-react";
import { QueryInput } from "@/components/QueryInput";
import { ResultsPanel } from "@/components/ResultsPanel";
import { CostDashboard } from "@/components/CostDashboard";
import { SettingsPanel } from "@/components/SettingsPanel";
import { IndexStatus } from "@/components/IndexStatus";
import { ThemeToggle } from "@/components/ThemeToggle";
import { useStreamingQuery } from "@/hooks/useStreamingQuery";
import { useTheme } from "@/hooks/useTheme";
import {
  listFolders,
  getCostSummary,
} from "@/services/api";
import type { QueryComplexity } from "@/types";

type ModalType = "costs" | "settings" | "index" | null;

function App() {
  const [activeModal, setActiveModal] = useState<ModalType>(null);
  const { resolvedTheme } = useTheme();

  const streamingQuery = useStreamingQuery();

  // Fetch folders for filter
  const { data: foldersData, refetch: refetchFolders, isFetching: isFetchingFolders } = useQuery({
    queryKey: ["folders"],
    queryFn: listFolders,
  });

  // Fetch cost summary for status bar
  const { data: costSummary } = useQuery({
    queryKey: ["costSummary"],
    queryFn: getCostSummary,
    refetchInterval: 10000,
  });

  const handleQuery = (
    question: string,
    complexity: QueryComplexity,
    folders: string[]
  ) => {
    streamingQuery.execute({
      question,
      complexity,
      folders: folders.length > 0 ? folders : undefined,
    });
  };

  return (
    <div className={`min-h-screen ${resolvedTheme === "dark" ? "gradient-dark" : "gradient-light"}`}>
      {/* Header */}
      <header className="bg-[rgb(var(--card))]/80 backdrop-blur-md border-b border-[rgb(var(--border))] sticky top-0 z-40">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="relative">
              <Sparkles className="h-7 w-7 text-obsidian-500" />
              <div className="absolute inset-0 bg-obsidian-500/20 rounded-full blur-md" />
            </div>
            <h1 className="text-xl font-bold text-[rgb(var(--foreground))]">
              Obsidian AI
            </h1>
          </div>

          <div className="flex items-center gap-3">
            <ThemeToggle />

            <div className="h-6 w-px bg-[rgb(var(--border))]" />

            <button
              onClick={() => setActiveModal("index")}
              className="btn-ghost p-2.5"
              title="Notes Index"
            >
              <Database className="h-5 w-5" />
            </button>
            <button
              onClick={() => setActiveModal("costs")}
              className="btn-ghost p-2.5"
              title="Cost Dashboard"
            >
              <BarChart3 className="h-5 w-5" />
            </button>
            <button
              onClick={() => setActiveModal("settings")}
              className="btn-ghost p-2.5"
              title="Settings"
            >
              <Settings className="h-5 w-5" />
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-8 pb-24">
        <div className="space-y-6">
          {/* Query Input */}
          <div className="card p-6">
            <QueryInput
              onSubmit={handleQuery}
              isLoading={streamingQuery.isStreaming}
              folders={foldersData?.folders || []}
              onRefreshFolders={() => refetchFolders()}
              isRefreshingFolders={isFetchingFolders}
            />
          </div>

          {/* Results */}
          <ResultsPanel
            answer={streamingQuery.answer}
            sources={streamingQuery.sources}
            metadata={streamingQuery.metadata}
            isStreaming={streamingQuery.isStreaming}
            error={streamingQuery.error}
          />
        </div>
      </main>

      {/* Status Bar */}
      {costSummary && costSummary.total_queries > 0 && (
        <footer className="fixed bottom-0 left-0 right-0 bg-[rgb(var(--card))]/80 backdrop-blur-md border-t border-[rgb(var(--border))] py-3 px-4">
          <div className="max-w-4xl mx-auto flex items-center justify-center gap-6 text-sm">
            <div className="flex items-center gap-2">
              <span className="text-[rgb(var(--muted-foreground))]">Session:</span>
              <span className="font-medium text-[rgb(var(--foreground))]">
                {costSummary.total_queries} queries
              </span>
            </div>
            <div className="h-4 w-px bg-[rgb(var(--border))]" />
            <div className="flex items-center gap-2">
              <span className="text-[rgb(var(--muted-foreground))]">Cost:</span>
              <span className="font-medium text-obsidian-600 dark:text-obsidian-400">
                ${parseFloat(costSummary.total_cost).toFixed(4)}
              </span>
            </div>
            <div className="h-4 w-px bg-[rgb(var(--border))]" />
            <div className="flex items-center gap-2">
              <span className="text-[rgb(var(--muted-foreground))]">Tokens:</span>
              <span className="font-medium text-[rgb(var(--foreground))]">
                {(
                  costSummary.total_input_tokens + costSummary.total_output_tokens
                ).toLocaleString()}
              </span>
            </div>
          </div>
        </footer>
      )}

      {/* Modals */}
      {activeModal === "costs" && (
        <CostDashboard onClose={() => setActiveModal(null)} />
      )}
      {activeModal === "settings" && (
        <SettingsPanel onClose={() => setActiveModal(null)} />
      )}
      {activeModal === "index" && (
        <IndexStatus onClose={() => setActiveModal(null)} />
      )}
    </div>
  );
}

export default App;
