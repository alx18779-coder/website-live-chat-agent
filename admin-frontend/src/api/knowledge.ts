/**
 * 知识库管理 API
 */

import client from './client'

// 文档接口
export interface Document {
  id: string
  text: string
  metadata: Record<string, any>
  created_at: number
}

// 文档列表响应接口
export interface DocumentListResponse {
  documents: Document[]
  total: number
  page: number
  page_size: number
}

// 文档更新请求接口
export interface DocumentUpdateRequest {
  content: string
  metadata: Record<string, any>
}

// 文件上传相关接口
export interface FileUploadResponse {
  upload_id: string
  filename: string
  status: string
  message: string
}

export interface UploadStatusResponse {
  upload_id: string
  filename: string
  file_type: string
  file_size: number
  status: string
  progress: number
  document_count: number
  error_message?: string
  created_at: string
  processed_at?: string
}

export interface FilePreviewResponse {
  filename: string
  file_type: string
  chunks: string[]
  total_chunks: number
  estimated_tokens: number
}

/**
 * 获取文档列表
 */
export async function getDocuments(params: {
  page?: number
  page_size?: number
  search?: string
}): Promise<DocumentListResponse> {
  return client.get('/api/admin/knowledge/documents', { params })
}

/**
 * 获取文档详情
 */
export async function getDocument(id: string): Promise<Document> {
  return client.get(`/api/admin/knowledge/documents/${id}`)
}

/**
 * 更新文档
 */
export async function updateDocument(
  id: string, 
  data: DocumentUpdateRequest
): Promise<{ message: string }> {
  return client.put(`/api/admin/knowledge/documents/${id}`, data)
}

/**
 * 删除文档
 */
export async function deleteDocument(id: string): Promise<{ message: string }> {
  return client.delete(`/api/admin/knowledge/documents/${id}`)
}

// 文件上传相关 API

/**
 * 上传文件
 */
export async function uploadFiles(
  files: File[],
  source?: string,
  version?: string,
  onProgress?: (progress: number) => void
): Promise<FileUploadResponse[]> {
  const formData = new FormData()
  
  files.forEach(file => {
    formData.append('files', file)
  })
  
  if (source) formData.append('source', source)
  if (version) formData.append('version', version)
  
  return client.post('/api/admin/knowledge/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (progressEvent) => {
      if (progressEvent.total && onProgress) {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        onProgress(progress)
      }
    }
  })
}

/**
 * 获取上传记录列表
 */
export async function getUploadRecords(limit?: number): Promise<UploadStatusResponse[]> {
  return client.get('/api/admin/knowledge/uploads', {
    params: { limit }
  })
}

/**
 * 获取上传状态
 */
export async function getUploadStatus(uploadId: string): Promise<UploadStatusResponse> {
  return client.get(`/api/admin/knowledge/uploads/${uploadId}`)
}

/**
 * 重试上传
 */
export async function retryUpload(uploadId: string): Promise<{ message: string }> {
  return client.post(`/api/admin/knowledge/uploads/${uploadId}/retry`)
}

/**
 * 回滚上传
 */
export async function rollbackUpload(uploadId: string): Promise<{ message: string }> {
  return client.delete(`/api/admin/knowledge/uploads/${uploadId}`)
}

/**
 * 预览文件
 */
export async function previewFile(file: File): Promise<FilePreviewResponse> {
  const formData = new FormData()
  formData.append('file', file)
  
  return client.post('/api/admin/knowledge/preview', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}
