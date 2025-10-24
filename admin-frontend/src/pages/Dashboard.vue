<template>
  <div class="dashboard-container">
    <n-grid :cols="4" :x-gap="16" :y-gap="16" responsive="screen" :collapsed-rows="1">
      <!-- 总览统计卡片 -->
      <n-grid-item v-for="stat in stats" :key="stat.title">
        <n-card>
          <n-statistic
            :label="stat.title"
            :value="stat.value"
            :suffix="stat.suffix"
          />
        </n-card>
      </n-grid-item>
    </n-grid>

    <!-- 图表区域 -->
    <n-card style="margin-top: 24px">
      <template #header>
        <h3>会话趋势</h3>
      </template>
      
      <ConversationTrendChart :days="7" />
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { NCard, NGrid, NGridItem, NStatistic } from 'naive-ui'
import { getOverviewStats } from '@/api/analytics'
import { getDocuments } from '@/api/knowledge'
import ConversationTrendChart from '@/components/ConversationTrendChart.vue'

// 统计数据
const stats = ref([
  {
    title: '总会话数',
    value: 0,
    suffix: '次'
  },
  {
    title: '今日会话',
    value: 0,
    suffix: '次'
  },
  {
    title: '平均置信度',
    value: 0,
    suffix: '%'
  },
  {
    title: '知识库文档',
    value: 0,
    suffix: '条'
  }
])

// 加载统计数据
async function loadStats() {
  try {
    const data = await getOverviewStats()
    if (stats.value[0]) stats.value[0].value = data.total_sessions
    if (stats.value[1]) stats.value[1].value = data.today_sessions
    if (stats.value[2]) stats.value[2].value = Math.round(data.avg_confidence * 100)
    
    // 获取知识库文档数量
    const knowledgeData = await getDocuments({ page: 1, page_size: 1 })
    if (stats.value[3]) stats.value[3].value = knowledgeData.total
  } catch (error) {
    console.error('Failed to load stats:', error)
  }
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .dashboard-container {
    padding: 10px;
  }
}
</style>
