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
          <div class="input-label input-label--top">
            <div>
              <span>监控品种</span>
              <div class="field-help">名称主、代码辅；保存与启动只提交程序值，不再手输 ALL。</div>
            </div>
            <el-tag size="small" type="info">当前将启动 {{ selectionSummary }}</el-tag>
          </div>

          <el-radio-group v-model="controlSelectionMode" :disabled="store.isRunning" class="selection-mode-group">
            <el-radio-button label="all">全部市场</el-radio-button>
            <el-radio-button label="exchange">按交易所</el-radio-button>
            <el-radio-button label="custom">自定义</el-radio-button>
          </el-radio-group>

          <div v-if="controlSelectionMode === 'exchange'" class="selector-panel">
            <el-checkbox-group v-model="controlSelectionExchanges" :disabled="store.isRunning" class="exchange-grid">
              <el-checkbox v-for="item in exchangeOptions" :key="item.value" :label="item.value">
                {{ item.label }}
              </el-checkbox>
            </el-checkbox-group>
          </div>

          <div v-else-if="controlSelectionMode === 'custom'" class="selector-panel">
            <el-select
              v-model="controlSelectionSymbols"
              multiple
              filterable
              collapse-tags
              collapse-tags-tooltip
              :max-collapse-tags="2"
              placeholder="搜索并选择品种"
              :disabled="store.isRunning"
              class="symbol-select"
            >
              <el-option
                v-for="candidate in filteredCandidates"
                :key="candidate.value"
                :label="formatCandidateLabel(candidate)"
                :value="candidate.value"
              >
                <div class="candidate-option">
                  <span class="candidate-option__name">{{ candidate.name }}</span>
                  <span class="candidate-option__meta">{{ candidate.code }} · {{ exchangeName(candidate.exchange) }}</span>
                </div>
              </el-option>
            </el-select>
            <div class="selected-preview" v-if="selectedControlCandidates.length > 0">
              <el-tag v-for="candidate in selectedControlCandidates" :key="candidate.value" size="small" class="preview-tag">
                {{ candidate.name }}（{{ candidate.code }}）
              </el-tag>
            </div>
          </div>

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
            <div class="card-subtitle">认证信息、行情模式、风控参数和品种选择在此集中维护，避免隐藏入口。</div>
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
            <p>用于突破后的止盈止损提醒，以及预突破试探提示的触发阈值。</p>
          </div>
          <div class="config-grid two-columns">
            <el-form-item label="止盈比例 take_profit_pct">
              <el-input-number v-model="form.take_profit_pct" :min="0" :max="1" :step="0.01" :precision="2" />
            </el-form-item>

            <el-form-item label="止损比例 stop_loss_pct">
              <el-input-number v-model="form.stop_loss_pct" :min="0" :max="1" :step="0.01" :precision="2" />
            </el-form-item>

            <el-form-item label="预突破目标次数 probe_target_count">
              <el-input-number v-model="form.probe_target_count" :min="1" :max="9" :step="1" :precision="0" />
            </el-form-item>

            <el-form-item label="预突破阈值 probe_distance_ratio">
              <el-input-number v-model="form.probe_distance_ratio" :min="0" :max="1" :step="0.05" :precision="2" />
            </el-form-item>
          </div>
          <div class="field-help">当价格接近当前观察突破位到设定阈值内时，系统会累计试探次数并展示黄色进度条，最多显示到目标次数。</div>
        </section>

        <section class="config-section">
          <div class="section-heading">
            <h3>品种选择</h3>
            <p>使用结构化选择模式；展示为中文名（代码），保存为程序值，兼容旧版 symbols 配置。</p>
          </div>

          <el-form-item label="选择模式">
            <el-radio-group v-model="form.selection_mode" class="selection-mode-group">
              <el-radio-button label="all">全部市场</el-radio-button>
              <el-radio-button label="exchange">按交易所</el-radio-button>
              <el-radio-button label="custom">自定义</el-radio-button>
            </el-radio-group>
          </el-form-item>

          <el-form-item v-if="form.selection_mode === 'exchange'" label="交易所范围">
            <el-checkbox-group v-model="form.selection_exchanges" class="exchange-grid">
              <el-checkbox v-for="item in exchangeOptions" :key="item.value" :label="item.value">
                {{ item.label }}
              </el-checkbox>
            </el-checkbox-group>
          </el-form-item>

          <el-form-item v-if="form.selection_mode === 'custom'" label="自定义品种">
            <el-select
              v-model="form.selection_symbols"
              multiple
              filterable
              collapse-tags
              collapse-tags-tooltip
              :max-collapse-tags="3"
              placeholder="搜索并选择品种"
              class="symbol-select"
            >
              <el-option
                v-for="candidate in filteredCandidates"
                :key="candidate.value"
                :label="formatCandidateLabel(candidate)"
                :value="candidate.value"
              >
                <div class="candidate-option">
                  <span class="candidate-option__name">{{ candidate.name }}</span>
                  <span class="candidate-option__meta">{{ candidate.code }} · {{ exchangeName(candidate.exchange) }}</span>
                </div>
              </el-option>
            </el-select>
            <div class="selected-preview" v-if="selectedFormCandidates.length > 0">
              <el-tag v-for="candidate in selectedFormCandidates" :key="candidate.value" size="small" class="preview-tag">
                {{ candidate.name }}（{{ candidate.code }}）
              </el-tag>
            </div>
          </el-form-item>

          <el-alert
            type="info"
            :closable="false"
            show-icon
            :title="`当前配置摘要：${configSelectionSummary}`"
          />
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
import type { SymbolCandidate } from '../services/api'

