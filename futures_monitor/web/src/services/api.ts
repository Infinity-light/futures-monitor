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
 *   - updateConfig(config) -> Promise<void>
 *   - controlMonitor(action, symbols?) -> Promise<void>
 *   - markBought(symbol) -> Promise<void>
 */

import axios from 'axios'

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000
})

export interface ConfigResponse {
  symbols: string[]
  breakout_threshold: number
  take_profit_pct: number
  stop_loss_pct: number
}

export interface ConfigUpdate {
  symbols?: string[]
  breakout_threshold?: number
  take_profit_pct?: number
  stop_loss_pct?: number
}

export interface MonitorStatus {
  is_running: boolean
  symbols: string[]
  connection_status: string
}

export async function getConfig(): Promise<ConfigResponse> {
  const response = await apiClient.get<ConfigResponse>('/config')
  return response.data
}

export async function updateConfig(config: ConfigUpdate): Promise<void> {
  await apiClient.post('/config', config)
}

export async function getMonitorStatus(): Promise<MonitorStatus> {
  const response = await apiClient.get<MonitorStatus>('/monitor/status')
  return response.data
}

export async function controlMonitor(
  action: 'start' | 'stop',
  symbols?: string[]
): Promise<void> {
  await apiClient.post('/monitor/control', { action, symbols })
}

export async function markBought(symbol: string): Promise<void> {
  await apiClient.post(`/monitor/mark-bought/${symbol}`)
}
