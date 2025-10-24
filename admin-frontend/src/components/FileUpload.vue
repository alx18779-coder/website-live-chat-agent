<template>
  <n-card title="文件上传">
    <!-- 文件选择器 -->
    <n-upload
      ref="uploadRef"
      multiple
      :max="10"
      :accept="'.pdf,.md,.txt'"
      :custom-request="handleUpload"
      :file-list="fileList"
      @update:file-list="handleFileListChange"
      :show-download-button="false"
      :show-remove-button="true"
    >
      <n-upload-dragger>
        <div style="padding: 20px">
          <n-icon size="48" :depth="3">
            <CloudUploadOutlined />
          </n-icon>
          <n-text style="font-size: 16px; margin-top: 8px; display: block">
            点击或拖拽文件到此区域上传
          </n-text>
          <n-text depth="3" style="font-size: 14px; margin-top: 4px; display: block">
            支持 PDF、Markdown、纯文本格式，单文件最大 10MB
          </n-text>
        </div>
      </n-upload-dragger>
    </n-upload>
    
    <!-- 元数据输入 -->
    <n-form style="margin-top: 16px" :model="formData">
      <n-grid :cols="2" :x-gap="16">
        <n-grid-item>
          <n-form-item label="来源">
            <n-input 
              v-model:value="formData.source" 
              placeholder="例如：官方文档" 
            />
          </n-form-item>
        </n-grid-item>
        <n-grid-item>
          <n-form-item label="版本号">
            <n-input 
              v-model:value="formData.version" 
              placeholder="例如：1.0" 
            />
          </n-form-item>
        </n-grid-item>
      </n-grid>
    </n-form>
    
    <!-- 上传按钮和进度 -->
    <div style="margin-top: 16px; display: flex; align-items: center; gap: 16px">
      <n-button 
        type="primary" 
        @click="submitUpload" 
        :loading="uploading"
        :disabled="fileList.length === 0"
      >
        开始上传
      </n-button>
      
      <n-button 
        @click="previewSelectedFile" 
        :disabled="selectedFile === null"
      >
        预览文件
      </n-button>
      
      <n-button @click="clearFiles">
        清空文件
      </n-button>
    </div>
    
    <!-- 上传进度 -->
    <div v-if="uploading" style="margin-top: 16px">
      <n-progress 
        :percentage="uploadProgress" 
        :show-indicator="true"
        status="info"
      />
      <n-text depth="3" style="font-size: 12px; margin-top: 4px; display: block">
        正在上传文件...
      </n-text>
    </div>
    
    <!-- 上传结果 -->
    <div v-if="uploadResults.length > 0" style="margin-top: 16px">
      <n-alert 
        v-for="(result, index) in uploadResults" 
        :key="index"
        :type="result.status === 'failed' ? 'error' : 'info'"
        :title="result.filename"
        style="margin-bottom: 8px"
      >
        {{ result.message }}
        <template v-if="result.upload_id">
          <n-button 
            size="small" 
            @click="viewUploadStatus(result.upload_id)"
          >
            查看状态
          </n-button>
        </template>
      </n-alert>
    </div>
  </n-card>
  
  <!-- 文件预览对话框 -->
  <n-modal v-model:show="showPreview" preset="card" title="文件预览" style="width: 80%; max-width: 800px">
    <div v-if="previewData">
      <n-descriptions :column="2" bordered>
        <n-descriptions-item label="文件名">
          {{ previewData.filename }}
        </n-descriptions-item>
        <n-descriptions-item label="文件类型">
          {{ previewData.file_type }}
        </n-descriptions-item>
        <n-descriptions-item label="分块数量">
          {{ previewData.total_chunks }}
        </n-descriptions-item>
        <n-descriptions-item label="预估 Token">
          {{ previewData.estimated_tokens }}
        </n-descriptions-item>
      </n-descriptions>
      
      <n-divider />
      
      <n-tabs type="line">
        <n-tab-pane name="chunks" tab="分块预览">
          <n-list>
            <n-list-item v-for="(chunk, index) in previewData.chunks" :key="index">
              <n-thing :title="`分块 ${index + 1}`">
                <template #description>
                  {{ chunk.length }} 字符
                </template>
                <n-text style="white-space: pre-wrap">{{ chunk }}</n-text>
              </n-thing>
            </n-list-item>
          </n-list>
        </n-tab-pane>
      </n-tabs>
    </div>
    
    <template #footer>
      <n-space justify="end">
        <n-button @click="showPreview = false">关闭</n-button>
        <n-button type="primary" @click="confirmUpload">确认上传</n-button>
      </n-space>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import {
  NCard,
  NUpload,
  NUploadDragger,
  NIcon,
  NText,
  NForm,
  NFormItem,
  NInput,
  NGrid,
  NGridItem,
  NButton,
  NProgress,
  NAlert,
  NModal,
  NDescriptions,
  NDescriptionsItem,
  NDivider,
  NTabs,
  NTabPane,
  NList,
  NListItem,
  NThing,
  NSpace,
  useMessage,
  type UploadFileInfo
} from 'naive-ui'
import { CloudUploadOutlined } from '@vicons/antd'
import { uploadFiles, previewFile, type FileUploadResponse, type FilePreviewResponse } from '@/api/knowledge'

