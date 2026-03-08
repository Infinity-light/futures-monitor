<!--
role: Render top-level application status summary.
depends:
  - vue
  - element-plus
  - ../stores/monitor
exports:
  - StatusBar
status: IMPLEMENTED
functions:
  - renderStatusBar() -> VNode
-->
<template>
  <el-header class="status-bar">
    <div class="status-content">
      <div class="logo">
        <el-icon><TrendCharts /></el-icon>
        <span>期货监控看板</span>
      </div>
      <el-space>
        <div class="status-item">
          <span class="status-label">连接状态:</span>
          <el-tag :type="connectionStatusType" size="small">
            {{ connectionStatusText }}
          </el-tag>
        </div>
        <div class="status-item">
          <span class="status-label">运行状态:</span>
          <el-tag :type="runningStatusType" size="small">
            {{ runningStatusText }}
          </el-tag>
        </div>
      </el-space>
    </div>
  </el-header>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { TrendCharts } from '@element-plus/icons-vue'
import { useMonitorStore } from '../stores/monitor'

const store = useMonitorStore()

const connectionStatusType = computed(() => {
  switch (store.connectionStatus) {
    case 'connected':
      return 'success'
    case 'connecting':
      return 'warning'
    case 'disconnected':
      return 'danger'
    case 'error':
      return 'danger'
    default:
      return 'info'
  }
})

const connectionStatusText = computed(() => {
  switch (store.connectionStatus) {
    case 'connected':
      return '已连接'
    case 'connecting':
      return '连接中'
    case 'disconnected':
      return '已断开'
    case 'error':
      return '连接失败'
    default:
      return '未知'
  }
})

const runningStatusType = computed(() => {
  return store.isRunning ? 'success' : 'info'
})

const runningStatusText = computed(() => {
  return store.isRunning ? '运行中' : '已停止'
})
</script>

<style scoped>
.status-bar {
  height: 60px;
  background-color: #fff;
  border-bottom: 1px solid #dcdfe6;
  padding: 0 20px;
  display: flex;
  align-items: center;
}

.status-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
  color: #409eff;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-label {
  font-size: 14px;
  color: #606266;
}
</style>
