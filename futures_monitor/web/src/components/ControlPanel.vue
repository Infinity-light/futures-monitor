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
          <div class="field-help">启动监控时将使用当前配置中的认证信息、行情模式和风控参数。</div>
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
        <div class="card-header config-header">
          <div>
            <div class="config-title-row">
              <span>监控配置</span>
              <el-tag v-if="store.config?.tq_account" size="small" type="success">已加载配置</el-tag>
            </div>
            <div class="card-subtitle">认证信息、行情模式、风控参数和 symbols 在此集中维护，避免隐藏入口。</div>
          </div>
          <div class="config-actions header-actions">
            <el-button :loading="isRefreshingConfig" @click="handleRefreshConfig">刷新配置</el-button>
            <el-button type="primary" :loading="isSavingConfig" @click="handleSaveConfig">保存配置</el-button>
          </div>
        </div>
      </template>

      <el-form label-position="top" class="config-form">
        <section class="config-section">
          <div class="section-heading">
            <h3>认证信息</h3>
            <p>仅在开启真实行情时使用。请填写可用于 TqSdk/快期认证的快期账户和对应密码。</p>
          </div>
          <el-alert
            type="warning"
            :closable="false"
            show-icon
            title="这里不是期货实盘账号，也不是普通模拟交易编号。"
            description="请填写可用于 TqSdk/快期认证的快期账户（手机号、邮箱或用户名）和对应密码。"
          />
          <div class="config-grid two-columns">
            <el-form-item label="快期认证账户">
              <el-input
                v-model="form.tq_account"
                placeholder="请输入快期账户（手机号 / 邮箱 / 用户名）"
                autocomplete="username"
              />
            </el-form-item>

            <el-form-item label="快期认证密码">
              <el-input
                v-model="form.tq_password"
                type="password"
                show-password
                placeholder="请输入与该快期账户对应的密码"
                autocomplete="current-password"
              />
            </el-form-item>
          </div>
        </section>

        <section class="config-section">
          <div class="section-heading">
            <h3>行情模式</h3>
            <p>决定监控使用真实行情还是 Mock 行情，以及真实行情失败时是否允许回退。</p>
          </div>
          <div class="config-grid two-columns">
            <div class="setting-card">
              <div class="setting-card__header">
                <span>行情来源</span>
                <el-switch
                  v-model="form.use_real_market_data"
                  inline-prompt
                  active-text="真实行情"
                  inactive-text="Mock 行情"
                />
              </div>
              <p class="setting-card__desc">开启后会使用快期/TqSdk 认证连接真实行情；关闭时使用本地 Mock 行情。</p>
            </div>
            <div class="setting-card">
              <div class="setting-card__header">
                <span>真实行情失败处理</span>
                <el-switch
                  v-model="form.strict_real_mode"
                  inline-prompt
                  active-text="严格模式"
                  inactive-text="允许回退"
                />
              </div>
              <p class="setting-card__desc">严格模式下认证或连接失败会直接报错；关闭后可自动回退到 Mock 行情。</p>
            </div>
          </div>
        </section>

        <section class="config-section">
          <div class="section-heading">
            <h3>风控参数</h3>
            <p>用于突破后的止盈止损提醒，建议按策略要求维护。</p>
          </div>
          <div class="config-grid two-columns">
            <el-form-item label="止盈比例 take_profit_pct">
              <el-input-number v-model="form.take_profit_pct" :min="0" :max="1" :step="0.01" :precision="2" />
            </el-form-item>

            <el-form-item label="止损比例 stop_loss_pct">
              <el-input-number v-model="form.stop_loss_pct" :min="0" :max="1" :step="0.01" :precision="2" />
            </el-form-item>
          </div>
        </section>

        <section class="config-section">
          <div class="section-heading">
            <h3>监控 symbols</h3>
            <p>支持逐行填写合约代码，也支持输入 ALL 自动解析当前有效合约。</p>
          </div>
          <el-form-item label="symbols 列表">
            <el-input
              v-model="form.symbolsText"
              type="textarea"
              :rows="5"
              placeholder="每行一个品种代码，或输入 ALL"
            />
          </el-form-item>
        </section>

        <div class="config-actions footer-actions">
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
  } catch (error) {
    const detail = error instanceof Error ? error.message : String(error)
    ElMessage.error(`启动监控失败：${detail}`)
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

.config-header {
  align-items: flex-start;
}

.config-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.card-subtitle {
  font-size: 13px;
  line-height: 1.6;
  color: #909399;
  font-weight: 400;
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

.field-help {
  font-size: 12px;
  line-height: 1.6;
  color: #909399;
}

.button-section,
.config-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.header-actions {
  justify-content: flex-end;
}

.footer-actions {
  padding-top: 4px;
}

.stats-section {
  display: flex;
  justify-content: space-around;
}

.config-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  border: 1px solid #ebeef5;
  border-radius: 12px;
  background: linear-gradient(180deg, #ffffff 0%, #fafcff 100%);
}

.section-heading {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.section-heading h3 {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.section-heading p {
  font-size: 13px;
  line-height: 1.6;
  color: #909399;
}

.config-grid {
  display: grid;
  gap: 12px;
}

.two-columns {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.setting-card {
  border: 1px solid #e4e7ed;
  border-radius: 10px;
  padding: 14px;
  background-color: #fff;
}

.setting-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
  font-weight: 500;
  color: #303133;
}

.setting-card__desc {
  font-size: 12px;
  line-height: 1.6;
  color: #909399;
}

:deep(.el-form-item) {
  margin-bottom: 0;
}

@media (max-width: 768px) {
  .config-header,
  .card-header,
  .setting-card__header,
  .stats-section,
  .config-title-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .header-actions,
  .config-actions {
    width: 100%;
  }

  .header-actions :deep(.el-button),
  .footer-actions :deep(.el-button) {
    flex: 1;
  }

  .two-columns {
    grid-template-columns: 1fr;
  }
}
</style>
