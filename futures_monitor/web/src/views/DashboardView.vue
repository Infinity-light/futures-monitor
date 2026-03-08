<!--
role: Compose dashboard view from components.
depends:
  - vue
  - element-plus
  - ../components/ControlPanel.vue
  - ../components/SymbolTable.vue
  - ../components/LogPanel.vue
  - ../stores/monitor
  - ../services/ws
exports:
  - DashboardView
status: IMPLEMENTED
functions:
  - renderDashboard() -> VNode
-->
<template>
  <el-container class="dashboard-view">
    <el-aside width="320px" class="sidebar">
      <ControlPanel />
    </el-aside>

    <el-container class="main-container">
      <el-main class="main-content">
        <SymbolTable />
      </el-main>

      <el-footer height="220px" class="footer">
        <LogPanel />
      </el-footer>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import ControlPanel from '../components/ControlPanel.vue'
import SymbolTable from '../components/SymbolTable.vue'
import LogPanel from '../components/LogPanel.vue'
import { useMonitorStore } from '../stores/monitor'
import { createMonitorSocket } from '../services/ws'

const store = useMonitorStore()
let wsClient: ReturnType<typeof createMonitorSocket> | null = null

function resolveWsUrl(): string {
  const configured = import.meta.env.VITE_WS_URL
  if (configured) {
    return configured
  }

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}/ws/events`
}

onMounted(async () => {
  await store.initialize()

  const wsUrl = resolveWsUrl()
  wsClient = createMonitorSocket(wsUrl, store)
  wsClient.connect()
})

onUnmounted(() => {
  if (wsClient) {
    wsClient.disconnect()
    wsClient = null
  }
})
</script>

<style scoped>
.dashboard-view {
  height: calc(100vh - 60px);
  background-color: #f5f7fa;
}

.sidebar {
  padding: 12px;
  background-color: #fff;
  border-right: 1px solid #dcdfe6;
  overflow-y: auto;
}

.main-container {
  display: flex;
  flex-direction: column;
}

.main-content {
  padding: 12px;
  overflow: hidden;
}

.footer {
  padding: 0 12px 12px;
  background-color: transparent;
}

@media (max-width: 768px) {
  .dashboard-view {
    flex-direction: column;
  }

  .sidebar {
    width: 100% !important;
    border-right: none;
    border-bottom: 1px solid #dcdfe6;
    max-height: 300px;
  }
}
</style>
