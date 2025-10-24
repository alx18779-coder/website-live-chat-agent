<template>
  <div class="page-container">
    <n-card>
      <template #header>
        <h3>对话监控</h3>
      </template>
      
      <div style="height: 400px; display: flex; align-items: center; justify-content: center; color: #999">
        对话监控功能待实现
      </div>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { NCard } from 'naive-ui'
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
