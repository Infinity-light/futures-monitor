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
  markBought as markBoughtApi
} from '../services/api'

export type ConnectionStatus = 'connected' | 'connecting' | 'disconnected'

export type SymbolStatus = 'MONITORING' | 'BREAKOUT_DETECTED' | 'BOUGHT' | 'STOPPED'

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
  status?: SymbolStatus
  last_price?: number
  day_high?: number
  day_low?: number
  breakout_price?: number
  take_profit?: number
  stop_loss?: number
  last_event?: string
  has_bought?: boolean
}

export const useMonitorStore = defineStore('monitor', {
  state: () => ({
    symbols: [] as string[],
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
        row => row.status === 'MONITORING' || row.status === 'BREAKOUT_DETECTED'
      ).length
    }
  },

  actions: {
    async startMonitor(symbols: string[]): Promise<void> {
      try {
        await controlMonitor('start', symbols)
        this.symbols = symbols
        this.isRunning = true
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
        await controlMonitor('stop')
        this.isRunning = false
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
        const row = this.symbolData.get(symbol)
        if (row) {
          row.status = 'BOUGHT'
          row.hasBought = true
        }
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
        status: (data.status as SymbolStatus) || existing?.status || 'MONITORING',
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
    },

    addLog(entry: LogEntry): void {
      this.logs.push(entry)
      // 限制日志数量，最多保留 100 条
      if (this.logs.length > 100) {
        this.logs.shift()
      }
    },

    setConnectionStatus(status: ConnectionStatus): void {
      this.connectionStatus = status
    },

    setRunningStatus(isRunning: boolean): void {
      this.isRunning = isRunning
    },

    initialize(): void {
      // 初始化时清空数据
      this.symbols = []
      this.isRunning = false
      this.connectionStatus = 'disconnected'
      this.symbolData.clear()
      this.logs = []
    }
  }
})
