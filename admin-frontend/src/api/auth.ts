/**
 * 认证相关 API
 */

import client from './client'

// 登录请求接口
export interface LoginRequest {
  username: string
  password: string
}

// 登录响应接口
export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in: number
}

// 刷新 token 请求接口
export interface RefreshRequest {
  refresh_token: string
}

/**
 * 管理员登录
 */
export async function login(data: LoginRequest): Promise<LoginResponse> {
  return client.post('/api/admin/auth/login', data)
}

/**
 * 刷新访问令牌
 */
export async function refreshToken(data: RefreshRequest): Promise<LoginResponse> {
  return client.post('/api/admin/auth/refresh', data)
}
