/**
 * FAQ 管理 API
 */

import client from './client'

// FAQ 接口
export interface FAQ {
  id: string
  question: string
  answer: string
  text: string
  metadata: Record<string, any>
  created_at: number
}

// FAQ 列表响应接口
export interface FAQListResponse {
  faqs: FAQ[]
  total: number
}

// CSV 预览响应接口
export interface CSVPreviewResponse {
  columns: string[]
  preview_rows: Array<Record<string, string>>
  total_rows: number
  detected_language: string
}

// FAQ 导入响应接口
export interface FAQImportResponse {
  success: boolean
  imported_count: number
  message: string
}

/**
 * 预览 CSV 文件
 */
export async function previewCSV(file: File): Promise<CSVPreviewResponse> {
  const formData = new FormData()
  formData.append('file', file)
  
  return client.post('/api/admin/faq/upload/preview', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

/**
 * 导入 FAQ
 */
export async function importFAQ(params: {
  file: File
  text_columns: string
  embedding_columns: string
  text_template?: string
  language?: string
  onProgress?: (progress: number) => void
}): Promise<FAQImportResponse> {
  const formData = new FormData()
  formData.append('file', params.file)
  formData.append('text_columns', params.text_columns)
  formData.append('embedding_columns', params.embedding_columns)
  if (params.text_template) {
    formData.append('text_template', params.text_template)
  }
  if (params.language) {
    formData.append('language', params.language)
  }
  
  return client.post('/api/admin/faq/upload/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (progressEvent) => {
      if (progressEvent.total && params.onProgress) {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        params.onProgress(progress)
      }
    }
  })
}

/**
 * 获取 FAQ 列表
 */
export async function getFAQList(params: {
  skip?: number
  limit?: number
  language?: string
}): Promise<FAQListResponse> {
  return client.get('/api/admin/faq/list', { params })
}

/**
 * 获取 FAQ 详情
 */
export async function getFAQ(id: string): Promise<FAQ> {
  return client.get(`/api/admin/faq/${id}`)
}

/**
 * 删除 FAQ
 */
export async function deleteFAQ(id: string): Promise<{ message: string }> {
  return client.delete(`/api/admin/faq/${id}`)
}

