<template>
  <div class="chart-container">
    <v-chart 
      class="chart" 
      :option="chartOption" 
      :loading="loading"
      autoresize
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components'
import VChart from 'vue-echarts'
import { getDailyStats } from '@/api/analytics'

// 注册 ECharts 组件
use([
  CanvasRenderer,
  LineChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
])

const props = defineProps<{
  days?: number
}>()

const loading = ref(true)
const dailyStats = ref<Array<{ date: string; count: number }>>([])

// 获取每日统计数据
const fetchDailyStats = async () => {
  try {
    loading.value = true
    const stats = await getDailyStats(props.days || 7)
    dailyStats.value = stats
  } catch (error) {
    console.error('获取每日统计失败:', error)
  } finally {
    loading.value = false
  }
}

// 图表配置
const chartOption = computed(() => {
  const dates = dailyStats.value.map(item => item.date)
  const counts = dailyStats.value.map(item => item.count)
  
  return {
    title: {
      text: '会话趋势',
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const data = params[0]
        return `${data.axisValue}<br/>会话数: ${data.value}`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: {
        formatter: (value: string) => {
          // 格式化日期显示
          const date = new Date(value)
          return `${date.getMonth() + 1}/${date.getDate()}`
        }
      }
    },
    yAxis: {
      type: 'value',
      name: '会话数',
      nameLocation: 'middle',
      nameGap: 30
    },
    series: [
      {
        name: '会话数',
        type: 'line',
        data: counts,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: {
          width: 3,
          color: '#1890ff'
        },
        itemStyle: {
          color: '#1890ff'
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(24, 144, 255, 0.3)' },
              { offset: 1, color: 'rgba(24, 144, 255, 0.05)' }
            ]
          }
        }
      }
    ]
  }
})

onMounted(() => {
  fetchDailyStats()
})
</script>

<style scoped>
.chart-container {
  width: 100%;
  height: 400px;
  padding: 16px;
}

.chart {
  width: 100%;
  height: 100%;
}
</style>

