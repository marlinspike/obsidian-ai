// API Types (mirroring Pydantic models)

export type LLMProvider = "openai" | "azure_openai" | "anthropic" | "openrouter";

export type QueryComplexity = "simple" | "complex" | "auto";

// Query types
export interface QueryRequest {
  question: string;
  complexity?: QueryComplexity;
  folders?: string[];
  max_sources?: number;
}

export interface NoteReference {
  note_path: string;
  title: string;
  relevant_excerpt: string;
  folder: string;
  similarity_score: number;
  obsidian_url?: string;
}

export interface QueryResponse {
  answer: string;
  sources: NoteReference[];
  complexity_used: QueryComplexity;
  model_used: string;
  provider_used: string;
  input_tokens: number;
  output_tokens: number;
  embedding_tokens: number;
  total_cost: string;
  latency_ms: number;
}

export interface StreamChunk {
  type: "content" | "sources" | "metadata" | "done" | "error";
  content?: string;
  sources?: NoteReference[];
  metadata?: {
    complexity_used: string;
    model_used: string;
    provider_used: string;
    input_tokens: number;
    output_tokens: number;
    embedding_tokens: number;
    total_cost: string;
    latency_ms: number;
  };
  error?: string;
}

// Index types
export interface IndexStatus {
  total_notes: number;
  indexed_notes: number;
  pending_notes: number;
  deleted_notes: number;
  last_full_sync: string | null;
  last_incremental_sync: string | null;
}

export interface SyncResult {
  notes_added: number;
  notes_updated: number;
  notes_deleted: number;
  chunks_created: number;
  embedding_tokens_used: number;
  embedding_cost: string;
  duration_seconds: number;
}

// Cost types
export interface ModelCostBreakdown {
  model: string;
  provider: LLMProvider;
  query_count: number;
  input_tokens: number;
  output_tokens: number;
  total_cost: string;
}

export interface CostSummary {
  session_id: string;
  session_start: string;
  total_queries: number;
  total_cost: string;
  cost_by_model: Record<string, ModelCostBreakdown>;
  cost_by_provider: Record<string, string>;
  total_input_tokens: number;
  total_output_tokens: number;
  total_embedding_tokens: number;
}

export interface QueryCost {
  query_id: string;
  timestamp: string;
  model: string;
  provider: LLMProvider;
  input_tokens: number;
  output_tokens: number;
  input_cost: string;
  output_cost: string;
  total_cost: string;
  embedding_tokens?: number;
  embedding_cost?: string;
}

export interface ModelPricing {
  model: string;
  provider: LLMProvider;
  display_name: string;
  input_price_per_million: string;
  output_price_per_million: string;
  embedding_price_per_million?: string;
}

// Settings types
export interface AvailableModel {
  provider: LLMProvider;
  model: string;
  display_name: string;
  input_price_per_million: string;
  output_price_per_million: string;
  is_configured: boolean;
  is_embedding_model: boolean;
}

export interface ProviderStatus {
  provider: LLMProvider;
  display_name: string;
  is_configured: boolean;
  available_models: string[];
}

export interface ModelConfig {
  simple_query_provider: LLMProvider;
  simple_query_model: string;
  complex_query_provider: LLMProvider;
  complex_query_model: string;
  embedding_provider: LLMProvider;
  embedding_model: string;
}

// Notes types
export interface NoteListItem {
  path: string;
  title: string;
  folder: string;
  last_modified: string;
}

export interface NoteListResponse {
  notes: NoteListItem[];
  total: number;
  offset: number;
  limit: number;
}

export interface FolderListResponse {
  folders: string[];
  total: number;
}

// All-time cost tracking
export interface AllTimeCostSummary {
  first_tracked: string;
  total_queries: number;
  total_cost: string;
  cost_by_model: Record<string, {
    model: string;
    provider: string;
    query_count: number;
    total_cost: string;
  }>;
  is_saved: boolean;
}

export interface SaveCostResult {
  success: boolean;
  message: string;
  total_queries: number;
  total_cost: string;
}