const store = useMonitorStore()

const isStarting = ref(false)
const isStopping = ref(false)
const isSavingConfig = ref(false)
const isRefreshingConfig = ref(false)

const exchangeOptions = [
  { value: 'SHFE', label: '上期所 SHFE' },
  { value: 'DCE', label: '大商所 DCE' },
  { value: 'CZCE', label: '郑商所 CZCE' },
  { value: 'CFFEX', label: '中金所 CFFEX' },
  { value: 'INE', label: '上期能源 INE' },
  { value: 'GFEX', label: '广期所 GFEX' }
]

const form = reactive({
  tq_account: '',
  tq_password: '',
  selection_mode: 'all' as 'all' | 'exchange' | 'custom',
  selection_exchanges: [] as string[],
  selection_symbols: [] as string[],
  take_profit_pct: 0.5,
  stop_loss_pct: 0.5,
  probe_target_count: 3,
  probe_distance_ratio: 0.2,
  use_real_market_data: false,
  strict_real_mode: true
})

const controlSelectionMode = ref<'all' | 'exchange' | 'custom'>('all')
const controlSelectionExchanges = ref<string[]>([])
const controlSelectionSymbols = ref<string[]>([])

function exchangeName(exchange: string): string {
  return exchangeOptions.find(item => item.value === exchange)?.label ?? exchange
}

function formatCandidateLabel(candidate: SymbolCandidate): string {
  return `${candidate.name}（${candidate.code}）`
}

const candidateMap = computed(() => {
  return new Map(store.symbolCandidates.map(candidate => [candidate.value, candidate]))
})

const filteredCandidates = computed(() => {
  if (form.selection_mode !== 'custom' && controlSelectionMode.value !== 'custom') {
    return store.symbolCandidates
  }

  const exchanges = form.selection_mode === 'custom'
    ? form.selection_exchanges
    : controlSelectionExchanges.value

  if (!exchanges.length) {
    return store.symbolCandidates
  }
  return store.symbolCandidates.filter(candidate => exchanges.includes(candidate.exchange))
})

const selectedFormCandidates = computed(() => {
  return form.selection_symbols
    .map(value => candidateMap.value.get(value))
    .filter((candidate): candidate is SymbolCandidate => Boolean(candidate))
})

const selectedControlCandidates = computed(() => {
  return controlSelectionSymbols.value
    .map(value => candidateMap.value.get(value))
    .filter((candidate): candidate is SymbolCandidate => Boolean(candidate))
})

function summarizeSelection(mode: 'all' | 'exchange' | 'custom', exchanges: string[], symbols: string[]): string {
  if (mode === 'all') {
    return '全部市场'
  }
  if (mode === 'exchange') {
    return exchanges.length ? `交易所：${exchanges.map(exchangeName).join('、')}` : '请选择至少一个交易所'
  }
  if (symbols.length === 0) {
    return '请选择至少一个品种'
  }
  return symbols
    .map(value => candidateMap.value.get(value))
    .filter((candidate): candidate is SymbolCandidate => Boolean(candidate))
    .map(candidate => `${candidate.name}（${candidate.code}）`)
    .join('、')
}

const selectionSummary = computed(() => summarizeSelection(
  controlSelectionMode.value,
  controlSelectionExchanges.value,
  controlSelectionSymbols.value
))

