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

export interface ApiErrorPayload {
  detail?: string | Record<string, unknown>
  hint?: string
}

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000
})

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function extractString(value: unknown): string | null {
  return typeof value === 'string' && value.trim() ? value.trim() : null
}

function extractApiErrorMessage(payload: unknown): string {
  if (!isRecord(payload)) {
    return '请求失败，请稍后重试'
  }

  const detail = payload.detail
  const topLevelHint = extractString(payload.hint)

  if (typeof detail === 'string') {
    return topLevelHint ? `${detail} ${topLevelHint}` : detail
  }

  if (isRecord(detail)) {
    const nestedDetail = extractString(detail.detail)
    const nestedHint = extractString(detail.hint)
    const message = nestedDetail ?? '请求失败，请稍后重试'
    const hint = nestedHint ?? topLevelHint
    return hint ? `${message} ${hint}` : message
  }

  return topLevelHint ?? '请求失败，请稍后重试'
}

apiClient.interceptors.response.use(
  response => response,
  error => {
    if (axios.isAxiosError(error) && error.response) {
      const message = extractApiErrorMessage(error.response.data)
      return Promise.reject(new Error(message))
    }
    return Promise.reject(error)
  }
)

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
}

export interface ConfigUpdate {
  symbols?: string[]
  take_profit_pct?: number
  stop_loss_pct?: number
  position_pct?: number
  enable_sms?: boolean
  alert_sound?: boolean
  data_dir?: string
  timezone?: string
  use_real_market_data?: boolean
  strict_real_mode?: boolean
  ui_refresh_ms?: number
  tq_account?: string
  tq_password?: string
}

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
