/**
 * 系统配置 API
 */

import client from './client'

// 系统配置接口
export interface SystemConfig {
  llm_provider: string
  llm_model: string
  embedding_provider: string
  embedding_model: string
  vector_top_k: number
  vector_score_threshold: number
  milvus_host: string
  milvus_port: number
  redis_host: string
  redis_port: number
}

// 健康检查接口
export interface HealthCheck {
  status: string
  services: Record<string, {
    status: string
    message: string
  }>
}

/**
 * 获取系统配置
 */
export async function getSystemConfig(): Promise<SystemConfig> {
  return client.get('/api/admin/settings/config')
}

/**
 * 系统健康检查
 */
export async function getHealthCheck(): Promise<HealthCheck> {
  return client.get('/api/admin/settings/health')
}
