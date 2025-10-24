<template>
  <div class="page-container">
    <!-- 标签页切换 -->
    <n-tabs type="line" v-model:value="activeTab">
      <n-tab-pane name="list" tab="FAQ列表">
        <!-- 搜索和操作栏 -->
        <n-card style="margin-bottom: 16px">
          <n-space>
            <n-select
              v-model:value="selectedLanguage"
              :options="languageOptions"
              placeholder="选择语言"
              style="width: 150px"
              clearable
              @update:value="loadFAQs"
            />
            <n-button type="primary" @click="loadFAQs">
              刷新
            </n-button>
          </n-space>
        </n-card>

        <!-- FAQ 列表 -->
        <n-card>
          <n-data-table
            :columns="columns"
            :data="faqs"
            :loading="loading"
            :pagination="pagination"
            @update:page="handlePageChange"
            @update:page-size="handlePageSizeChange"
          />
        </n-card>
      </n-tab-pane>
      
      <n-tab-pane name="upload" tab="CSV 上传">
        <!-- 上传步骤说明 -->
        <n-card title="上传步骤" style="margin-bottom: 16px">
          <n-steps :current="uploadStep" status="process">
            <n-step title="上传 CSV" description="选择并上传 CSV 文件" />
            <n-step title="配置列" description="选择用于文本和向量的列" />
            <n-step title="导入" description="确认并导入到数据库" />
          </n-steps>
        </n-card>

        <!-- 步骤 1: 选择文件 -->
        <n-card v-if="uploadStep === 1" title="选择 CSV 文件">
          <n-upload
            :max="1"
            accept=".csv"
            :custom-request="handleUpload"
            @change="handleFileChange"
            v-model:file-list="fileList"
          >
            <n-upload-dragger>
              <div style="margin-bottom: 12px">
                <n-icon size="48" :depth="3">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                    <path fill="currentColor" d="M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm4 18H6V4h7v5h5v11z"/>
                  </svg>
                </n-icon>
              </div>
              <n-text style="font-size: 16px">
                点击或拖拽 CSV 文件到此区域上传
              </n-text>
              <n-p depth="3" style="margin: 8px 0 0 0">
                仅支持 CSV 格式文件
              </n-p>
            </n-upload-dragger>
          </n-upload>

          <n-card v-if="csvPreview" title="CSV 预览" style="margin-top: 16px">
            <n-space vertical>
              <n-text>
                检测到列：<n-tag v-for="col in csvPreview.columns" :key="col" style="margin: 0 4px">{{ col }}</n-tag>
              </n-text>
              <n-text>总行数：{{ csvPreview.total_rows }}</n-text>
              <n-text>检测语言：{{ csvPreview.detected_language === 'zh' ? '中文' : '英文' }}</n-text>
              
              <!-- 预览数据 -->
              <n-data-table
                :columns="previewColumns"
                :data="csvPreview.preview_rows"
                :pagination="false"
                size="small"
              />

              <n-space justify="end">
                <n-button @click="resetUpload">重新上传</n-button>
                <n-button type="primary" @click="uploadStep = 2">
                  下一步
                </n-button>
              </n-space>
            </n-space>
          </n-card>
        </n-card>

        <!-- 步骤 2: 配置列 -->
        <n-card v-if="uploadStep === 2" title="配置列映射">
          <n-form
            ref="configFormRef"
            :model="importConfig"
            label-placement="left"
            label-width="140"
          >
            <n-form-item label="文本列 (text)">
              <n-select
                v-model:value="importConfig.textColumns"
                :options="columnOptions"
                multiple
                placeholder="选择用于生成展示文本的列"
                style="width: 100%"
              />
              <template #feedback>
                选择的列将被拼接成展示文本
              </template>
            </n-form-item>

            <n-form-item label="向量列 (embedding)">
              <n-select
                v-model:value="importConfig.embeddingColumns"
                :options="columnOptions"
                multiple
                placeholder="选择用于生成向量的列"
                style="width: 100%"
              />
              <template #feedback>
                选择的列将被用于生成检索向量（建议只选择问题列）
              </template>
            </n-form-item>

            <n-form-item label="文本模板">
              <n-input
                v-model:value="importConfig.textTemplate"
                placeholder="{question}\n答：{answer}"
                type="textarea"
                :rows="3"
              />
              <template #feedback>
                使用 {column_name} 作为占位符，例如：{question}\n答：{answer}
              </template>
            </n-form-item>

            <n-form-item label="语言">
              <n-radio-group v-model:value="importConfig.language">
                <n-space>
                  <n-radio value="zh">中文</n-radio>
                  <n-radio value="en">English</n-radio>
                </n-space>
              </n-radio-group>
            </n-form-item>
          </n-form>

          <n-space justify="end" style="margin-top: 16px">
            <n-button @click="uploadStep = 1">上一步</n-button>
            <n-button type="primary" @click="uploadStep = 3" :disabled="!isConfigValid">
              下一步
            </n-button>
          </n-space>
        </n-card>

        <!-- 步骤 3: 确认导入 -->
        <n-card v-if="uploadStep === 3" title="确认导入">
          <n-space vertical>
            <n-alert type="info" title="导入配置摘要">
              <n-space vertical size="small">
                <n-text>文件名：{{ currentFile?.name }}</n-text>
                <n-text>总行数：{{ csvPreview?.total_rows }}</n-text>
                <n-text>文本列：{{ importConfig.textColumns.join(', ') }}</n-text>
                <n-text>向量列：{{ importConfig.embeddingColumns.join(', ') }}</n-text>
                <n-text>语言：{{ importConfig.language === 'zh' ? '中文' : '英文' }}</n-text>
              </n-space>
            </n-alert>

            <n-progress
              v-if="importing"
              type="line"
              :percentage="importProgress"
              :indicator-placement="'inside'"
              processing
            />

            <n-space justify="end">
              <n-button @click="uploadStep = 2" :disabled="importing">
                上一步
              </n-button>
              <n-button
                type="primary"
                @click="handleImport"
                :loading="importing"
                :disabled="importing || !isConfigValid"
              >
                {{ importing ? '导入中...' : '开始导入' }}
              </n-button>
            </n-space>
          </n-space>
        </n-card>
      </n-tab-pane>
    </n-tabs>

    <!-- 删除确认对话框 -->
    <n-modal v-model:show="showDeleteModal">
      <n-card
        style="width: 500px"
        title="确认删除"
        :bordered="false"
        size="huge"
        role="dialog"
        aria-modal="true"
      >
        <n-text>确定要删除这条 FAQ 吗？此操作不可恢复。</n-text>
        <template #footer>
          <n-space justify="end">
            <n-button @click="showDeleteModal = false">取消</n-button>
            <n-button type="error" :loading="deleteLoading" @click="confirmDelete">
              删除
            </n-button>
          </n-space>
        </template>
      </n-card>
    </n-modal>

    <!-- 查看详情对话框 -->
    <n-modal v-model:show="showDetailModal">
      <n-card
        style="width: 700px"
        title="FAQ 详情"
        :bordered="false"
        size="huge"
        role="dialog"
        aria-modal="true"
      >
        <n-space vertical v-if="currentFAQ">
          <n-descriptions label-placement="left" :column="1" bordered>
            <n-descriptions-item label="ID">
              {{ currentFAQ.id }}
            </n-descriptions-item>
            <n-descriptions-item label="问题">
              <n-text>{{ currentFAQ.question }}</n-text>
            </n-descriptions-item>
            <n-descriptions-item label="答案">
              <n-text>{{ currentFAQ.answer }}</n-text>
            </n-descriptions-item>
            <n-descriptions-item label="语言">
              {{ currentFAQ.metadata.language === 'zh' ? '中文' : '英文' }}
            </n-descriptions-item>
            <n-descriptions-item label="创建时间">
              {{ formatDate(currentFAQ.created_at) }}
            </n-descriptions-item>
          </n-descriptions>
        </n-space>
        <template #footer>
          <n-space justify="end">
            <n-button @click="showDetailModal = false">关闭</n-button>
          </n-space>
        </template>
      </n-card>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, h, computed } from 'vue'
