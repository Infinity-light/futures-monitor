/**
 * role: Define monitor state container contract for dashboard usage.
 * depends:
 *   - pinia
 *   - ../services/api
 * exports:
 *   - useMonitorStore
 * status: IMPLEMENTED
 * functions:
 *   - useMonitorStore() -> Store
 *   - startMonitor(symbols: string[]) -> Promise<void>
 *   - stopMonitor() -> Promise<void>
 *   - markBought(symbol: string) -> Promise<void>
 *   - handleRowUpdate(data: SymbolRowData) -> void
 *   - addLog(entry: LogEntry) -> void
 */

import { defineStore } from 'pinia'
import {
  controlMonitor,
  getConfig,
  getMonitorStatus,
  markBought as markBoughtApi,
  type ConfigResponse,
  type MonitorStatus
} from '../services/api'

export type ConnectionStatus = 'connected' | 'connecting' | 'disconnected' | 'error'

export type SymbolStatus = 'MONITORING' | 'BREAKOUT_DETECTED' | 'HOLDING' | 'STOPPED'

export interface SymbolRow {
  symbol: string
  status: SymbolStatus
  lastPrice: number | null
  dayHigh: number | null
  dayLow: number | null
  breakoutPrice: number | null
  takeProfit: number | null
  stopLoss: number | null
  lastEvent: string | null
  hasBought: boolean
}

export interface LogEntry {
  timestamp: string
  level: 'INFO' | 'WARNING' | 'ERROR'
  message: string
}

export interface SymbolRowData {
  symbol: string
  status?: string
  last_price?: number | null
  day_high?: number | null
  day_low?: number | null
  breakout_price?: number | null
  take_profit?: number | null
  stop_loss?: number | null
  last_event?: string
  has_bought?: boolean
}

function normalizeConnectionStatus(status: string): ConnectionStatus {
  switch (status) {
    case 'connected':
    case 'connecting':
    case 'disconnected':
    case 'error':
      return status
    case '已连接':
      return 'connected'
    case '连接中':
      return 'connecting'
    case '已断开':
    case '未连接':
      return 'disconnected'
    case '连接失败':
      return 'error'
    default:
      return 'disconnected'
  }
}

function normalizeSymbolStatus(status?: string): SymbolStatus {
  switch (status) {
    case 'BREAKOUT_DETECTED':
      return 'BREAKOUT_DETECTED'
    case 'HOLDING':
    case 'BOUGHT':
      return 'HOLDING'
    case 'STOPPED':
      return 'STOPPED'
    case 'MONITORING':
    default:
      return 'MONITORING'
  }
}

export const useMonitorStore = defineStore('monitor', {
  state: () => ({
    symbols: [] as string[],
    symbolInput: '' as string,
    config: null as ConfigResponse | null,
    isRunning: false,
    connectionStatus: 'disconnected' as ConnectionStatus,
    symbolData: new Map<string, SymbolRow>(),
    logs: [] as LogEntry[]
  }),

  getters: {
    sortedSymbols(state): SymbolRow[] {
      const rows = Array.from(state.symbolData.values())
      return rows.sort((a, b) => a.symbol.localeCompare(b.symbol))
    },

    activeSymbolCount(state): number {
      return Array.from(state.symbolData.values()).filter(
        row => row.status === 'MONITORING' || row.status === 'BREAKOUT_DETECTED' || row.status === 'HOLDING'
      ).length
    }
  },

  actions: {
    async startMonitor(symbols: string[]): Promise<void> {
      try {
        const status = await controlMonitor('start', symbols)
        this.applyStatusSnapshot(status)
      } catch (error) {
        this.addLog({
          timestamp: new Date().toISOString(),
          level: 'ERROR',
          message: `启动监控失败: ${error instanceof Error ? error.message : String(error)}`
        })
        throw error
      }
    },

    async stopMonitor(): Promise<void> {
      try {
        const status = await controlMonitor('stop')
        this.applyStatusSnapshot(status)
      } catch (error) {
        this.addLog({
          timestamp: new Date().toISOString(),
          level: 'ERROR',
          message: `停止监控失败: ${error instanceof Error ? error.message : String(error)}`
        })
        throw error
      }
    },

    async markBought(symbol: string): Promise<void> {
      try {
        await markBoughtApi(symbol)
      } catch (error) {
        this.addLog({
          timestamp: new Date().toISOString(),
          level: 'ERROR',
          message: `标记买入失败: ${error instanceof Error ? error.message : String(error)}`
        })
        throw error
      }
    },

    handleRowUpdate(data: SymbolRowData): void {
      const existing = this.symbolData.get(data.symbol)
      const row: SymbolRow = {
        symbol: data.symbol,
        status: normalizeSymbolStatus(data.status) || existing?.status || 'MONITORING',
        lastPrice: data.last_price ?? existing?.lastPrice ?? null,
        dayHigh: data.day_high ?? existing?.dayHigh ?? null,
        dayLow: data.day_low ?? existing?.dayLow ?? null,
        breakoutPrice: data.breakout_price ?? existing?.breakoutPrice ?? null,
        takeProfit: data.take_profit ?? existing?.takeProfit ?? null,
        stopLoss: data.stop_loss ?? existing?.stopLoss ?? null,
        lastEvent: data.last_event ?? existing?.lastEvent ?? null,
        hasBought: data.has_bought ?? existing?.hasBought ?? false
      }
      this.symbolData.set(data.symbol, row)
      if (!this.symbols.includes(data.symbol)) {
        this.symbols = [...this.symbols, data.symbol]
      }
    },

    addLog(entry: LogEntry): void {
      this.logs.push(entry)
      if (this.logs.length > 100) {
        this.logs.shift()
      }
    },

    clearLogs(): void {
      this.logs = []
    },

    setConnectionStatus(status: ConnectionStatus): void {
      this.connectionStatus = status
    },

    setRunningStatus(isRunning: boolean): void {
      this.isRunning = isRunning
    },

    async initialize(): Promise<void> {
      this.symbols = []
      this.isRunning = false
      this.connectionStatus = 'disconnected'
      this.symbolData.clear()
      this.logs = []

      const [config, status] = await Promise.all([getConfig(), getMonitorStatus()])
      this.config = config
      this.symbolInput = config.symbols.join('\n')
      this.applyStatusSnapshot(status)
    },

    applyStatusSnapshot(status: MonitorStatus): void {
      this.isRunning = status.running
      this.symbols = status.symbols
      this.connectionStatus = normalizeConnectionStatus(status.connection_status)
      this.symbolData = new Map()
      status.rows.forEach(row => this.handleRowUpdate(row))
    }
  }
})
