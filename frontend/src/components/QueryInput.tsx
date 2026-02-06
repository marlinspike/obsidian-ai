import { useState, FormEvent, KeyboardEvent } from "react";
import { Send, Loader2, Sparkles, Zap, Brain } from "lucide-react";
import { FolderSelector } from "./FolderSelector";
import type { QueryComplexity } from "@/types";

interface QueryInputProps {
  onSubmit: (question: string, complexity: QueryComplexity, folders: string[]) => void;
  isLoading: boolean;
  folders: string[];
  onRefreshFolders?: () => void;
  isRefreshingFolders?: boolean;
}

const complexityOptions = [
  { value: "auto" as const, label: "Auto", icon: Sparkles, description: "Let AI decide" },
  { value: "simple" as const, label: "Quick", icon: Zap, description: "Fast lookup" },
  { value: "complex" as const, label: "Deep", icon: Brain, description: "Detailed analysis" },
];

export function QueryInput({ onSubmit, isLoading, folders, onRefreshFolders, isRefreshingFolders }: QueryInputProps) {
  const [question, setQuestion] = useState("");
  const [complexity, setComplexity] = useState<QueryComplexity>("auto");
  const [selectedFolders, setSelectedFolders] = useState<string[]>([]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (question.trim() && !isLoading) {
      onSubmit(question.trim(), complexity, selectedFolders);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Query input */}
      <div className="relative">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about your notes..."
          className="input min-h-[120px] pr-14 resize-none text-base"
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={!question.trim() || isLoading}
          className="absolute right-3 bottom-3 btn-primary p-3 rounded-xl shadow-lg"
        >
          {isLoading ? (
            <Loader2 className="h-5 w-5 animate-spin" />
          ) : (
            <Send className="h-5 w-5" />
          )}
        </button>
      </div>

      {/* Options row */}
      <div className="flex flex-wrap items-center gap-4">
        {/* Complexity selector */}
        <div className="flex items-center gap-3">
          <span className="text-xs font-medium text-[rgb(var(--muted-foreground))] uppercase tracking-wider">
            Mode
          </span>
          <div className="flex rounded-xl border border-[rgb(var(--border))] overflow-hidden bg-[rgb(var(--muted))]">
            {complexityOptions.map(({ value, label, icon: Icon }) => (
              <button
                key={value}
                type="button"
                onClick={() => setComplexity(value)}
                className={`flex items-center gap-1.5 px-3 py-2 text-sm font-medium transition-all duration-200 ${
                  complexity === value
                    ? "bg-obsidian-600 text-white dark:bg-obsidian-500 shadow-sm"
                    : "text-[rgb(var(--muted-foreground))] hover:text-[rgb(var(--foreground))] hover:bg-[rgb(var(--card))]"
                }`}
              >
                <Icon className="h-3.5 w-3.5" />
                {label}
              </button>
            ))}
          </div>
        </div>

        {/* Divider */}
        <div className="h-8 w-px bg-[rgb(var(--border))]" />

        {/* Folder selector */}
        <div className="flex items-center gap-3">
          <span className="text-xs font-medium text-[rgb(var(--muted-foreground))] uppercase tracking-wider">
            Scope
          </span>
          <FolderSelector
            folders={folders}
            selectedFolders={selectedFolders}
            onSelectionChange={setSelectedFolders}
            onRefresh={onRefreshFolders}
            isRefreshing={isRefreshingFolders}
          />
        </div>
      </div>
    </form>
  );
}
