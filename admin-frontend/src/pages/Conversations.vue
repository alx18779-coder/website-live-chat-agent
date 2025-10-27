<template>
  <div class="page-container">
    <n-card>
      <template #header>
        <h3>对话监控</h3>
      </template>
      
      <!-- 筛选工具栏 -->
      <n-space vertical :size="16">
        <n-space>
          <n-date-picker
            v-model:value="dateRange"
            type="datetimerange"
            clearable
            placeholder="选择时间范围"
            style="width: 400px"
            @update:value="handleDateRangeChange"
          />
          <n-button type="primary" @click="loadConversations">
            <template #icon>
              <n-icon><SearchOutlined /></n-icon>
            </template>
            查询
          </n-button>
          <n-button @click="handleReset">
            <template #icon>
              <n-icon><SyncOutlined /></n-icon>
            </template>
            重置
          </n-button>
          <n-button @click="loadConversations" :loading="loading">
            <template #icon>
              <n-icon><ReloadOutlined /></n-icon>
            </template>
            刷新
          </n-button>
        </n-space>

        <!-- 统计信息 -->
        <n-space v-if="!loading && conversations.length > 0">
          <n-tag type="info">
            总对话数: {{ total }}
          </n-tag>
          <n-tag type="success" v-if="avgConfidence !== null">
            平均置信度: {{ (avgConfidence * 100).toFixed(1) }}%
          </n-tag>
        </n-space>
      </n-space>
    </n-card>

    <!-- 对话列表 -->
    <n-card style="margin-top: 16px">
      <n-data-table
        :columns="columns"
        :data="conversations"
        :loading="loading"
        :pagination="pagination"
        :bordered="false"
        @update:page="handlePageChange"
        @update:page-size="handlePageSizeChange"
      />
    </n-card>

    <!-- 对话详情对话框 -->
    <n-modal v-model:show="showDetailModal" preset="card" style="width: 900px" title="对话详情">
      <n-spin :show="detailLoading">
        <div v-if="selectedConversation" class="conversation-detail">
          <!-- 基本信息 -->
          <n-descriptions :column="2" bordered>
            <n-descriptions-item label="会话 ID">
              <n-text code>{{ selectedConversation.session_id }}</n-text>
            </n-descriptions-item>
            <n-descriptions-item label="对话 ID">
              <n-text code>{{ selectedConversation.id }}</n-text>
            </n-descriptions-item>
            <n-descriptions-item label="创建时间">
              {{ formatDateTime(selectedConversation.created_at) }}
            </n-descriptions-item>
            <n-descriptions-item label="置信度">
              <n-tag
                :type="getConfidenceType(selectedConversation.confidence_score)"
                v-if="selectedConversation.confidence_score !== null"
              >
                {{ (selectedConversation.confidence_score * 100).toFixed(1) }}%
              </n-tag>
              <n-text depth="3" v-else>N/A</n-text>
            </n-descriptions-item>
          </n-descriptions>

          <!-- 对话内容 -->
          <n-divider />
          <div class="message-section">
            <h4>用户消息</h4>
            <n-card embedded class="message-card user-message">
              <n-text>{{ selectedConversation.user_message }}</n-text>
            </n-card>
          </div>

          <div class="message-section">
            <h4>AI 回复</h4>
            <n-card embedded class="message-card ai-message">
              <n-text>{{ selectedConversation.ai_response }}</n-text>
            </n-card>
          </div>

          <!-- 检索文档 -->
          <div class="message-section" v-if="selectedConversation.retrieved_docs && selectedConversation.retrieved_docs.length > 0">
            <h4>检索文档 ({{ selectedConversation.retrieved_docs.length }})</h4>
            <n-collapse>
              <n-collapse-item 
                v-for="(doc, index) in selectedConversation.retrieved_docs" 
                :key="index"
                :title="`文档 ${index + 1}${doc.score ? ` - 相似度: ${(doc.score * 100).toFixed(1)}%` : ''}`"
              >
                <n-card embedded size="small">
                  <n-space vertical>
                    <div v-if="doc.metadata">
                      <n-text strong>元数据:</n-text>
                      <pre class="metadata-pre">{{ JSON.stringify(doc.metadata, null, 2) }}</pre>
                    </div>
                    <div v-if="doc.content">
                      <n-text strong>内容:</n-text>
                      <n-text depth="3">{{ doc.content }}</n-text>
                    </div>
                    <div v-if="doc.text">
                      <n-text strong>文本:</n-text>
                      <n-text depth="3">{{ doc.text }}</n-text>
                    </div>
                  </n-space>
                </n-card>
              </n-collapse-item>
            </n-collapse>
          </div>
          <n-empty 
            v-else 
            description="未使用检索文档" 
            style="margin-top: 16px"
          />
        </div>
      </n-spin>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, h, computed } from 'vue'
