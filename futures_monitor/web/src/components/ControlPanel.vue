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
  <div class="control-panel-stack">
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

    <el-card class="config-panel" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>配置编辑</span>
          <el-tag v-if="store.config?.tq_account" size="small" type="success">已加载配置</el-tag>
        </div>
      </template>

      <el-form label-position="top" class="config-form">
        <el-form-item label="天勤账号">
          <el-input v-model="form.tq_account" placeholder="请输入 tq_account" />
        </el-form-item>

        <el-form-item label="天勤密码">
          <el-input
            v-model="form.tq_password"
            type="password"
            show-password
            placeholder="请输入 tq_password，点击右侧图标可查看真实密码"
          />
        </el-form-item>

        <el-form-item label="symbols">
          <el-input
            v-model="form.symbolsText"
            type="textarea"
            :rows="4"
            placeholder="每行一个品种代码，或输入 ALL"
          />
        </el-form-item>

        <div class="config-grid">
          <el-form-item label="take_profit_pct">
            <el-input-number v-model="form.take_profit_pct" :min="0" :max="1" :step="0.01" :precision="2" />
          </el-form-item>

          <el-form-item label="stop_loss_pct">
            <el-input-number v-model="form.stop_loss_pct" :min="0" :max="1" :step="0.01" :precision="2" />
          </el-form-item>
        </div>

        <div class="config-switches">
          <el-switch
            v-model="form.use_real_market_data"
            inline-prompt
            active-text="真实行情"
            inactive-text="Mock 行情"
          />
          <el-switch
            v-model="form.strict_real_mode"
            inline-prompt
            active-text="严格模式"
            inactive-text="允许回退"
          />
        </div>

        <div class="config-actions">
          <el-button :loading="isRefreshingConfig" @click="handleRefreshConfig">刷新配置</el-button>
          <el-button type="primary" :loading="isSavingConfig" @click="handleSaveConfig">保存配置</el-button>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { VideoPause, VideoPlay } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useMonitorStore } from '../stores/monitor'

const store = useMonitorStore()

const isStarting = ref(false)
const isStopping = ref(false)
const isSavingConfig = ref(false)
const isRefreshingConfig = ref(false)

const form = reactive({
  tq_account: '',
  tq_password: '',
  symbolsText: '',
  take_profit_pct: 0.5,
  stop_loss_pct: 0.5,
  use_real_market_data: false,
  strict_real_mode: true
})

function syncFormFromStore(): void {
  form.tq_account = store.config?.tq_account ?? ''
  form.tq_password = store.config?.tq_password ?? ''
  form.symbolsText = store.config?.symbols.join('\n') ?? ''
  form.take_profit_pct = store.config?.take_profit_pct ?? 0.5
  form.stop_loss_pct = store.config?.stop_loss_pct ?? 0.5
  form.use_real_market_data = store.config?.use_real_market_data ?? false
  form.strict_real_mode = store.config?.strict_real_mode ?? true
}

watch(() => store.config, syncFormFromStore, { immediate: true })

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

const parsedConfigSymbols = computed(() => {
  const input = form.symbolsText.trim()
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

async function handleRefreshConfig() {
  isRefreshingConfig.value = true
  try {
    await store.refreshConfig()
    ElMessage.success('配置已刷新')
  } catch (error) {
    const detail = error instanceof Error ? error.message : String(error)
    ElMessage.error(`刷新配置失败: ${detail}`)
  } finally {
    isRefreshingConfig.value = false
  }
}

async function handleSaveConfig() {
  isSavingConfig.value = true
  try {
    await store.saveConfig({
      tq_account: form.tq_account.trim(),
      tq_password: form.tq_password,
      symbols: parsedConfigSymbols.value,
      take_profit_pct: form.take_profit_pct,
      stop_loss_pct: form.stop_loss_pct,
      use_real_market_data: form.use_real_market_data,
      strict_real_mode: form.strict_real_mode
    })
    ElMessage.success('配置保存成功，已刷新为最新状态')
  } catch (error) {
    const detail = error instanceof Error ? error.message : String(error)
    ElMessage.error(`保存配置失败: ${detail}`)
  } finally {
    isSavingConfig.value = false
  }
}
</script>

<style scoped>
.control-panel-stack {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.control-panel,
.config-panel {
  height: 100%;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  font-weight: 600;
}

.control-content,
.config-form {
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

.button-section,
.config-actions,
.config-switches {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.stats-section {
  display: flex;
  justify-content: space-around;
}

.config-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

@media (max-width: 768px) {
  .config-grid {
    grid-template-columns: 1fr;
  }
}
</style>