const configSelectionSummary = computed(() => summarizeSelection(
  form.selection_mode,
  form.selection_exchanges,
  form.selection_symbols
))

function syncFormFromStore(): void {
  form.tq_account = store.config?.tq_account ?? ''
  form.tq_password = store.config?.tq_password ?? ''
  form.selection_mode = store.config?.selection_mode ?? 'all'
  form.selection_exchanges = [...(store.config?.selection_exchanges ?? [])]
  form.selection_symbols = [...(store.config?.selection_symbols ?? [])]
  form.take_profit_pct = store.config?.take_profit_pct ?? 0.5
  form.stop_loss_pct = store.config?.stop_loss_pct ?? 0.5
  form.probe_target_count = store.config?.probe_target_count ?? 3
  form.probe_distance_ratio = store.config?.probe_distance_ratio ?? 0.2
  form.use_real_market_data = store.config?.use_real_market_data ?? false
  form.strict_real_mode = store.config?.strict_real_mode ?? true

  controlSelectionMode.value = store.selectionMode
  controlSelectionExchanges.value = [...store.selectionExchanges]
  controlSelectionSymbols.value = [...(store.selectionMode === 'custom' ? store.symbols : store.config?.selection_symbols ?? [])]
}

watch(() => store.config, syncFormFromStore, { immediate: true })
watch(controlSelectionMode, mode => {
  if (mode !== 'exchange') {
    controlSelectionExchanges.value = []
  }
  if (mode !== 'custom') {
    controlSelectionSymbols.value = []
  }
})
watch(() => form.selection_mode, mode => {
  if (mode !== 'exchange') {
    form.selection_exchanges = []
  }
  if (mode !== 'custom') {
    form.selection_symbols = []
  }
})

const canStart = computed(() => {
  if (store.isRunning) {
    return false
  }
  if (controlSelectionMode.value === 'all') {
    return true
  }
  if (controlSelectionMode.value === 'exchange') {
    return controlSelectionExchanges.value.length > 0
  }
  return controlSelectionSymbols.value.length > 0
})

function buildStartPayload() {
  return {
    selection_mode: controlSelectionMode.value,
    selection_exchanges: [...controlSelectionExchanges.value],
    symbols: controlSelectionMode.value === 'custom' ? [...controlSelectionSymbols.value] : []
  }
}

async function handleStart() {
  if (!canStart.value) {
    ElMessage.warning('请先完成品种选择')
    return
  }

  isStarting.value = true
  try {
    await store.startMonitor(buildStartPayload())
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
  if (form.selection_mode === 'exchange' && form.selection_exchanges.length === 0) {
    ElMessage.warning('请选择至少一个交易所')
    return
  }
  if (form.selection_mode === 'custom' && form.selection_symbols.length === 0) {
    ElMessage.warning('请选择至少一个品种')
    return
  }

  isSavingConfig.value = true
  try {
    await store.saveConfig({
      tq_account: form.tq_account.trim(),
      tq_password: form.tq_password,
      selection_mode: form.selection_mode,
      selection_exchanges: [...form.selection_exchanges],
      selection_symbols: [...form.selection_symbols],
      symbols: form.selection_mode === 'custom' ? [...form.selection_symbols] : [],
      take_profit_pct: form.take_profit_pct,
      stop_loss_pct: form.stop_loss_pct,
      probe_target_count: form.probe_target_count,
      probe_distance_ratio: form.probe_distance_ratio,
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
  gap: 12px;
}

.input-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  color: #606266;
}

.input-label--top {
  align-items: flex-start;
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

.selection-mode-group {
  display: flex;
  flex-wrap: wrap;
}

.selector-panel {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.exchange-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.symbol-select {
  width: 100%;
}

.candidate-option {
  display: flex;
  flex-direction: column;
  gap: 2px;
  line-height: 1.4;
}

.candidate-option__name {
  color: #303133;
}

.candidate-option__meta {
  font-size: 12px;
  color: #909399;
}

.selected-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.preview-tag {
  max-width: 100%;
}

:deep(.el-form-item) {
  margin-bottom: 0;
}

@media (max-width: 768px) {
  .config-header,
  .card-header,
  .setting-card__header,
  .stats-section,
  .config-title-row,
  .input-label {
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

  .two-columns,
  .exchange-grid {
    grid-template-columns: 1fr;
  }
}
</style>
