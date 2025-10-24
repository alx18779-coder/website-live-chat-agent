<template>
  <div class="page-container">
    <!-- 标签页切换 -->
    <n-tabs type="line" v-model:value="activeTab">
      <n-tab-pane name="documents" tab="文档列表">
        <!-- 搜索和操作栏 -->
        <n-card style="margin-bottom: 16px">
          <n-space>
            <n-input
              v-model:value="searchText"
              placeholder="搜索文档..."
              style="width: 300px"
              @keyup.enter="loadDocuments"
            />
            <n-button type="primary" @click="loadDocuments">
              搜索
            </n-button>
            <n-button @click="searchText = ''; loadDocuments()">
              重置
            </n-button>
          </n-space>
        </n-card>

        <!-- 文档列表 -->
        <n-card>
          <n-data-table
            :columns="columns"
            :data="documents"
            :loading="loading"
            :pagination="pagination"
            @update:page="handlePageChange"
            @update:page-size="handlePageSizeChange"
          />
        </n-card>
      </n-tab-pane>
      
      <n-tab-pane name="upload" tab="文件上传">
        <!-- 文件上传组件 -->
        <FileUpload @upload-success="handleUploadSuccess" />
        
        <!-- 上传历史 -->
        <div style="margin-top: 24px">
          <UploadHistory ref="uploadHistoryRef" />
        </div>
      </n-tab-pane>
    </n-tabs>

    <!-- 编辑对话框 -->
    <n-modal v-model:show="showEditModal">
      <n-card
        style="width: 600px"
        title="编辑文档"
        :bordered="false"
        size="huge"
        role="dialog"
        aria-modal="true"
      >
        <n-form
          ref="editFormRef"
          :model="editForm"
          :rules="editRules"
          label-placement="left"
          label-width="auto"
        >
          <n-form-item label="文档内容" path="content">
            <n-input
              v-model:value="editForm.content"
              type="textarea"
              :rows="10"
              placeholder="请输入文档内容"
            />
          </n-form-item>
        </n-form>

        <template #footer>
          <n-space justify="end">
            <n-button @click="showEditModal = false">取消</n-button>
            <n-button type="primary" :loading="editLoading" @click="handleSave">
              保存
            </n-button>
          </n-space>
        </template>
      </n-card>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, h } from 'vue'
import { NCard, NSpace, NInput, NButton, NDataTable, NModal, NForm, NFormItem, NTabs, NTabPane, useMessage } from 'naive-ui'
import type { DataTableColumns, FormInst, FormRules } from 'naive-ui'
import { getDocuments, updateDocument, deleteDocument, type Document } from '@/api/knowledge'
import FileUpload from '@/components/FileUpload.vue'
import UploadHistory from '@/components/UploadHistory.vue'

const message = useMessage()

// 数据状态
const documents = ref<Document[]>([])
const loading = ref(false)
const searchText = ref('')
const activeTab = ref('documents')

// 组件引用
const uploadHistoryRef = ref()

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 20,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 50, 100]
})

// 编辑对话框
const showEditModal = ref(false)
const editLoading = ref(false)
const editForm = reactive({
  id: '',
  content: '',
  metadata: {}
})
const editFormRef = ref<FormInst | null>(null)

const editRules: FormRules = {
  content: [
    {
      required: true,
      message: '请输入文档内容',
      trigger: ['input', 'blur']
    }
  ]
}

// 表格列定义
const columns: DataTableColumns<Document> = [
  {
    title: 'ID',
    key: 'id',
    width: 200,
    ellipsis: true
  },
  {
    title: '内容预览',
    key: 'text',
    ellipsis: {
      tooltip: true
    }
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 180,
    render: (row) => {
      return new Date(row.created_at * 1000).toLocaleString()
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    render: (row) => {
      return h('div', [
        h(NButton, {
          size: 'small',
          type: 'primary',
          onClick: () => handleEdit(row)
        }, { default: () => '编辑' }),
        h('span', { style: 'margin: 0 8px' }),
        h(NButton, {
          size: 'small',
          type: 'error',
          onClick: () => handleDelete(row.id)
        }, { default: () => '删除' })
      ])
    }
  }
]

// 加载文档列表
async function loadDocuments() {
  loading.value = true
  try {
    const response = await getDocuments({
      page: pagination.page,
      page_size: pagination.pageSize,
      search: searchText.value || undefined
    })
    
    documents.value = response.documents
    pagination.itemCount = response.total
  } catch (error) {
    message.error('加载文档列表失败')
    console.error('Load documents error:', error)
  } finally {
    loading.value = false
  }
}

// 分页处理
function handlePageChange(page: number) {
  pagination.page = page
  loadDocuments()
}

function handlePageSizeChange(pageSize: number) {
  pagination.pageSize = pageSize
  pagination.page = 1
  loadDocuments()
}

// 编辑文档
function handleEdit(document: Document) {
  editForm.id = document.id
  editForm.content = document.text
  editForm.metadata = document.metadata
  showEditModal.value = true
}

// 保存编辑
async function handleSave() {
  if (!editFormRef.value) return

  try {
    await editFormRef.value.validate()
    editLoading.value = true

    await updateDocument(editForm.id, {
      content: editForm.content,
      metadata: editForm.metadata
    })

    message.success('文档更新成功')
    showEditModal.value = false
    loadDocuments()
  } catch (error) {
    message.error('更新文档失败')
    console.error('Update document error:', error)
  } finally {
    editLoading.value = false
  }
}

// 删除文档
async function handleDelete(id: string) {
  try {
    await deleteDocument(id)
    message.success('文档删除成功')
    loadDocuments()
  } catch (error) {
    message.error('删除文档失败')
    console.error('Delete document error:', error)
  }
}

// 处理上传成功
function handleUploadSuccess() {
  // 刷新上传历史
  if (uploadHistoryRef.value) {
    uploadHistoryRef.value.refreshData()
  }
  
  // 如果当前在文档列表页面，也刷新文档列表
  if (activeTab.value === 'documents') {
    loadDocuments()
  }
}

onMounted(() => {
  loadDocuments()
})
</script>

<style scoped>
.page-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-container {
    padding: 10px;
  }
}
</style>
