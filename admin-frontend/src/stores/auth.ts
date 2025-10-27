/**
 * 认证状态管理
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login, type LoginRequest } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const token = ref<string>(localStorage.getItem('admin_token') || '')
  const user = ref<string>('')

  // 计算属性
  const isAuthenticated = computed(() => !!token.value)

  // 登录
  async function loginUser(credentials: LoginRequest) {
    try {
      const response = await login(credentials)
      
      // 保存 token 和用户信息
      token.value = response.access_token
      user.value = credentials.username
      
      // 持久化存储
      localStorage.setItem('admin_token', response.access_token)
      localStorage.setItem('admin_user', credentials.username)
      
      return response
    } catch (error) {
      console.error('Login failed:', error)
      throw error
    }
  }

  // 登出
  function logout() {
    token.value = ''
    user.value = ''
    localStorage.removeItem('admin_token')
    localStorage.removeItem('admin_user')
  }

  // 初始化（从本地存储恢复状态）
  function init() {
    const storedToken = localStorage.getItem('admin_token')
    const storedUser = localStorage.getItem('admin_user')
    
    if (storedToken && storedUser) {
      token.value = storedToken
      user.value = storedUser
    }
  }

  return {
    // 状态
    token,
    user,
    isAuthenticated,
    
    // 方法
    loginUser,
    logout,
    init
  }
})
