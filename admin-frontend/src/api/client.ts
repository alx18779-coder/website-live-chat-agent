/**
 * API 客户端配置
 * 
 * 提供统一的 HTTP 请求封装，包括认证、错误处理等。
 */

import axios, { type AxiosInstance, type AxiosResponse, type AxiosError } from 'axios'

// 创建 axios 实例
const client: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 300000, // 5分钟超时（FAQ导入需要生成embedding，耗时较长）
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器：添加认证 token
client.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('admin_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器：处理错误和认证
client.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data
  },
  (error: AxiosError) => {
    // 处理认证错误
    if (error.response?.status === 401) {
      // 清除本地存储的 token
      localStorage.removeItem('admin_token')
      // 跳转到登录页
      window.location.href = '/login'
    }
    
    // 处理其他错误
    const message = (error.response?.data as any)?.detail || error.message || '请求失败'
    console.error('API Error:', message)
    
    return Promise.reject(error)
  }
)

export default client
