<!--
role: Render runtime log panel with auto-scroll.
depends:
  - vue
  - element-plus
  - ../stores/monitor
exports:
  - LogPanel
status: IMPLEMENTED
functions:
  - renderLogPanel() -> VNode
-->
<template>
  <el-card class="log-panel" shadow="hover">
    <template #header>
      <div class="card-header">
        <span>运行日志</span>
        <div class="header-actions">
          <el-tag size="small" type="info">{{ store.logs.length }} 条</el-tag>
          <el-button
            link
            size="small"
            @click="clearLogs"
          >
            清空
          </el-button>
        </div>
      </div>
    </template>

    <div ref="logContainer" class="log-container">
      <div
        v-for="(log, index) in store.logs"
        :key="index"
        class="log-item"
        :class="`log-level-${log.level.toLowerCase()}`"
      >
        <span class="log-time">{{ formatTime(log.timestamp) }}</span>
        <el-tag :type="getLevelType(log.level)" size="small" class="log-level">
          {{ log.level }}
        </el-tag>
        <span class="log-message">{{ log.message }}</span>
      </div>
      <div v-if="store.logs.length === 0" class="log-empty">
        暂无日志
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { useMonitorStore } from '../stores/monitor'

const store = useMonitorStore()
const logContainer = ref<HTMLElement | null>(null)

function formatTime(timestamp: string): string {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

function getLevelType(level: string): string {
  const typeMap: Record<string, string> = {
    INFO: 'info',
    WARNING: 'warning',
    ERROR: 'danger'
  }
  return typeMap[level] || 'info'
}

function clearLogs() {
  store.logs = []
}

// 自动滚动到最新日志
watch(
  () => store.logs.length,
  () => {
    nextTick(() => {
      if (logContainer.value) {
        logContainer.value.scrollTop = logContainer.value.scrollHeight
      }
    })
  }
)
</script>

<style scoped>
.log-panel {
  height: 200px;
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

:deep(.el-card__body) {
  flex: 1;
  overflow: hidden;
  padding: 0;
}

.log-container {
  height: 100%;
  overflow-y: auto;
  padding: 12px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
}

.log-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
  border-bottom: 1px solid #f0f0f0;
}

.log-item:last-child {
  border-bottom: none;
}

.log-time {
  color: #909399;
  min-width: 80px;
  flex-shrink: 0;
}

.log-level {
  min-width: 60px;
  text-align: center;
  flex-shrink: 0;
}

.log-message {
  flex: 1;
  word-break: break-all;
}

.log-level-info .log-message {
  color: #303133;
}

.log-level-warning .log-message {
  color: #e6a23c;
}

.log-level-error .log-message {
  color: #f56c6c;
}

.log-empty {
  text-align: center;
  color: #909399;
  padding: 20px;
}

/* 自定义滚动条 */
.log-container::-webkit-scrollbar {
  width: 6px;
}

.log-container::-webkit-scrollbar-thumb {
  background-color: #c0c4cc;
  border-radius: 3px;
}

.log-container::-webkit-scrollbar-track {
  background-color: #f5f7fa;
}
</style>
