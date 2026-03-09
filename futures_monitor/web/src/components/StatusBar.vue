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
      <el-space wrap>
        <div class="status-item status-item--time">
          <span class="status-label">北京时间:</span>
          <div class="status-stack">
            <span class="status-value status-value--time">{{ beijingTimeText }}</span>
            <span class="status-subtext">{{ tradingSessionHint }}</span>
          </div>
        </div>
        <div class="status-item">
          <span class="status-label">交易时段:</span>
          <el-tag :type="tradingSessionType" size="small">
            {{ tradingSessionText }}
          </el-tag>
        </div>
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
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { TrendCharts } from '@element-plus/icons-vue'
import { useMonitorStore } from '../stores/monitor'

const store = useMonitorStore()
const now = ref(new Date())

const BEIJING_TIMEZONE = 'Asia/Shanghai'
const TRADING_SESSION_NOTE = '参考时段 09:00-11:30 / 13:30-15:00 / 21:00-23:00（部分品种夜盘）'

const timeFormatter = new Intl.DateTimeFormat('zh-CN', {
  timeZone: BEIJING_TIMEZONE,
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  weekday: 'short',
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
  hour12: false
})

const minuteFormatter = new Intl.DateTimeFormat('en-CA', {
  timeZone: BEIJING_TIMEZONE,
  weekday: 'short',
  hour: '2-digit',
  minute: '2-digit',
  hour12: false
})

const readBeijingClock = (value: Date) => {
  const parts = minuteFormatter.formatToParts(value)
  const weekdayToken = parts.find((part) => part.type === 'weekday')?.value ?? ''
  const hourToken = Number(parts.find((part) => part.type === 'hour')?.value ?? 0)
  const minuteToken = Number(parts.find((part) => part.type === 'minute')?.value ?? 0)
  const weekdayMap: Record<string, number> = {
    Mon: 1,
    Tue: 2,
    Wed: 3,
    Thu: 4,
    Fri: 5,
    Sat: 6,
    Sun: 0
  }

  return {
    weekday: weekdayMap[weekdayToken] ?? -1,
    minutesOfDay: hourToken * 60 + minuteToken
  }
}

const isWithinRange = (minutesOfDay: number, start: number, end: number) => {
  return minutesOfDay >= start && minutesOfDay < end
}

const tradingSession = computed(() => {
  const { weekday, minutesOfDay } = readBeijingClock(now.value)

  if (weekday === 0 || weekday === 6) {
    return {
      text: '休市',
      type: 'info' as const,
      hint: '周末休市，夜盘不开市'
    }
  }

  if (isWithinRange(minutesOfDay, 9 * 60, 11 * 60 + 30)) {
    return {
      text: '日盘',
      type: 'success' as const,
      hint: '日盘时段 09:00-11:30'
    }
  }

  if (isWithinRange(minutesOfDay, 11 * 60 + 30, 13 * 60 + 30)) {
    return {
      text: '午休',
      type: 'warning' as const,
      hint: '午休时段 11:30-13:30'
    }
  }

  if (isWithinRange(minutesOfDay, 13 * 60 + 30, 15 * 60)) {
    return {
      text: '日盘',
      type: 'success' as const,
      hint: '日盘时段 13:30-15:00'
    }
  }

  if (isWithinRange(minutesOfDay, 21 * 60, 23 * 60)) {
    return {
      text: '夜盘',
      type: 'success' as const,
      hint: '夜盘时段 21:00-23:00（部分品种）'
    }
  }

  return {
    text: '休市',
    type: 'info' as const,
    hint: '非统一交易时段，部分品种夜盘请以交易所规则为准'
  }
})

const beijingTimeText = computed(() => timeFormatter.format(now.value))
const tradingSessionText = computed(() => tradingSession.value.text)
const tradingSessionType = computed(() => tradingSession.value.type)
const tradingSessionHint = computed(() => `${tradingSession.value.hint} · ${TRADING_SESSION_NOTE}`)

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

let timer: ReturnType<typeof window.setInterval> | null = null

onMounted(() => {
  timer = window.setInterval(() => {
    now.value = new Date()
  }, 1000)
})

onBeforeUnmount(() => {
  if (timer !== null) {
    window.clearInterval(timer)
  }
})
</script>

<style scoped>
.status-bar {
  min-height: 60px;
  background-color: #fff;
  border-bottom: 1px solid #dcdfe6;
  padding: 8px 20px;
  display: flex;
  align-items: center;
}

.status-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  width: 100%;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
  color: #409eff;
  flex-shrink: 0;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-item--time {
  align-items: flex-start;
}

.status-label {
  font-size: 14px;
  color: #606266;
  white-space: nowrap;
}

.status-stack {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.status-value {
  font-size: 14px;
  color: #303133;
}

.status-value--time {
  font-weight: 600;
}

.status-subtext {
  font-size: 12px;
  color: #909399;
  line-height: 1.4;
  max-width: 420px;
}

@media (max-width: 1200px) {
  .status-content {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
