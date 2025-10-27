<template>
  <n-card title="上传记录">
    <!-- 操作栏 -->
    <template #header-extra>
      <n-space>
        <n-button @click="refreshData" :loading="loading">
          刷新
        </n-button>
        <n-button @click="clearCompleted" type="warning">
          清理已完成
        </n-button>
      </n-space>
    </template>
    
    <!-- 数据表格 -->
    <n-data-table
      :columns="columns"
      :data="uploadRecords"
      :loading="loading"
      :pagination="pagination"
      @update:page="handlePageChange"
      @update:page-size="handlePageSizeChange"
    />
  </n-card>
</template>

<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import {
  NCard,
  NSpace,
  NButton,
  NDataTable,
  NTag,
  NProgress,
  NPopconfirm,
  NIcon,
  useMessage,
  type DataTableColumns
} from 'naive-ui'
import {
  DeleteOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
  ReloadOutlined
} from '@vicons/antd'
import { getUploadRecords, retryUpload, rollbackUpload, type UploadStatusResponse } from '@/api/knowledge'

const message = useMessage()

// 响应式数据
const uploadRecords = ref<UploadStatusResponse[]>([])
const loading = ref(false)
const pagination = ref({
  page: 1,
  pageSize: 20,
  showSizePicker: true,
  pageSizes: [10, 20, 50, 100],
  showQuickJumper: true
})

// 表格列定义
const columns: DataTableColumns<UploadStatusResponse> = [
  {
    title: '文件名',
    key: 'filename',
    width: 200,
    ellipsis: {
      tooltip: true
    }
  },
  {
    title: '文件类型',
    key: 'file_type',
    width: 100,
    render: (row) => {
      const typeMap: Record<string, string> = {
        'pdf': 'PDF',
        'markdown': 'Markdown',
        'txt': '文本'
      }
      return h(NTag, { type: 'info' }, { default: () => typeMap[row.file_type] || row.file_type })
    }
  },
  {
    title: '文件大小',
    key: 'file_size',
    width: 120,
    render: (row) => {
      const size = row.file_size
      if (size < 1024) return `${size} B`
      if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
      return `${(size / 1024 / 1024).toFixed(1)} MB`
    }
  },
  {
    title: '状态',
    key: 'status',
    width: 120,
    render: (row) => renderStatus(row)
  },
  {
    title: '进度',
    key: 'progress',
    width: 150,
    render: (row) => renderProgress(row)
  },
  {
    title: '文档数',
    key: 'document_count',
    width: 100,
    render: (row) => row.document_count || '-'
  },
  {
    title: '上传时间',
    key: 'created_at',
    width: 180,
    render: (row) => new Date(row.created_at).toLocaleString()
  },
  {
    title: '处理时间',
    key: 'processed_at',
    width: 180,
    render: (row) => row.processed_at ? new Date(row.processed_at).toLocaleString() : '-'
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    render: (row) => renderActions(row)
  }
]

// 渲染状态
function renderStatus(row: UploadStatusResponse) {
  const statusMap: Record<string, { type: string, text: string, icon: any }> = {
    'pending': { type: 'default', text: '等待中', icon: ClockCircleOutlined },
    'processing': { type: 'info', text: '处理中', icon: ClockCircleOutlined },
    'completed': { type: 'success', text: '已完成', icon: CheckCircleOutlined },
    'failed': { type: 'error', text: '失败', icon: CloseCircleOutlined }
  }
  
  const status = statusMap[row.status] || { type: 'default', text: row.status, icon: ExclamationCircleOutlined }
  
  return h(NTag, { type: status.type as any }, {
    default: () => [
      h(NIcon, { size: 14, style: 'margin-right: 4px' }, { default: () => h(status.icon) }),
      status.text
    ]
  })
}

// 渲染进度
function renderProgress(row: UploadStatusResponse) {
  if (row.status === 'completed') {
    return h(NProgress, { percentage: 100, status: 'success', showIndicator: false })
  } else if (row.status === 'failed') {
    return h(NProgress, { percentage: row.progress, status: 'error', showIndicator: false })
  } else {
    return h(NProgress, { percentage: row.progress, status: 'info', showIndicator: false })
  }
}

// 渲染操作按钮
function renderActions(row: UploadStatusResponse) {
  const actions = []
  
  // 重试按钮（仅失败状态显示）
  if (row.status === 'failed') {
    actions.push(
      h(NPopconfirm, {
        onPositiveClick: () => handleRetry(row.upload_id)
      }, {
        trigger: () => h(NButton, {
          size: 'small',
          type: 'warning',
          quaternary: true
        }, {
          default: () => [
            h(NIcon, { size: 14 }, { default: () => h(ReloadOutlined) }),
            ' 重试'
          ]
        }),
        default: () => '确定要重试这个上传吗？'
      })
    )
  }
  
  // 回滚按钮（仅已完成状态显示）
  if (row.status === 'completed') {
    actions.push(
      h(NPopconfirm, {
        onPositiveClick: () => handleRollback(row.upload_id)
      }, {
        trigger: () => h(NButton, {
          size: 'small',
          type: 'error',
          quaternary: true
        }, {
          default: () => [
            h(NIcon, { size: 14 }, { default: () => h(DeleteOutlined) }),
            ' 回滚'
          ]
        }),
        default: () => '确定要回滚这个上传吗？这将删除所有相关文档。'
      })
    )
  }
  
  return h('div', { style: 'display: flex; gap: 8px' }, actions)
}

// 处理重试
async function handleRetry(uploadId: string) {
  try {
    await retryUpload(uploadId)
    message.success('重试任务已启动')
    await refreshData()
  } catch (error: any) {
    message.error(`重试失败: ${error.message || error}`)
  }
}

// 处理回滚
async function handleRollback(uploadId: string) {
  try {
    await rollbackUpload(uploadId)
    message.success('回滚成功')
    await refreshData()
  } catch (error: any) {
    message.error(`回滚失败: ${error.message || error}`)
  }
}

// 刷新数据
async function refreshData() {
  await loadData()
}

// 清理已完成记录
async function clearCompleted() {
  // 这里可以实现清理已完成记录的逻辑
  message.info('清理功能待实现')
}

// 加载数据
async function loadData() {
  try {
    loading.value = true
    const records = await getUploadRecords(pagination.value.pageSize)
    uploadRecords.value = records
  } catch (error: any) {
    message.error(`加载数据失败: ${error.message || error}`)
  } finally {
    loading.value = false
  }
}

// 处理分页变化
function handlePageChange(page: number) {
  pagination.value.page = page
  loadData()
}

// 处理页面大小变化
function handlePageSizeChange(pageSize: number) {
  pagination.value.pageSize = pageSize
  pagination.value.page = 1
  loadData()
}

// 组件挂载时加载数据
onMounted(() => {
  loadData()
})

// 暴露给父组件的方法
defineExpose({
  refreshData,
  loadData
})
</script>

<style scoped>
.n-data-table {
  margin-top: 16px;
}
</style>
