/**
 * 对话监控 API
 */

import client from './client'

// 对话接口
export interface Conversation {
  id: string
  session_id: string
  user_message: string
  ai_response: string
  retrieved_docs: Array<Record<string, any>> | any // 支持多种格式
  confidence_score: number | null
  created_at: string
}

// 对话列表响应接口
export interface ConversationListResponse {
  conversations: Conversation[]
  total: number
  page: number
  page_size: number
}

/**
 * 获取对话历史列表
 */
export async function getConversations(params: {
  page?: number
  page_size?: number
  start_date?: string
  end_date?: string
}): Promise<ConversationListResponse> {
  return client.get('/api/admin/conversations/history', { params })
}

/**
 * 获取指定会话的对话记录
 */
export async function getSessionConversations(sessionId: string): Promise<Conversation[]> {
  return client.get(`/api/admin/conversations/sessions/${sessionId}`)
}
