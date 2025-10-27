/**
 * 统计报表 API
 */

import client from './client'

// 总览统计接口
export interface OverviewStats {
  total_sessions: number
  today_sessions: number
  avg_confidence: number
}

// 每日统计接口
export interface DailyStats {
  date: string
  count: number
}

/**
 * 获取总览统计
 */
export async function getOverviewStats(): Promise<OverviewStats> {
  return client.get('/api/admin/analytics/overview')
}

/**
 * 获取每日统计
 */
export async function getDailyStats(days: number = 7): Promise<DailyStats[]> {
  return client.get('/api/admin/analytics/daily', { 
    params: { days } 
  })
}
