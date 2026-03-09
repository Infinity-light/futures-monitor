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
 *   - startMonitor(payload) -> Promise<void>
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
  updateConfig,
  type ConfigResponse,
  type ConfigUpdate,
  type MonitorStatus,
  type MonitorStartRequest,
  type SymbolCandidate
} from '../services/api'

export type ConnectionStatus = 'connected' | 'connecting' | 'disconnected' | 'error'

export type SymbolStatus = 'MONITORING' | 'BREAKOUT_DETECTED' | 'HOLDING' | 'STOPPED'

export interface SymbolRow {
  symbol: string
  displaySymbol: string
  name: string
  exchange: string
  status: SymbolStatus
  lastPrice: number | null
  dayHigh: number | null
  dayLow: number | null
  breakoutPrice: number | null
  takeProfit: number | null
  stopLoss: number | null
  lastEvent: string | null
  hasBought: boolean
  probeCount: number
  probeProgress: number
  probeIconLevel: number
  probeStateText: string
}

export interface LogEntry {
  timestamp: string
  level: 'INFO' | 'WARNING' | 'ERROR'
  message: string
}

export interface SymbolRowData {
  symbol: string
  display_symbol?: string
  name?: string
  exchange?: string
  status?: string
  last_price?: number | null
  day_high?: number | null
  day_low?: number | null
  breakout_price?: number | null
  take_profit?: number | null
  stop_loss?: number | null
  last_event?: string
  has_bought?: boolean
  probe_count?: number
  probe_progress?: number
  probe_icon_level?: number
  probe_state_text?: string
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
    selectionMode: 'all' as 'all' | 'exchange' | 'custom',
    selectionExchanges: [] as string[],
    config: null as ConfigResponse | null,
    isRunning: false,
    connectionStatus: 'disconnected' as ConnectionStatus,
    symbolData: new Map<string, SymbolRow>(),
    logs: [] as LogEntry[]
  }),

  getters: {
    sortedSymbols(state): SymbolRow[] {
      const rows = Array.from(state.symbolData.values())
      return rows.sort((a, b) => {
        const left = `${a.name || a.displaySymbol || a.symbol}-${a.symbol}`
        const right = `${b.name || b.displaySymbol || b.symbol}-${b.symbol}`
        return left.localeCompare(right)
      })
    },

    activeSymbolCount(state): number {
      return Array.from(state.symbolData.values()).filter(
        row => row.status === 'MONITORING' || row.status === 'BREAKOUT_DETECTED' || row.status === 'HOLDING'
      ).length
    },

    symbolCandidates(state): SymbolCandidate[] {
      return state.config?.symbol_candidates ?? []
    }
  },

  actions: {
    async startMonitor(request: MonitorStartRequest): Promise<void> {
      try {
        const status = await controlMonitor('start', request)
        this.applyStatusSnapshot(status)
      } catch (error) {
        const detail = error instanceof Error ? error.message : String(error)
        this.addLog({
          timestamp: new Date().toISOString(),
          level: 'ERROR',
          message: `启动监控失败：${detail}`
        })
        throw new Error(detail)
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
        displaySymbol: data.display_symbol ?? existing?.displaySymbol ?? data.symbol,
        name: data.name ?? existing?.name ?? '',
        exchange: data.exchange ?? existing?.exchange ?? '',
        status: normalizeSymbolStatus(data.status) || existing?.status || 'MONITORING',
        lastPrice: data.last_price ?? existing?.lastPrice ?? null,
        dayHigh: data.day_high ?? existing?.dayHigh ?? null,
        dayLow: data.day_low ?? existing?.dayLow ?? null,
        breakoutPrice: data.breakout_price ?? existing?.breakoutPrice ?? null,
        takeProfit: data.take_profit ?? existing?.takeProfit ?? null,
        stopLoss: data.stop_loss ?? existing?.stopLoss ?? null,
        lastEvent: data.last_event ?? existing?.lastEvent ?? null,
        hasBought: data.has_bought ?? existing?.hasBought ?? false,
        probeCount: data.probe_count ?? existing?.probeCount ?? 0,
        probeProgress: data.probe_progress ?? existing?.probeProgress ?? 0,
        probeIconLevel: data.probe_icon_level ?? existing?.probeIconLevel ?? 0,
        probeStateText: data.probe_state_text ?? existing?.probeStateText ?? '监控中'
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
      this.selectionMode = 'all'
      this.selectionExchanges = []
      this.isRunning = false
      this.connectionStatus = 'disconnected'
      this.symbolData.clear()
      this.logs = []

      const [config, status] = await Promise.all([getConfig(), getMonitorStatus()])
      this.setConfig(config)
      this.applyStatusSnapshot(status)
    },

    setConfig(config: ConfigResponse): void {
      this.config = config
      this.selectionMode = config.selection_mode
      this.selectionExchanges = [...config.selection_exchanges]
      if (!this.isRunning) {
        this.symbols = [...config.selection_symbols]
      }
    },

    async refreshConfig(): Promise<ConfigResponse> {
      const config = await getConfig()
      this.setConfig(config)
      return config
    },

    async saveConfig(payload: ConfigUpdate): Promise<ConfigResponse> {
      const saved = await updateConfig(payload)
      this.setConfig(saved)
      return await this.refreshConfig()
    },

    applyStatusSnapshot(status: MonitorStatus): void {
      this.isRunning = status.running
      this.symbols = status.symbols
      this.selectionMode = status.selection_mode
      this.selectionExchanges = [...status.selection_exchanges]
      this.connectionStatus = normalizeConnectionStatus(status.connection_status)
      this.symbolData = new Map()
      status.rows.forEach(row => this.handleRowUpdate(row))
    }
  }
})