const message = useMessage()

// 响应式数据
const uploadRef = ref()
const fileList = ref<UploadFileInfo[]>([])
const formData = ref({
  source: '',
  version: '1.0'
})
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadResults = ref<FileUploadResponse[]>([])
const showPreview = ref(false)
const previewData = ref<FilePreviewResponse | null>(null)
const selectedFile = ref<File | null>(null)

// 处理文件列表变化
function handleFileListChange(files: UploadFileInfo[]) {
  fileList.value = files
}

// 处理文件上传
async function handleUpload() {
  // 这里不做实际上传，只是添加到文件列表
  return Promise.resolve()
}

// 提交上传
async function submitUpload() {
  if (fileList.value.length === 0) {
    message.warning('请先选择文件')
    return
  }
  
  try {
    uploading.value = true
    uploadProgress.value = 0
    uploadResults.value = []
    
    // 获取文件对象
    const files = fileList.value
      .filter(file => file.file)
      .map(file => file.file!)
    
    // 上传文件
    const results = await uploadFiles(
      files,
      formData.value.source || undefined,
      formData.value.version || undefined,
      (progress) => {
        uploadProgress.value = progress
      }
    )
    
    uploadResults.value = results
    
    // 检查结果
    const successCount = results.filter(r => r.status !== 'failed').length
    const failCount = results.filter(r => r.status === 'failed').length
    
    if (successCount > 0) {
      message.success(`成功上传 ${successCount} 个文件`)
    }
    if (failCount > 0) {
      message.error(`${failCount} 个文件上传失败`)
    }
    
    // 清空文件列表
    if (successCount > 0) {
      fileList.value = []
      formData.value.source = ''
      formData.value.version = '1.0'
    }
    
  } catch (error: any) {
    message.error(`上传失败: ${error.message || error}`)
  } finally {
    uploading.value = false
    uploadProgress.value = 0
  }
}

// 预览选中的文件
async function previewSelectedFile() {
  if (fileList.value.length === 0) {
    message.warning('请先选择文件')
    return
  }
  
  if (fileList.value.length > 1) {
    message.warning('请只选择一个文件进行预览')
    return
  }
  
  try {
    const file = fileList.value[0]?.file
    if (!file) {
      message.warning('文件信息不完整')
      return
    }
    previewData.value = await previewFile(file)
    showPreview.value = true
  } catch (error: any) {
    message.error(`预览失败: ${error.message || error}`)
  }
}

// 确认上传（从预览对话框）
async function confirmUpload() {
  showPreview.value = false
  await submitUpload()
}

// 清空文件
function clearFiles() {
  fileList.value = []
  uploadResults.value = []
  formData.value.source = ''
  formData.value.version = '1.0'
}

// 查看上传状态
function viewUploadStatus(uploadId: string) {
  // 这里可以跳转到上传历史页面或显示状态详情
  message.info(`查看上传状态: ${uploadId}`)
}

// 暴露给父组件的方法
defineExpose({
  clearFiles,
  submitUpload
})
</script>

<style scoped>
.n-upload-dragger {
  border: 2px dashed #d9d9d9;
  border-radius: 6px;
  width: 100%;
  height: 180px;
  text-align: center;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: border-color 0.3s;
}

.n-upload-dragger:hover {
  border-color: #40a9ff;
}

.n-upload-dragger.is-dragover {
  border-color: #40a9ff;
  background-color: rgba(24, 144, 255, 0.06);
}
</style>
