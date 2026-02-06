import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { X, DollarSign, BarChart3, History, RefreshCw, Save, Trash2, Check, Clock, TrendingUp } from "lucide-react";
import { getCostSummary, getCostHistory, resetCostSession, getAllTimeCostSummary, saveCosts, resetAllCosts } from "@/services/api";

interface CostDashboardProps {
  onClose: () => void;
}

export function CostDashboard({ onClose }: CostDashboardProps) {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<"session" | "all-time">("session");
  const [saveMessage, setSaveMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const { data: summary, refetch: refetchSummary } = useQuery({
    queryKey: ["costSummary"],
    queryFn: getCostSummary,
    refetchInterval: 5000,
  });

  const { data: allTimeSummary, refetch: refetchAllTime } = useQuery({
    queryKey: ["allTimeCostSummary"],
    queryFn: getAllTimeCostSummary,
    refetchInterval: 10000,
  });

  const { data: history } = useQuery({
    queryKey: ["costHistory"],
    queryFn: () => getCostHistory(20),
    refetchInterval: 5000,
  });

  const saveMutation = useMutation({
    mutationFn: saveCosts,
    onSuccess: (result) => {
      setSaveMessage({
        type: result.success ? "success" : "error",
        text: result.message,
      });
      setTimeout(() => setSaveMessage(null), 3000);
      refetchAllTime();
    },
    onError: () => {
      setSaveMessage({ type: "error", text: "Failed to save costs" });
      setTimeout(() => setSaveMessage(null), 3000);
    },
  });

  const resetAllMutation = useMutation({
    mutationFn: resetAllCosts,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["costSummary"] });
      queryClient.invalidateQueries({ queryKey: ["allTimeCostSummary"] });
      queryClient.invalidateQueries({ queryKey: ["costHistory"] });
    },
  });

  const handleResetSession = async () => {
    await resetCostSession();
    refetchSummary();
    refetchAllTime();
  };

  const handleResetAll = () => {
    if (confirm("Are you sure you want to delete ALL cost history? This cannot be undone.")) {
      resetAllMutation.mutate();
    }
  };

  const formatCost = (cost: string) => {
    const num = parseFloat(cost);
    return num < 0.01 ? `$${num.toFixed(6)}` : `$${num.toFixed(4)}`;
  };

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  // Calculate percentages for bar chart
  const modelBreakdowns = summary ? Object.values(summary.cost_by_model) : [];
  const totalCost = summary ? parseFloat(summary.total_cost) : 0;

  const allTimeModelBreakdowns = allTimeSummary ? Object.values(allTimeSummary.cost_by_model) : [];
  const allTimeTotalCost = allTimeSummary ? parseFloat(allTimeSummary.total_cost) : 0;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content max-w-2xl max-h-[85vh]" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-[rgb(var(--border))]">
          <h2 className="text-lg font-semibold text-[rgb(var(--foreground))] flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-obsidian-100 dark:bg-obsidian-900/50">
              <BarChart3 className="h-4 w-4 text-obsidian-600 dark:text-obsidian-400" />
            </span>
            Cost Dashboard
          </h2>
          <div className="flex items-center gap-2">
            <button
              onClick={() => saveMutation.mutate()}
              disabled={saveMutation.isPending}
              className="btn-ghost p-2 text-[rgb(var(--muted-foreground))] hover:text-green-600 dark:hover:text-green-400"
              title="Save costs to file"
            >
              <Save className={`h-4 w-4 ${saveMutation.isPending ? "animate-pulse" : ""}`} />
            </button>
            <button
              onClick={onClose}
              className="btn-ghost p-2 text-[rgb(var(--muted-foreground))] hover:text-[rgb(var(--foreground))]"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Save Message */}
        {saveMessage && (
          <div className={`mx-5 mt-4 p-3 rounded-lg flex items-center gap-2 text-sm ${
            saveMessage.type === "success"
              ? "bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300"
              : "bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300"
          }`}>
            <Check className="h-4 w-4" />
            {saveMessage.text}
          </div>
        )}

        {/* Tabs */}
        <div className="px-5 pt-4">
          <div className="flex rounded-xl bg-[rgb(var(--muted))] p-1">
            <button
              onClick={() => setActiveTab("session")}
              className={`flex-1 py-2 px-4 text-sm font-medium rounded-lg transition-all ${
                activeTab === "session"
                  ? "bg-[rgb(var(--card))] text-[rgb(var(--foreground))] shadow-sm"
                  : "text-[rgb(var(--muted-foreground))] hover:text-[rgb(var(--foreground))]"
              }`}
            >
              <Clock className="h-4 w-4 inline mr-2" />
              Current Session
            </button>
            <button
              onClick={() => setActiveTab("all-time")}
              className={`flex-1 py-2 px-4 text-sm font-medium rounded-lg transition-all ${
                activeTab === "all-time"
                  ? "bg-[rgb(var(--card))] text-[rgb(var(--foreground))] shadow-sm"
                  : "text-[rgb(var(--muted-foreground))] hover:text-[rgb(var(--foreground))]"
              }`}
            >
              <TrendingUp className="h-4 w-4 inline mr-2" />
              All-Time
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-5 overflow-y-auto max-h-[calc(85vh-180px)]">
          {activeTab === "session" && summary && (
            <div className="space-y-6">
              {/* Session Summary */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 rounded-xl bg-obsidian-50 dark:bg-obsidian-900/30 border border-obsidian-100 dark:border-obsidian-900/50">
                  <div className="text-sm text-obsidian-600 dark:text-obsidian-400">Total Cost</div>
                  <div className="text-2xl font-bold text-obsidian-900 dark:text-obsidian-100">
                    {formatCost(summary.total_cost)}
                  </div>
                </div>
                <div className="p-4 rounded-xl bg-[rgb(var(--muted))] border border-[rgb(var(--border))]">
                  <div className="text-sm text-[rgb(var(--muted-foreground))]">Queries</div>
                  <div className="text-2xl font-bold text-[rgb(var(--foreground))]">
                    {summary.total_queries}
                  </div>
                </div>
                <div className="p-4 rounded-xl bg-[rgb(var(--muted))] border border-[rgb(var(--border))]">
                  <div className="text-sm text-[rgb(var(--muted-foreground))]">Input Tokens</div>
                  <div className="text-2xl font-bold text-[rgb(var(--foreground))]">
                    {summary.total_input_tokens.toLocaleString()}
                  </div>
                </div>
                <div className="p-4 rounded-xl bg-[rgb(var(--muted))] border border-[rgb(var(--border))]">
                  <div className="text-sm text-[rgb(var(--muted-foreground))]">Output Tokens</div>
                  <div className="text-2xl font-bold text-[rgb(var(--foreground))]">
                    {summary.total_output_tokens.toLocaleString()}
                  </div>
                </div>
              </div>

              {/* Cost by Model */}
              {modelBreakdowns.length > 0 && (
                <div>
                  <h3 className="font-semibold text-[rgb(var(--foreground))] mb-3 flex items-center gap-2">
                    <DollarSign className="h-4 w-4" />
                    Cost by Model
                  </h3>
                  <div className="space-y-3">
                    {modelBreakdowns.map((breakdown) => {
                      const cost = parseFloat(breakdown.total_cost);
                      const percentage = totalCost > 0 ? (cost / totalCost) * 100 : 0;
                      return (
                        <div key={breakdown.model} className="space-y-1.5">
                          <div className="flex justify-between text-sm">
                            <span className="font-medium text-[rgb(var(--foreground))]">{breakdown.model}</span>
                            <span className="text-[rgb(var(--muted-foreground))]">
                              {breakdown.query_count} queries · {formatCost(breakdown.total_cost)}
                            </span>
                          </div>
                          <div className="h-2 bg-[rgb(var(--muted))] rounded-full overflow-hidden">
                            <div
                              className="h-full bg-obsidian-500 rounded-full transition-all"
                              style={{ width: `${percentage}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Cost by Provider */}
              {Object.keys(summary.cost_by_provider).length > 0 && (
                <div>
                  <h3 className="font-semibold text-[rgb(var(--foreground))] mb-3">Cost by Provider</h3>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(summary.cost_by_provider).map(([provider, cost]) => (
                      <div
                        key={provider}
                        className="px-3 py-2 rounded-lg bg-[rgb(var(--muted))] border border-[rgb(var(--border))] text-sm"
                      >
                        <span className="font-medium text-[rgb(var(--foreground))] capitalize">{provider}</span>
                        <span className="text-[rgb(var(--muted-foreground))] ml-2">{formatCost(cost)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recent Queries */}
              {history && history.length > 0 && (
                <div>
                  <h3 className="font-semibold text-[rgb(var(--foreground))] mb-3 flex items-center gap-2">
                    <History className="h-4 w-4" />
                    Recent Queries
                  </h3>
                  <div className="overflow-x-auto rounded-xl border border-[rgb(var(--border))]">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-left text-[rgb(var(--muted-foreground))] bg-[rgb(var(--muted))]">
                          <th className="py-3 px-4">Time</th>
                          <th className="py-3 px-4">Model</th>
                          <th className="py-3 px-4 text-right">Tokens</th>
                          <th className="py-3 px-4 text-right">Cost</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[rgb(var(--border))]">
                        {history.slice(0, 10).map((query) => (
                          <tr key={query.query_id}>
                            <td className="py-3 px-4 text-[rgb(var(--muted-foreground))]">
                              {formatTime(query.timestamp)}
                            </td>
                            <td className="py-3 px-4 text-[rgb(var(--foreground))]">{query.model}</td>
                            <td className="py-3 px-4 text-right text-[rgb(var(--muted-foreground))]">
                              {query.input_tokens + query.output_tokens}
                            </td>
                            <td className="py-3 px-4 text-right font-mono text-obsidian-600 dark:text-obsidian-400">
                              {formatCost(query.total_cost)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Reset Session Button */}
              <div className="pt-4 border-t border-[rgb(var(--border))]">
                <button
                  onClick={handleResetSession}
                  className="btn-secondary text-sm"
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Reset Session
                </button>
                <p className="text-xs text-[rgb(var(--muted-foreground))] mt-2">
                  Resets current session costs. Historical data is preserved.
                </p>
              </div>
            </div>
          )}

          {activeTab === "all-time" && allTimeSummary && (
            <div className="space-y-6">
              {/* All-Time Summary */}
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-obsidian-50 dark:bg-obsidian-900/30 border border-obsidian-100 dark:border-obsidian-900/50">
                  <div className="text-sm text-obsidian-600 dark:text-obsidian-400">All-Time Cost</div>
                  <div className="text-3xl font-bold text-obsidian-900 dark:text-obsidian-100">
                    {formatCost(allTimeSummary.total_cost)}
                  </div>
                </div>
                <div className="p-4 rounded-xl bg-[rgb(var(--muted))] border border-[rgb(var(--border))]">
                  <div className="text-sm text-[rgb(var(--muted-foreground))]">Total Queries</div>
                  <div className="text-3xl font-bold text-[rgb(var(--foreground))]">
                    {allTimeSummary.total_queries.toLocaleString()}
                  </div>
                </div>
              </div>

              {/* Tracking Since */}
              <div className="p-4 rounded-xl bg-[rgb(var(--muted))] border border-[rgb(var(--border))]">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm text-[rgb(var(--muted-foreground))]">Tracking Since</div>
                    <div className="text-lg font-medium text-[rgb(var(--foreground))]">
                      {formatDate(allTimeSummary.first_tracked)}
                    </div>
                  </div>
                  <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                    allTimeSummary.is_saved
                      ? "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300"
                      : "bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300"
                  }`}>
                    {allTimeSummary.is_saved ? "Saved to disk" : "Not yet saved"}
                  </div>
                </div>
              </div>

              {/* All-Time Cost by Model */}
              {allTimeModelBreakdowns.length > 0 && (
                <div>
                  <h3 className="font-semibold text-[rgb(var(--foreground))] mb-3 flex items-center gap-2">
                    <DollarSign className="h-4 w-4" />
                    Cost by Model (All-Time)
                  </h3>
                  <div className="space-y-3">
                    {allTimeModelBreakdowns.map((breakdown) => {
                      const cost = parseFloat(breakdown.total_cost);
                      const percentage = allTimeTotalCost > 0 ? (cost / allTimeTotalCost) * 100 : 0;
                      return (
                        <div key={breakdown.model} className="space-y-1.5">
                          <div className="flex justify-between text-sm">
                            <span className="font-medium text-[rgb(var(--foreground))]">{breakdown.model}</span>
                            <span className="text-[rgb(var(--muted-foreground))]">
                              {breakdown.query_count} queries · {formatCost(breakdown.total_cost)}
                            </span>
                          </div>
                          <div className="h-2 bg-[rgb(var(--muted))] rounded-full overflow-hidden">
                            <div
                              className="h-full bg-obsidian-500 rounded-full transition-all"
                              style={{ width: `${percentage}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Save and Reset Buttons */}
              <div className="pt-4 border-t border-[rgb(var(--border))] space-y-3">
                <div className="flex gap-3">
                  <button
                    onClick={() => saveMutation.mutate()}
                    disabled={saveMutation.isPending}
                    className="btn-primary"
                  >
                    <Save className={`h-4 w-4 mr-2 ${saveMutation.isPending ? "animate-spin" : ""}`} />
                    {saveMutation.isPending ? "Saving..." : "Save Costs Now"}
                  </button>
                  <button
                    onClick={handleResetAll}
                    disabled={resetAllMutation.isPending}
                    className="btn-secondary text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete All History
                  </button>
                </div>
                <p className="text-xs text-[rgb(var(--muted-foreground))]">
                  Costs are automatically saved after each query. Use "Save Costs Now" to force an immediate save.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
