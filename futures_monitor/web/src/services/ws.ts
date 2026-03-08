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

export interface WsEnvelope<T = unknown> {
  type: string
  data: T
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
      return
    }

    this.isManualClose = false
    this.store.setConnectionStatus('connecting')

    try {
      this.ws = new WebSocket(this.url)

      this.ws.onopen = () => {
        this.reconnectAttempts = 0
        this.reconnectDelay = 1000
      }

      this.ws.onmessage = (event) => {
        try {
          const message: WsEnvelope = JSON.parse(event.data)
          this.handleMessage(message)
        } catch (error) {
          console.error('[WebSocket] Failed to parse message:', error)
        }
      }

      this.ws.onclose = () => {
        this.store.setConnectionStatus('disconnected')
        if (!this.isManualClose) {
          this.scheduleReconnect()
        }
      }

      this.ws.onerror = () => {
        this.store.setConnectionStatus('error')
      }
    } catch (error) {
      console.error('[WebSocket] Failed to connect:', error)
      this.store.setConnectionStatus('error')
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
      this.store.addLog({
        timestamp: new Date().toISOString(),
        level: 'ERROR',
        message: 'WebSocket 重连次数已达上限'
      })
      return
    }

    this.reconnectAttempts++
    this.reconnectTimer = setTimeout(() => {
      this.connect()
    }, this.reconnectDelay)

    this.reconnectDelay = Math.min(
      this.reconnectDelay * this.reconnectBackoffFactor,
      this.maxReconnectDelay
    )
  }

  private handleMessage(message: WsEnvelope): void {
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
        this.store.setRunningStatus((message.data as { running: boolean }).running)
        break
      case 'pong':
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
