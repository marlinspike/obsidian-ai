import axios, { AxiosInstance } from "axios";
import type {
  QueryRequest,
  QueryResponse,
  IndexStatus,
  SyncResult,
  CostSummary,
  QueryCost,
  ModelPricing,
  AvailableModel,
  ProviderStatus,
  ModelConfig,
  NoteListResponse,
  FolderListResponse,
  StreamChunk,
  AllTimeCostSummary,
  SaveCostResult,
} from "@/types";

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: "/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
});

// Query API
export async function query(request: QueryRequest): Promise<QueryResponse> {
  const response = await api.post<QueryResponse>("/query", request);
  return response.data;
}

export async function* streamQuery(
  request: QueryRequest
): AsyncGenerator<StreamChunk> {
  const response = await fetch("/api/v1/query/stream", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error("No response body");

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // Process complete SSE messages
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        const data = line.slice(6);
        if (data) {
          try {
            yield JSON.parse(data) as StreamChunk;
          } catch {
            // Skip invalid JSON
          }
        }
      }
    }
  }
}

// Index API
export async function getIndexStatus(): Promise<IndexStatus> {
  const response = await api.get<IndexStatus>("/index/status");
  return response.data;
}

export async function incrementalSync(): Promise<SyncResult> {
  const response = await api.post<SyncResult>("/index/sync");
  return response.data;
}

export async function fullRebuild(): Promise<SyncResult> {
  const response = await api.post<SyncResult>("/index/rebuild");
  return response.data;
}

// Cost API
export async function getCostSummary(): Promise<CostSummary> {
  const response = await api.get<CostSummary>("/cost/summary");
  return response.data;
}

export async function getCostHistory(limit = 50): Promise<QueryCost[]> {
  const response = await api.get<QueryCost[]>("/cost/history", {
    params: { limit },
  });
  return response.data;
}

export async function getPricingTable(): Promise<ModelPricing[]> {
  const response = await api.get<ModelPricing[]>("/cost/pricing");
  return response.data;
}

export async function resetCostSession(): Promise<{ message: string; new_session_id: string }> {
  const response = await api.post("/cost/reset");
  return response.data;
}

export async function getAllTimeCostSummary(): Promise<AllTimeCostSummary> {
  const response = await api.get<AllTimeCostSummary>("/cost/all-time");
  return response.data;
}

export async function saveCosts(): Promise<SaveCostResult> {
  const response = await api.post<SaveCostResult>("/cost/save");
  return response.data;
}

export async function resetAllCosts(): Promise<{ message: string; new_session_id: string }> {
  const response = await api.post("/cost/reset-all");
  return response.data;
}

// Settings API
export async function getAvailableModels(): Promise<AvailableModel[]> {
  const response = await api.get<AvailableModel[]>("/settings/models");
  return response.data;
}

export async function getCurrentModelConfig(): Promise<ModelConfig> {
  const response = await api.get<ModelConfig>("/settings/models/current");
  return response.data;
}

export async function getProviders(): Promise<ProviderStatus[]> {
  const response = await api.get<ProviderStatus[]>("/settings/providers");
  return response.data;
}

// Notes API
export async function listNotes(
  offset = 0,
  limit = 50,
  folder?: string
): Promise<NoteListResponse> {
  const response = await api.get<NoteListResponse>("/notes", {
    params: { offset, limit, folder },
  });
  return response.data;
}

export async function listFolders(): Promise<FolderListResponse> {
  const response = await api.get<FolderListResponse>("/notes/folders");
  return response.data;
}

// Health API
export async function healthCheck(): Promise<{ status: string; version: string }> {
  const response = await api.get("/health");
  return response.data;
}

export default api;