import {
  NCard, NSpace, NButton, NDataTable, NModal, NTabs, NTabPane, NText, NTag,
  NSelect, NUpload, NUploadDragger, NIcon, NP, NSteps, NStep, NForm,
  NFormItem, NInput, NRadioGroup, NRadio, NAlert, NProgress, NDescriptions,
  NDescriptionsItem, useMessage, type UploadCustomRequestOptions, type UploadFileInfo
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import {
  getFAQList, deleteFAQ, previewCSV, importFAQ,
  type FAQ, type CSVPreviewResponse
} from '@/api/faq'

const message = useMessage()

// 激活的标签页
const activeTab = ref('list')

// FAQ 列表状态
const faqs = ref<FAQ[]>([])
const loading = ref(false)
const selectedLanguage = ref<string | null>(null)

// 分页状态
const pagination = reactive({
  page: 1,
  pageSize: 20,
  showSizePicker: true,
  pageSizes: [10, 20, 50, 100],
  itemCount: 0,
  prefix: (info: any) => `共 ${info.itemCount} 条`
})

// 语言选项
const languageOptions = [
  { label: '全部', value: null },
  { label: '中文', value: 'zh' },
  { label: '英文', value: 'en' }
]

// 上传相关状态
const uploadStep = ref(1)
const fileList = ref<UploadFileInfo[]>([])
const currentFile = ref<File | null>(null)
const csvPreview = ref<CSVPreviewResponse | null>(null)

// 导入配置
const importConfig = reactive({
  textColumns: [] as string[],
  embeddingColumns: [] as string[],
  textTemplate: '{question}\n答：{answer}',
  language: 'zh'
})

// 导入状态
const importing = ref(false)
const importProgress = ref(0)

// 删除相关状态
const showDeleteModal = ref(false)
const deleteLoading = ref(false)
const deleteId = ref('')

// 详情相关状态
const showDetailModal = ref(false)
const currentFAQ = ref<FAQ | null>(null)

// 列定义
const columns: DataTableColumns<FAQ> = [
  {
    title: 'ID',
    key: 'id',
    width: 100,
    ellipsis: {
      tooltip: true
    }
  },
  {
    title: '问题',
    key: 'question',
    width: 300,
    ellipsis: {
      tooltip: true
    }
  },
  {
    title: '答案',
    key: 'answer',
    ellipsis: {
      tooltip: true
    }
  },
  {
    title: '语言',
    key: 'metadata.language',
    width: 80,
    render: (row) => {
      const lang = row.metadata?.language
      return lang === 'zh' ? '中文' : lang === 'en' ? 'English' : lang || '-'
    }
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 180,
    render: (row) => formatDate(row.created_at)
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    render: (row) => {
      return h('div', { style: 'display: flex; gap: 8px;' }, [
        h(
          NButton,
          {
            size: 'small',
            onClick: () => handleView(row)
          },
          { default: () => '查看' }
        ),
        h(
          NButton,
          {
            size: 'small',
            type: 'error',
            onClick: () => handleDelete(row.id)
          },
          { default: () => '删除' }
        )
      ])
    }
  }
]

// 预览列定义
const previewColumns = computed(() => {
  if (!csvPreview.value) return []
  return csvPreview.value.columns.map(col => ({
    title: col,
    key: col,
    ellipsis: { tooltip: true }
  }))
})

// 列选项
const columnOptions = computed(() => {
  if (!csvPreview.value) return []
  return csvPreview.value.columns.map(col => ({
    label: col,
    value: col
  }))
})

// 配置是否有效
const isConfigValid = computed(() => {
  return importConfig.textColumns.length > 0 && importConfig.embeddingColumns.length > 0
})

// 加载 FAQ 列表
async function loadFAQs() {
  loading.value = true
  try {
    const response = await getFAQList({
      skip: (pagination.page - 1) * pagination.pageSize,
      limit: pagination.pageSize,
      language: selectedLanguage.value || undefined
    })
    faqs.value = response.faqs
    pagination.itemCount = response.total
  } catch (error: any) {
    message.error(error.message || '加载 FAQ 列表失败')
  } finally {
    loading.value = false
  }
}

// 处理文件上传
async function handleUpload(options: UploadCustomRequestOptions) {
  const { file, onFinish, onError } = options
  currentFile.value = file.file as File
  
  try {
    const preview = await previewCSV(currentFile.value)
    csvPreview.value = preview
    
    // 自动设置默认配置
    if (preview.columns.includes('question') && preview.columns.includes('answer')) {
      importConfig.textColumns = ['question', 'answer']
      importConfig.embeddingColumns = ['question']
    } else {
      importConfig.textColumns = preview.columns
      importConfig.embeddingColumns = [preview.columns[0]]
    }
    importConfig.language = preview.detected_language
    
    message.success('CSV 文件解析成功')
    
    // 调用 Naive UI 的成功回调
    onFinish()
  } catch (error: any) {
    message.error(error.message || '解析 CSV 文件失败')
    currentFile.value = null
    
    // 调用 Naive UI 的错误回调
    onError()
  }
}

// 处理文件变化
function handleFileChange(data: { fileList: UploadFileInfo[] }) {
  if (data.fileList.length === 0) {
    resetUpload()
  }
}

// 重置上传
function resetUpload() {
  uploadStep.value = 1
  fileList.value = []
  currentFile.value = null
  csvPreview.value = null
  importConfig.textColumns = []
  importConfig.embeddingColumns = []
  importConfig.textTemplate = '{question}\n答：{answer}'
  importConfig.language = 'zh'
}

// 执行导入
async function handleImport() {
  if (!currentFile.value) {
    message.error('请先选择文件')
    return
  }

  // 验证配置
  if (importConfig.textColumns.length === 0) {
    message.error('请选择文本列（text）')
    return
  }
  
  if (importConfig.embeddingColumns.length === 0) {
    message.error('请选择向量列（embedding）')
    return
  }

  importing.value = true
  importProgress.value = 0

  try {
    const response = await importFAQ({
      file: currentFile.value,
      text_columns: importConfig.textColumns.join(','),
      embedding_columns: importConfig.embeddingColumns.join(','),
      text_template: importConfig.textTemplate,
      language: importConfig.language,
      onProgress: (progress) => {
        importProgress.value = progress
      }
    })

    message.success(response.message)
    
    // 重置并切换到列表
    resetUpload()
    activeTab.value = 'list'
    loadFAQs()
  } catch (error: any) {
    message.error(error.message || '导入 FAQ 失败')
  } finally {
    importing.value = false
    importProgress.value = 0
  }
}

// 查看详情
async function handleView(faq: FAQ) {
  currentFAQ.value = faq
  showDetailModal.value = true
}

// 删除 FAQ
function handleDelete(id: string) {
  deleteId.value = id
  showDeleteModal.value = true
}

// 确认删除
async function confirmDelete() {
  deleteLoading.value = true
  try {
    await deleteFAQ(deleteId.value)
    message.success('删除成功')
    showDeleteModal.value = false
    await loadFAQs()
  } catch (error: any) {
    message.error(error.message || '删除失败')
  } finally {
    deleteLoading.value = false
  }
}

// 分页处理
function handlePageChange(page: number) {
  pagination.page = page
  loadFAQs()
}

function handlePageSizeChange(pageSize: number) {
  pagination.pageSize = pageSize
  pagination.page = 1
  loadFAQs()
}

// 格式化日期
function formatDate(timestamp: number): string {
  const date = new Date(timestamp * 1000)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 组件挂载时加载数据
onMounted(() => {
  loadFAQs()
})
</script>

<style scoped>
.page-container {
  padding: 24px;
}
</style>

