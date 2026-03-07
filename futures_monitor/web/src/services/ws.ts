/**
 * role: Provide websocket client contract for realtime monitor events.
 * depends:
 *   - WebSocket
 *   - ../stores/monitor
 * exports:
 *   - createMonitorSocket
 *   - MonitorWebSocket
 * status: IMPLEMENTED
 * functions:
 *   - createMonitorSocket(url, store) -> MonitorWebSocket
 *   - MonitorWebSocket.connect() -> void
 *   - MonitorWebSocket.disconnect() -> void
 *   - MonitorWebSocket.reconnect() -> void
 */

import { useMonitorStore, type ConnectionStatus, type SymbolRowData } from '../stores/monitor'

export interface WsMessage {
  type: 'row' | 'log' | 'connection' | 'running'
  data: unknown
}

export class MonitorWebSocket {
  private ws: WebSocket | null = null
  private url: string
  private store: ReturnType<typeof useMonitorStore>
  private reconnectAttempts = 0
  private maxReconnectAttempts = 10
  private reconnectDelay = 1000
  private maxReconnectDelay = 30000
  private reconnectBackoffFactor = 2
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private isManualClose = false

  constructor(url: string, store: ReturnType<typeof useMonitorStore>) {
    this.url = url
    this.store = store
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log('[WebSocket] Already connected')
      return
    }

    this.isManualClose = false
    this.store.setConnectionStatus('connecting')

    try {
      this.ws = new WebSocket(this.url)

      this.ws.onopen = () => {
        console.log('[WebSocket] Connected')
        this.reconnectAttempts = 0
        this.reconnectDelay = 1000
        this.store.setConnectionStatus('connected')
      }

      this.ws.onmessage = (event) => {
        try {
          const message: WsMessage = JSON.parse(event.data)
          this.handleMessage(message)
        } catch (error) {
          console.error('[WebSocket] Failed to parse message:', error)
        }
      }

      this.ws.onclose = () => {
        console.log('[WebSocket] Closed')
        this.store.setConnectionStatus('disconnected')
        if (!this.isManualClose) {
          this.scheduleReconnect()
        }
      }

      this.ws.onerror = (error) => {
        console.error('[WebSocket] Error:', error)
        this.store.setConnectionStatus('disconnected')
      }
    } catch (error) {
      console.error('[WebSocket] Failed to connect:', error)
      this.store.setConnectionStatus('disconnected')
      this.scheduleReconnect()
    }
  }

  disconnect(): void {
    this.isManualClose = true
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[WebSocket] Max reconnect attempts reached')
      this.store.addLog({
        timestamp: new Date().toISOString(),
        level: 'ERROR',
        message: 'WebSocket 重连次数已达上限'
      })
      return
    }

    this.reconnectAttempts++
    console.log(`[WebSocket] Reconnecting in ${this.reconnectDelay}ms (attempt ${this.reconnectAttempts})`)

    this.reconnectTimer = setTimeout(() => {
      this.connect()
    }, this.reconnectDelay)

    // 指数退避
    this.reconnectDelay = Math.min(
      this.reconnectDelay * this.reconnectBackoffFactor,
      this.maxReconnectDelay
    )
  }

  private handleMessage(message: WsMessage): void {
    switch (message.type) {
      case 'row':
        this.store.handleRowUpdate(message.data as SymbolRowData)
        break
      case 'log':
        this.store.addLog(message.data as {
          timestamp: string
          level: 'INFO' | 'WARNING' | 'ERROR'
          message: string
        })
        break
      case 'connection':
        this.store.setConnectionStatus((message.data as { status: ConnectionStatus }).status)
        break
      case 'running':
        this.store.setRunningStatus((message.data as { isRunning: boolean }).isRunning)
        break
      default:
        console.warn('[WebSocket] Unknown message type:', message.type)
    }
  }
}

export function createMonitorSocket(
  url: string,
  store: ReturnType<typeof useMonitorStore>
): MonitorWebSocket {
  return new MonitorWebSocket(url, store)
}
