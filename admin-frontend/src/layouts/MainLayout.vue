<template>
  <n-layout has-sider>
    <!-- 侧边栏 -->
    <n-layout-sider
      :collapsed="collapsed"
      :collapsed-width="64"
      :width="240"
      show-trigger
      @collapse="collapsed = true"
      @expand="collapsed = false"
    >
      <n-menu
        :collapsed="collapsed"
        :collapsed-width="64"
        :collapsed-icon-size="22"
        :options="menuOptions"
        :value="currentRoute"
        @update:value="handleMenuSelect"
      />
    </n-layout-sider>

    <!-- 主内容区 -->
    <n-layout>
      <!-- 顶部导航 -->
      <n-layout-header style="padding: 24px; background: #fff; border-bottom: 1px solid #f0f0f0">
        <div style="display: flex; justify-content: space-between; align-items: center">
          <h2 style="margin: 0">{{ pageTitle }}</h2>
          <div style="display: flex; align-items: center; gap: 16px">
            <span>欢迎，{{ authStore.user }}</span>
            <n-button @click="handleLogout" type="error" ghost>
              退出登录
            </n-button>
          </div>
        </div>
      </n-layout-header>

      <!-- 页面内容 -->
      <n-layout-content style="padding: 24px; background: #f5f5f5; min-height: calc(100vh - 120px)">
        <router-view />
      </n-layout-content>
    </n-layout>
  </n-layout>
</template>

<script setup lang="ts">
import { ref, computed, h } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { NLayout, NLayoutSider, NLayoutHeader, NLayoutContent, NMenu, NButton, NIcon } from 'naive-ui'
import type { MenuOption } from 'naive-ui'
import { 
  DashboardOutlined, 
  DatabaseOutlined,
  QuestionCircleOutlined,
  CommentOutlined, 
  BarChartOutlined, 
  SettingOutlined 
} from '@vicons/antd'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// 侧边栏折叠状态
const collapsed = ref(false)

// 当前路由
const currentRoute = computed(() => route.name as string)

// 页面标题
const pageTitle = computed(() => {
  const titleMap: Record<string, string> = {
    Dashboard: '仪表盘',
    Knowledge: '知识库管理',
    FAQ: 'FAQ 管理',
    Conversations: '对话监控',
    Analytics: '统计报表',
    Settings: '系统配置'
  }
  return titleMap[route.name as string] || '管理平台'
})

// 菜单选项
const menuOptions: MenuOption[] = [
  {
    label: '仪表盘',
    key: 'Dashboard',
    icon: () => h(NIcon, null, { default: () => h(DashboardOutlined) })
  },
  {
    label: '知识库管理',
    key: 'Knowledge',
    icon: () => h(NIcon, null, { default: () => h(DatabaseOutlined) })
  },
  {
    label: 'FAQ 管理',
    key: 'FAQ',
    icon: () => h(NIcon, null, { default: () => h(QuestionCircleOutlined) })
  },
  {
    label: '对话监控',
    key: 'Conversations',
    icon: () => h(NIcon, null, { default: () => h(CommentOutlined) })
  },
  {
    label: '统计报表',
    key: 'Analytics',
    icon: () => h(NIcon, null, { default: () => h(BarChartOutlined) })
  },
  {
    label: '系统配置',
    key: 'Settings',
    icon: () => h(NIcon, null, { default: () => h(SettingOutlined) })
  }
]

// 菜单选择处理
function handleMenuSelect(key: string) {
  router.push({ name: key })
}

// 退出登录
function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
/* 响应式布局 */
@media (max-width: 768px) {
  .n-layout-sider {
    position: fixed !important;
    z-index: 1000;
    height: 100vh;
  }
  
  .n-layout-content {
    margin-left: 0 !important;
  }
}
</style>
