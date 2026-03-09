<!--
role: Render monitored symbol table with real-time data.
depends:
  - vue
  - element-plus
  - ../stores/monitor
exports:
  - SymbolTable
status: IMPLEMENTED
functions:
  - renderSymbolTable() -> VNode
-->
<template>
  <el-card class="symbol-table" shadow="hover">
    <template #header>
      <div class="card-header">
        <span>品种监控</span>
        <el-tag size="small" type="info">{{ store.sortedSymbols.length }} 个品种</el-tag>
      </div>
    </template>

    <el-table
      :data="store.sortedSymbols"
      style="width: 100%"
      height="100%"
      v-loading="store.connectionStatus === 'connecting'"
    >
      <el-table-column label="品种" min-width="260" fixed>
        <template #default="{ row }">
          <div class="symbol-cell">
            <div class="symbol-cell__header">
              <div class="symbol-cell__identity">
                <span class="symbol-cell__name">{{ row.name || row.displaySymbol || row.symbol }}</span>
                <span class="symbol-cell__meta">{{ row.displaySymbol || row.symbol }}</span>
              </div>
              <div class="probe-icons" v-if="row.probeIconLevel > 0 && row.status === 'MONITORING'">
                <span v-for="level in row.probeIconLevel" :key="level" class="probe-icons__dot"></span>
              </div>
            </div>
            <div class="probe-panel" v-if="row.status === 'MONITORING' || row.status === 'BREAKOUT_DETECTED'">
              <div class="probe-panel__topline">
                <span class="probe-panel__text">{{ row.probeStateText || getStatusText(row.status) }}</span>
                <span class="probe-panel__count" v-if="row.probeCount > 0">{{ row.probeCount }} / {{ probeTargetCount }}</span>
              </div>
              <el-progress
                :percentage="normalizeProgress(row.probeProgress)"
                :stroke-width="6"
                :show-text="false"
                :color="row.status === 'BREAKOUT_DETECTED' ? '#f56c6c' : '#e6a23c'"
              />
            </div>
          </div>
        </template>
      </el-table-column>

      <el-table-column prop="status" label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)" size="small">
            {{ row.probeStateText && row.status === 'BREAKOUT_DETECTED' ? row.probeStateText : getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column prop="lastPrice" label="最新价" width="100">
        <template #default="{ row }">
          {{ formatPrice(row.lastPrice) }}
        </template>
      </el-table-column>

      <el-table-column prop="dayHigh" label="日高" width="100">
        <template #default="{ row }">
          {{ formatPrice(row.dayHigh) }}
        </template>
      </el-table-column>

      <el-table-column prop="dayLow" label="日低" width="100">
        <template #default="{ row }">
          {{ formatPrice(row.dayLow) }}
        </template>
      </el-table-column>

      <el-table-column prop="breakoutPrice" label="突破价" width="100">
        <template #default="{ row }">
          {{ formatPrice(row.breakoutPrice) }}
        </template>
      </el-table-column>

      <el-table-column prop="takeProfit" label="止盈价" width="100">
        <template #default="{ row }">
          <span :class="{ 'profit-text': row.takeProfit !== null }">
            {{ formatPrice(row.takeProfit) }}
          </span>
        </template>
      </el-table-column>

      <el-table-column prop="stopLoss" label="止损价" width="100">
        <template #default="{ row }">
          <span :class="{ 'loss-text': row.stopLoss !== null }">
            {{ formatPrice(row.stopLoss) }}
          </span>
        </template>
      </el-table-column>

      <el-table-column prop="lastEvent" label="最后事件" min-width="180" show-overflow-tooltip>
        <template #default="{ row }">
          {{ row.lastEvent || '-' }}
        </template>
      </el-table-column>

      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="row.status === 'BREAKOUT_DETECTED'"
            type="primary"
            size="small"
            @click="handleMarkBought(row.symbol)"
          >
            标记买入
          </el-button>
          <el-tag v-else-if="row.hasBought" type="success" size="small">已买入</el-tag>
          <span v-else>-</span>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useMonitorStore, type SymbolStatus } from '../stores/monitor'

const store = useMonitorStore()
const probeTargetCount = computed(() => store.config?.probe_target_count ?? 3)

function getStatusType(status: SymbolStatus): string {
  const typeMap: Record<SymbolStatus, string> = {
    MONITORING: 'info',
    BREAKOUT_DETECTED: 'danger',
    HOLDING: 'success',
    STOPPED: 'warning'
  }
  return typeMap[status] || 'info'
}

function getStatusText(status: SymbolStatus): string {
  const textMap: Record<SymbolStatus, string> = {
    MONITORING: '监控中',
    BREAKOUT_DETECTED: '突破检测',
    HOLDING: '已持仓',
    STOPPED: '已停止'
  }
  return textMap[status] || status
}

function formatPrice(price: number | null): string {
  if (price === null || price === undefined) return '-'
  return price.toFixed(2)
}

function normalizeProgress(value: number): number {
  return Math.max(0, Math.min(100, Math.round(value || 0)))
}

async function handleMarkBought(symbol: string) {
  try {
    await ElMessageBox.confirm(
      `确定要标记 ${symbol} 为已买入吗？`,
      '确认买入',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await store.markBought(symbol)
    ElMessage.success(`已标记 ${symbol} 为买入`)
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('标记买入失败')
    }
  }
}
</script>

<style scoped>
.symbol-table {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

:deep(.el-card__body) {
  flex: 1;
  overflow: hidden;
  padding: 0;
}

.symbol-cell {
  display: flex;
  flex-direction: column;
  gap: 6px;
  line-height: 1.4;
}

.symbol-cell__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}

.symbol-cell__identity {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.symbol-cell__name {
  color: #303133;
  font-weight: 600;
}

.symbol-cell__meta {
  font-size: 12px;
  color: #909399;
}

.probe-icons {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding-top: 2px;
}

.probe-icons__dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #e6a23c;
  box-shadow: 0 0 0 2px rgba(230, 162, 60, 0.15);
}

.probe-panel {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.probe-panel__topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  font-size: 12px;
  color: #606266;
}

.probe-panel__text {
  color: #8a5b00;
}

.probe-panel__count {
  color: #909399;
}

.profit-text {
  color: #67c23a;
  font-weight: 600;
}

.loss-text {
  color: #f56c6c;
  font-weight: 600;
}
</style>