import { 
  NCard, NSpace, NButton, NDataTable, NModal, NDescriptions, NDescriptionsItem,
  NTag, NText, NDivider, NCollapse, NCollapseItem, NEmpty, NSpin, NDatePicker,
  NIcon, useMessage
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { SearchOutlined, ReloadOutlined, SyncOutlined } from '@vicons/antd'
import { getConversations, type Conversation, type ConversationListResponse } from '@/api/conversations'

const message = useMessage()

// 数据状态
const conversations = ref<Conversation[]>([])
const loading = ref(false)
const total = ref(0)
const dateRange = ref<[number, number] | null>(null)
const startDate = ref<string | undefined>(undefined)
const endDate = ref<string | undefined>(undefined)

// 详情对话框
const showDetailModal = ref(false)
const selectedConversation = ref<Conversation | null>(null)
const detailLoading = ref(false)

// 分页配置
const pagination = reactive({
  page: 1,
  pageSize: 20,
  showSizePicker: true,
  pageSizes: [10, 20, 50, 100],
  itemCount: 0,
  prefix: ({ itemCount }: { itemCount: number }) => `共 ${itemCount} 条`
})

// 计算平均置信度
const avgConfidence = computed(() => {
  if (conversations.value.length === 0) return null
  const scores = conversations.value
    .map(c => c.confidence_score)
    .filter((score): score is number => score !== null)
  
  if (scores.length === 0) return null
  return scores.reduce((sum, score) => sum + score, 0) / scores.length
})

// 表格列定义
const columns: DataTableColumns<Conversation> = [
  {
    title: '会话 ID',
    key: 'session_id',
    width: 180,
    ellipsis: {
      tooltip: true
    },
    render: (row) => h(
      NText,
      { code: true, style: { fontSize: '12px' } },
      { default: () => row.session_id.substring(0, 16) + '...' }
    )
  },
  {
    title: '用户消息',
    key: 'user_message',
    width: 250,
    ellipsis: {
      tooltip: true
    }
  },
  {
    title: 'AI 回复',
    key: 'ai_response',
    width: 250,
    ellipsis: {
      tooltip: true
    }
  },
  {
    title: '置信度',
    key: 'confidence_score',
    width: 100,
    align: 'center',
    render: (row) => {
      if (row.confidence_score === null) {
        return h(NText, { depth: 3 }, { default: () => 'N/A' })
      }
      return h(
        NTag,
        { type: getConfidenceType(row.confidence_score), size: 'small' },
        { default: () => `${(row.confidence_score! * 100).toFixed(1)}%` }
      )
    }
  },
  {
    title: '检索文档',
    key: 'retrieved_docs',
    width: 100,
    align: 'center',
    render: (row) => row.retrieved_docs?.length || 0
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 180,
    render: (row) => formatDateTime(row.created_at)
  },
  {
    title: '操作',
    key: 'actions',
    width: 100,
    align: 'center',
    render: (row) => h(
      NButton,
      {
        size: 'small',
        type: 'primary',
        text: true,
        onClick: () => handleViewDetail(row)
      },
      { default: () => '查看详情' }
    )
  }
]

// 时间格式化
function formatDateTime(dateStr: string): string {
  try {
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    })
  } catch (e) {
    return dateStr
  }
}

// 置信度类型
function getConfidenceType(score: number | null): 'success' | 'warning' | 'error' | 'default' {
  if (score === null) return 'default'
  if (score >= 0.8) return 'success'
  if (score >= 0.6) return 'warning'
  return 'error'
}

// 加载对话列表
async function loadConversations() {
  loading.value = true
  try {
    const params: {
      page?: number
      page_size?: number
      start_date?: string
      end_date?: string
    } = {
      page: pagination.page,
      page_size: pagination.pageSize
    }
    
    if (startDate.value) params.start_date = startDate.value
    if (endDate.value) params.end_date = endDate.value
    
    const response: ConversationListResponse = await getConversations(params)
    
    conversations.value = response.conversations
    total.value = response.total
    pagination.itemCount = response.total
    
    if (conversations.value.length === 0 && total.value === 0) {
      message.info('暂无对话记录')
    }
  } catch (error: any) {
    console.error('Failed to load conversations:', error)
    message.error(error.response?.data?.detail || '加载对话列表失败')
    conversations.value = []
    total.value = 0
    pagination.itemCount = 0
  } finally {
    loading.value = false
  }
}

// 查看详情
function handleViewDetail(conversation: Conversation) {
  selectedConversation.value = conversation
  showDetailModal.value = true
}

// 分页变化
function handlePageChange(page: number) {
  pagination.page = page
  loadConversations()
}

function handlePageSizeChange(pageSize: number) {
  pagination.pageSize = pageSize
  pagination.page = 1
  loadConversations()
}

// 时间范围变化
function handleDateRangeChange(value: [number, number] | null) {
  if (value) {
    startDate.value = new Date(value[0]).toISOString()
    endDate.value = new Date(value[1]).toISOString()
  } else {
    startDate.value = undefined
    endDate.value = undefined
  }
}

// 重置筛选
function handleReset() {
  dateRange.value = null
  startDate.value = undefined
  endDate.value = undefined
  pagination.page = 1
  loadConversations()
}

// 组件挂载时加载数据
onMounted(() => {
  loadConversations()
})
</script>

<style scoped>
.page-container {
  padding: 20px;
  max-width: 1600px;
  margin: 0 auto;
}

.conversation-detail {
  padding: 8px 0;
}

.message-section {
  margin-top: 16px;
}

.message-section h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.message-card {
  margin-bottom: 8px;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
}

.user-message {
  background-color: #f0f9ff;
  border-left: 3px solid #1890ff;
}

.ai-message {
  background-color: #f6ffed;
  border-left: 3px solid #52c41a;
}

.metadata-pre {
  background-color: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 12px;
  line-height: 1.5;
  margin: 8px 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-container {
    padding: 10px;
  }
}
</style>
