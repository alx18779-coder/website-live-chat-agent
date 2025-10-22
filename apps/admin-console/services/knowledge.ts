import { request } from '@/services/http';

export type KnowledgeDocumentStatus = 'draft' | 'published' | 'archived';

export interface KnowledgeDocumentSummary {
  id: string;
  title: string;
  category?: string;
  tags: string[];
  version?: string;
  status: KnowledgeDocumentStatus;
  chunk_count: number;
  updated_at: string;
  created_by?: string;
  metadata?: Record<string, unknown>;
}

export interface KnowledgeDocumentListParams {
  page?: number;
  page_size?: number;
  keyword?: string;
  tags?: string[];
  status?: KnowledgeDocumentStatus | 'all';
}

export interface KnowledgeDocumentListResponse {
  documents: KnowledgeDocumentSummary[];
  total: number;
  page: number;
  page_size: number;
}

export interface KnowledgeUploadDocument {
  text: string;
  metadata: Record<string, unknown>;
}

export interface KnowledgeUploadPayload {
  documents: KnowledgeUploadDocument[];
  collection_name?: string;
  chunk_size?: number;
  chunk_overlap?: number;
}

export interface KnowledgeUploadResponse {
  success: boolean;
  inserted_count: number;
  collection_name: string;
  message: string;
}

export interface KnowledgeSearchParams {
  query: string;
  top_k?: number;
  collection_name?: string;
}

export interface KnowledgeSearchResult {
  text: string;
  score: number;
  metadata: Record<string, unknown>;
}

export interface KnowledgeSearchResponse {
  results: KnowledgeSearchResult[];
  query: string;
  total_results: number;
}

function buildQueryString(params: Record<string, unknown>) {
  const searchParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') {
      return;
    }

    if (Array.isArray(value)) {
      value.forEach((item) => searchParams.append(key, String(item)));
      return;
    }

    searchParams.set(key, String(value));
  });

  const queryString = searchParams.toString();
  return queryString ? `?${queryString}` : '';
}

export async function listKnowledgeDocuments(
  params: KnowledgeDocumentListParams,
): Promise<KnowledgeDocumentListResponse> {
  const query = buildQueryString({
    page: params.page,
    page_size: params.page_size,
    keyword: params.keyword,
    status: params.status === 'all' ? undefined : params.status,
    tags: params.tags,
  });

  return request<KnowledgeDocumentListResponse>(`/api/v1/knowledge/documents${query}`);
}

export async function uploadKnowledgeDocuments(
  payload: KnowledgeUploadPayload,
): Promise<KnowledgeUploadResponse> {
  return request<KnowledgeUploadResponse>('/api/v1/knowledge/upsert', {
    method: 'POST',
    body: JSON.stringify({
      collection_name: payload.collection_name ?? 'knowledge_base',
      chunk_size: payload.chunk_size ?? 500,
      chunk_overlap: payload.chunk_overlap ?? 50,
      documents: payload.documents,
    }),
  });
}

export async function searchKnowledge(
  params: KnowledgeSearchParams,
): Promise<KnowledgeSearchResponse> {
  const query = buildQueryString({
    query: params.query,
    top_k: params.top_k,
    collection_name: params.collection_name,
  });

  return request<KnowledgeSearchResponse>(`/api/v1/knowledge/search${query}`);
}
