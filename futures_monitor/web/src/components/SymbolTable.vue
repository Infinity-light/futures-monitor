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
      <el-table-column prop="symbol" label="品种代码" width="100" fixed />

      <el-table-column prop="status" label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)" size="small">
            {{ getStatusText(row.status) }}
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
          <span :class="{ 'profit-text': row.takeProfit }">
            {{ formatPrice(row.takeProfit) }}
          </span>
        </template>
      </el-table-column>

      <el-table-column prop="stopLoss" label="止损价" width="100">
        <template #default="{ row }">
          <span :class="{ 'loss-text': row.stopLoss }">
            {{ formatPrice(row.stopLoss) }}
          </span>
        </template>
      </el-table-column>

      <el-table-column prop="lastEvent" label="最后事件" min-width="150" show-overflow-tooltip>
        <template #default="{ row }">
          {{ row.lastEvent || '-' }}
        </template>
      </el-table-column>

      <el-table-column label="操作" width="100" fixed="right">
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { useMonitorStore, type SymbolStatus } from '../stores/monitor'

const store = useMonitorStore()

function getStatusType(status: SymbolStatus): string {
  const typeMap: Record<SymbolStatus, string> = {
    MONITORING: 'info',
    BREAKOUT_DETECTED: 'danger',
    BOUGHT: 'success',
    STOPPED: 'warning'
  }
  return typeMap[status] || 'info'
}

function getStatusText(status: SymbolStatus): string {
  const textMap: Record<SymbolStatus, string> = {
    MONITORING: '监控中',
    BREAKOUT_DETECTED: '突破检测',
    BOUGHT: '已买入',
    STOPPED: '已停止'
  }
  return textMap[status] || status
}

function formatPrice(price: number | null): string {
  if (price === null || price === undefined) return '-'
  return price.toFixed(2)
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

.profit-text {
  color: #67c23a;
  font-weight: 600;
}

.loss-text {
  color: #f56c6c;
  font-weight: 600;
}
</style>
