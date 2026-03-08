/**
 * role: Provide HTTP client contract for backend API calls.
 * depends:
 *   - axios
 * exports:
 *   - apiClient
 *   - getMonitorStatus
 *   - getConfig
 *   - updateConfig
 *   - controlMonitor
 *   - markBought
 * status: IMPLEMENTED
 * functions:
 *   - getMonitorStatus() -> Promise<MonitorStatus>
 *   - getConfig() -> Promise<ConfigResponse>
 *   - updateConfig(config) -> Promise<ConfigResponse>
 *   - controlMonitor(action, symbols?) -> Promise<MonitorStatus>
 *   - markBought(symbol) -> Promise<void>
 */

import axios from 'axios'

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000
})

export interface ConfigResponse {
  symbols: string[]
  take_profit_pct: number
  stop_loss_pct: number
  position_pct: number
  enable_sms: boolean
  alert_sound: boolean
  data_dir: string
  timezone: string
  use_real_market_data: boolean
  strict_real_mode: boolean
  ui_refresh_ms: number
  tq_account: string
  tq_password: string
  poll_interval: number
}

export interface ConfigUpdate extends Partial<ConfigResponse> {}

export interface SymbolRow {
  symbol: string
  status: string
  last_price: number | null
  day_high: number | null
  day_low: number | null
  breakout_price: number | null
  take_profit: number | null
  stop_loss: number | null
  last_event: string
  has_bought: boolean
}

export interface MonitorStatus {
  running: boolean
  symbols: string[]
  connection_status: string
  rows: SymbolRow[]
  message: string
}

export async function getConfig(): Promise<ConfigResponse> {
  const response = await apiClient.get<ConfigResponse>('/config')
  return response.data
}

export async function updateConfig(config: ConfigUpdate): Promise<ConfigResponse> {
  const response = await apiClient.put<ConfigResponse>('/config', config)
  return response.data
}

export async function getMonitorStatus(): Promise<MonitorStatus> {
  const response = await apiClient.get<MonitorStatus>('/monitor/status')
  return response.data
}

export async function controlMonitor(
  action: 'start' | 'stop',
  symbols?: string[]
): Promise<MonitorStatus> {
  const response = await apiClient.post<MonitorStatus>('/monitor/control', { action, symbols: symbols || [] })
  return response.data
}

export async function markBought(symbol: string): Promise<void> {
  await apiClient.post('/monitor/mark-bought', { symbol })
}
