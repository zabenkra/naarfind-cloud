const LOCAL_API = 'http://localhost:8000'
const WS_PATH = '/ws/events'

/**
 * Always return a WebSocket base URL ending with /ws/events (no query string).
 */
export function normalizeWsUrl(raw) {
  const value = (raw || '').trim().replace(/\?.*$/, '').replace(/\/$/, '')
  if (!value) {
    return ''
  }

  // Already correct
  if (value.endsWith(WS_PATH)) {
    return value
  }

  try {
    const parsed = new URL(value.includes('://') ? value : `https://${value}`)
    parsed.pathname = WS_PATH
    parsed.search = ''
    parsed.hash = ''
    const protocol = parsed.protocol === 'https:' ? 'wss:' : parsed.protocol === 'http:' ? 'ws:' : parsed.protocol
    return `${protocol}//${parsed.host}${WS_PATH}`
  } catch {
    const base = value.replace(/\/ws\/events\/?$/, '').replace(/\/$/, '')
    const wsBase = base.replace(/^https:/, 'wss:').replace(/^http:/, 'ws:')
    return `${wsBase}${WS_PATH}`
  }
}

export function getApiUrl() {
  const raw = import.meta.env.VITE_API_URL || LOCAL_API
  return String(raw).trim().replace(/\/$/, '')
}

export function getWsUrl() {
  const explicit = import.meta.env.VITE_WS_URL
  if (explicit) {
    return normalizeWsUrl(explicit)
  }

  const api = getApiUrl()
  return normalizeWsUrl(api)
}
