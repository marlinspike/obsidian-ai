import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { X, Database, RefreshCw, Loader2, Check, AlertTriangle, FileText, Zap, Info } from "lucide-react";
import { getIndexStatus, incrementalSync, fullRebuild } from "@/services/api";

interface IndexStatusProps {
  onClose: () => void;
}

export function IndexStatus({ onClose }: IndexStatusProps) {
  const queryClient = useQueryClient();
  const [syncResult, setSyncResult] = useState<{
    type: "sync" | "rebuild";
    result: {
      notes_added: number;
      notes_updated: number;
      notes_deleted: number;
      chunks_created: number;
      embedding_cost: string;
      duration_seconds: number;
    };
  } | null>(null);

  const { data: status, isLoading } = useQuery({
    queryKey: ["indexStatus"],
    queryFn: getIndexStatus,
    refetchInterval: 5000,
  });

  const syncMutation = useMutation({
    mutationFn: incrementalSync,
    onSuccess: (result) => {
      setSyncResult({ type: "sync", result });
      queryClient.invalidateQueries({ queryKey: ["indexStatus"] });
      queryClient.invalidateQueries({ queryKey: ["folders"] }); // Refresh folders in case new ones were added
    },
  });

  const rebuildMutation = useMutation({
    mutationFn: fullRebuild,
    onSuccess: (result) => {
      setSyncResult({ type: "rebuild", result });
      queryClient.invalidateQueries({ queryKey: ["indexStatus"] });
      queryClient.invalidateQueries({ queryKey: ["folders"] }); // Refresh folders in case new ones were added
    },
  });

  const isWorking = syncMutation.isPending || rebuildMutation.isPending;

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "Never";
    return new Date(dateStr).toLocaleString();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-[rgb(var(--border))]">
          <h2 className="text-lg font-semibold text-[rgb(var(--foreground))] flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-obsidian-100 dark:bg-obsidian-900/50">
              <Database className="h-4 w-4 text-obsidian-600 dark:text-obsidian-400" />
            </span>
            Notes Index
          </h2>
          <button
            onClick={onClose}
            className="btn-ghost p-2 text-[rgb(var(--muted-foreground))] hover:text-[rgb(var(--foreground))]"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {isLoading ? (
            <div className="text-center py-12">
              <Loader2 className="h-10 w-10 animate-spin mx-auto text-obsidian-500" />
              <p className="mt-3 text-[rgb(var(--muted-foreground))]">Loading status...</p>
            </div>
          ) : status ? (
            <div className="space-y-6">
              {/* Explanation */}
              <div className="flex items-start gap-3 p-4 rounded-xl bg-[rgb(var(--muted))] border border-[rgb(var(--border))]">
                <Info className="h-5 w-5 text-[rgb(var(--muted-foreground))] flex-shrink-0 mt-0.5" />
                <div className="text-sm text-[rgb(var(--muted-foreground))]">
                  <p className="mb-1">
                    <strong className="text-[rgb(var(--foreground))]">Total Notes</strong> = all markdown files in your vault
                  </p>
                  <p className="mb-1">
                    <strong className="text-[rgb(var(--foreground))]">Indexed</strong> = notes searchable by AI (some notes like empty files or system files are skipped)
                  </p>
                  <p>
                    <strong className="text-[rgb(var(--foreground))]">Pending</strong> = new or modified notes not yet synced
                  </p>
                </div>
              </div>

              {/* Status Grid */}
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-obsidian-50 dark:bg-obsidian-900/30 border border-obsidian-100 dark:border-obsidian-900/50">
                  <div className="flex items-center gap-2 mb-1">
                    <FileText className="h-4 w-4 text-obsidian-500" />
                    <span className="text-sm text-obsidian-600 dark:text-obsidian-400">Total Notes</span>
                  </div>
                  <div className="text-3xl font-bold text-obsidian-900 dark:text-obsidian-100">
                    {status.total_notes.toLocaleString()}
                  </div>
                </div>
                <div className="p-4 rounded-xl bg-green-50 dark:bg-green-900/30 border border-green-100 dark:border-green-900/50">
                  <div className="flex items-center gap-2 mb-1">
                    <Check className="h-4 w-4 text-green-500" />
                    <span className="text-sm text-green-600 dark:text-green-400">Indexed</span>
                  </div>
                  <div className="text-3xl font-bold text-green-900 dark:text-green-100">
                    {status.indexed_notes.toLocaleString()}
                  </div>
                </div>
                {status.pending_notes > 0 && (
                  <div className="p-4 rounded-xl bg-yellow-50 dark:bg-yellow-900/30 border border-yellow-100 dark:border-yellow-900/50">
                    <div className="flex items-center gap-2 mb-1">
                      <Zap className="h-4 w-4 text-yellow-500" />
                      <span className="text-sm text-yellow-600 dark:text-yellow-400">Pending</span>
                    </div>
                    <div className="text-3xl font-bold text-yellow-900 dark:text-yellow-100">
                      {status.pending_notes.toLocaleString()}
                    </div>
                  </div>
                )}
                {status.deleted_notes > 0 && (
                  <div className="p-4 rounded-xl bg-red-50 dark:bg-red-900/30 border border-red-100 dark:border-red-900/50">
                    <div className="flex items-center gap-2 mb-1">
                      <X className="h-4 w-4 text-red-500" />
                      <span className="text-sm text-red-600 dark:text-red-400">Deleted</span>
                    </div>
                    <div className="text-3xl font-bold text-red-900 dark:text-red-100">
                      {status.deleted_notes.toLocaleString()}
                    </div>
                  </div>
                )}
              </div>

              {/* Pending Info */}
              {status.pending_notes > 0 && (
                <div className="flex items-start gap-3 p-4 rounded-xl bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-900/50">
                  <AlertTriangle className="h-5 w-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-yellow-800 dark:text-yellow-200">
                    <p className="font-medium">{status.pending_notes} note(s) ready to sync</p>
                    <p className="text-yellow-700 dark:text-yellow-300 mt-1">
                      Click "Sync Now" to index only the new/changed notes. This is fast and only costs a few cents.
                    </p>
                  </div>
                </div>
              )}

              {/* Sync Times */}
              <div className="text-sm text-[rgb(var(--muted-foreground))] space-y-2 p-4 rounded-xl bg-[rgb(var(--muted))]">
                <p className="flex justify-between">
                  <span>Last incremental sync:</span>
                  <span className="font-medium text-[rgb(var(--foreground))]">
                    {formatDate(status.last_incremental_sync)}
                  </span>
                </p>
                <p className="flex justify-between">
                  <span>Last full rebuild:</span>
                  <span className="font-medium text-[rgb(var(--foreground))]">
                    {formatDate(status.last_full_sync)}
                  </span>
                </p>
              </div>

              {/* Sync Result */}
              {syncResult && (
                <div className="p-4 rounded-xl bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-900/50 animate-fade-in">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="p-1 rounded-full bg-green-100 dark:bg-green-900/50">
                      <Check className="h-4 w-4 text-green-600 dark:text-green-400" />
                    </span>
                    <span className="font-medium text-green-800 dark:text-green-200">
                      {syncResult.type === "sync" ? "Sync" : "Rebuild"} Complete
                    </span>
                  </div>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <div className="text-green-600 dark:text-green-400">Added</div>
                      <div className="font-semibold text-green-900 dark:text-green-100">{syncResult.result.notes_added}</div>
                    </div>
                    <div>
                      <div className="text-green-600 dark:text-green-400">Updated</div>
                      <div className="font-semibold text-green-900 dark:text-green-100">{syncResult.result.notes_updated}</div>
                    </div>
                    <div>
                      <div className="text-green-600 dark:text-green-400">Deleted</div>
                      <div className="font-semibold text-green-900 dark:text-green-100">{syncResult.result.notes_deleted}</div>
                    </div>
                  </div>
                  <div className="mt-3 pt-3 border-t border-green-200 dark:border-green-900/50 text-xs text-green-700 dark:text-green-300">
                    {syncResult.result.chunks_created.toLocaleString()} chunks |
                    ${parseFloat(syncResult.result.embedding_cost).toFixed(4)} |
                    {syncResult.result.duration_seconds.toFixed(1)}s
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex gap-3">
                <button
                  onClick={() => syncMutation.mutate()}
                  disabled={isWorking}
                  className="btn-primary flex-1"
                >
                  {syncMutation.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      Syncing...
                    </>
                  ) : (
                    <>
                      <RefreshCw className="h-4 w-4 mr-2" />
                      Sync Now
                    </>
                  )}
                </button>
                <button
                  onClick={() => {
                    if (
                      confirm(
                        "This will rebuild the entire index. This may take a few minutes and incur embedding costs. Continue?"
                      )
                    ) {
                      rebuildMutation.mutate();
                    }
                  }}
                  disabled={isWorking}
                  className="btn-secondary"
                >
                  {rebuildMutation.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      Rebuilding...
                    </>
                  ) : (
                    "Full Rebuild"
                  )}
                </button>
              </div>
            </div>
          ) : (
            <p className="text-center text-[rgb(var(--muted-foreground))] py-8">Failed to load status</p>
          )}
        </div>
      </div>
    </div>
  );
}
