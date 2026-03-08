<!--
role: Render monitor control placeholders for user operations.
depends:
  - vue
  - element-plus
  - ../stores/monitor
exports:
  - ControlPanel
status: IMPLEMENTED
functions:
  - renderControlPanel() -> VNode
-->
<template>
  <el-card class="control-panel" shadow="hover">
    <template #header>
      <div class="card-header">
        <span>监控控制</span>
      </div>
    </template>

    <div class="control-content">
      <div class="input-section">
        <div class="input-label">
          <span>监控品种</span>
          <el-tag size="small" type="info">已解析: {{ parsedSymbolCount }} 个</el-tag>
        </div>
        <el-input
          v-model="symbolInput"
          type="textarea"
          :rows="3"
          placeholder="输入品种代码，每行一个，或输入 ALL&#10;例如：&#10;RB2505&#10;TA2505"
          :disabled="store.isRunning"
        />
      </div>

      <div class="button-section">
        <el-button
          type="primary"
          :disabled="!canStart"
          :loading="isStarting"
          @click="handleStart"
        >
          <el-icon><VideoPlay /></el-icon>
          启动监控
        </el-button>
        <el-button
          type="danger"
          :disabled="!store.isRunning"
          :loading="isStopping"
          @click="handleStop"
        >
          <el-icon><VideoPause /></el-icon>
          停止监控
        </el-button>
      </div>

      <el-divider />

      <div class="stats-section">
        <el-statistic title="监控品种数" :value="store.symbols.length" />
        <el-statistic title="活跃品种数" :value="store.activeSymbolCount" />
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { VideoPause, VideoPlay } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useMonitorStore } from '../stores/monitor'

const store = useMonitorStore()

const isStarting = ref(false)
const isStopping = ref(false)

const symbolInput = computed({
  get: () => store.symbolInput,
  set: (value: string) => {
    store.symbolInput = value
  }
})

const parsedSymbols = computed(() => {
  const input = symbolInput.value.trim()
  if (!input) {
    return []
  }
  if (input.toUpperCase() === 'ALL') {
    return ['ALL']
  }
  return input
    .split('\n')
    .map(s => s.trim().toUpperCase())
    .filter(s => s.length > 0)
})

const parsedSymbolCount = computed(() => parsedSymbols.value.length)

const canStart = computed(() => parsedSymbolCount.value > 0 && !store.isRunning)

async function handleStart() {
  if (parsedSymbols.value.length === 0) {
    ElMessage.warning('请输入至少一个品种代码')
    return
  }

  isStarting.value = true
  try {
    await store.startMonitor(parsedSymbols.value)
    ElMessage.success('监控已启动')
  } catch {
    ElMessage.error('启动监控失败')
  } finally {
    isStarting.value = false
  }
}

async function handleStop() {
  isStopping.value = true
  try {
    await store.stopMonitor()
    ElMessage.success('监控已停止')
  } catch {
    ElMessage.error('停止监控失败')
  } finally {
    isStopping.value = false
  }
}
</script>

<style scoped>
.control-panel {
  height: 100%;
}

.card-header {
  font-weight: 600;
}

.control-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.input-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.input-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  color: #606266;
}

.button-section {
  display: flex;
  gap: 12px;
}

.stats-section {
  display: flex;
  justify-content: space-around;
}
</style>
