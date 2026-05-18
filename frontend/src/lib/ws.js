import { getWsUrl } from './apiUrl'
import { getToken } from './authStorage'

function buildWsUrl() {
  const token = getToken()
  const base = getWsUrl()
  if (!token) return base
  const separator = base.includes('?') ? '&' : '?'
  return `${base}${separator}token=${encodeURIComponent(token)}`
}

const RECONNECT_BASE_MS = 1000
const RECONNECT_MAX_MS = 15000

class EventsWebSocket {
  constructor() {
    this.socket = null
    this.listeners = new Set()
    this.statusListeners = new Set()
    this.reconnectTimer = null
    this.reconnectAttempt = 0
    this.shouldReconnect = true
    this._status = 'disconnected'
  }

  get status() {
    return this._status
  }

  setStatus(status) {
    this._status = status
    this.statusListeners.forEach((fn) => fn(status))
  }

  connect() {
    if (!getToken()) {
      this.setStatus('disconnected')
      return
    }
    if (this.socket?.readyState === WebSocket.OPEN) return
    if (this.socket?.readyState === WebSocket.CONNECTING) return

    this.setStatus('connecting')
    this.socket = new WebSocket(buildWsUrl())

    this.socket.onopen = () => {
      this.reconnectAttempt = 0
      this.setStatus('connected')
    }

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        this.listeners.forEach((fn) => fn(data))
      } catch {
        // ignore malformed messages
      }
    }

    this.socket.onerror = () => {
      this.setStatus('error')
    }

    this.socket.onclose = () => {
      this.setStatus('disconnected')
      this.socket = null
      this.scheduleReconnect()
    }
  }

  scheduleReconnect() {
    if (!this.shouldReconnect || !getToken()) return
    if (this.reconnectTimer) return

    const delay = Math.min(
      RECONNECT_BASE_MS * 2 ** this.reconnectAttempt,
      RECONNECT_MAX_MS,
    )
    this.reconnectAttempt += 1

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null
      this.connect()
    }, delay)
  }

  disconnect() {
    this.shouldReconnect = false
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    if (this.socket) {
      this.socket.close()
      this.socket = null
    }
    this.setStatus('disconnected')
  }

  reconnect() {
    this.shouldReconnect = true
    this.disconnect()
    this.shouldReconnect = true
    this.reconnectAttempt = 0
    this.connect()
  }

  subscribe(listener) {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }

  onStatusChange(listener) {
    this.statusListeners.add(listener)
    return () => this.statusListeners.delete(listener)
  }

  sendPing() {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send('ping')
    }
  }
}

export const eventsWs = new EventsWebSocket()
