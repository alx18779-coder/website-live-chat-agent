/**
 * 路由配置
 */

import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/pages/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/dashboard'
      },
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/pages/Dashboard.vue'),
        meta: { title: '仪表盘' }
      },
      {
        path: 'knowledge',
        name: 'Knowledge',
        component: () => import('@/pages/Knowledge.vue'),
        meta: { title: '知识库管理' }
      },
      {
        path: 'faq',
        name: 'FAQ',
        component: () => import('@/pages/FAQ.vue'),
        meta: { title: 'FAQ 管理' }
      },
      {
        path: 'conversations',
        name: 'Conversations',
        component: () => import('@/pages/Conversations.vue'),
        meta: { title: '对话监控' }
      },
      {
        path: 'analytics',
        name: 'Analytics',
        component: () => import('@/pages/Analytics.vue'),
        meta: { title: '统计报表' }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/pages/Settings.vue'),
        meta: { title: '系统配置' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()
  
  // 初始化认证状态
  authStore.init()
  
  // 检查是否需要认证
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if (to.path === '/login' && authStore.isAuthenticated) {
    next('/')
  } else {
    next()
  }
})

export default router
