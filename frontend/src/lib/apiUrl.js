const LOCAL_API = 'http://localhost:8000'
const LOCAL_WS = 'ws://localhost:8000/ws/events'

export function getApiUrl() {
  return import.meta.env.VITE_API_URL || LOCAL_API
}

export function getWsUrl() {
  if (import.meta.env.VITE_WS_URL) {
    return import.meta.env.VITE_WS_URL.replace(/\?.*$/, '')
  }

  const api = getApiUrl()
  try {
    const parsed = new URL(api)
    parsed.protocol = parsed.protocol === 'https:' ? 'wss:' : 'ws:'
    parsed.pathname = '/ws/events'
    parsed.search = ''
    parsed.hash = ''
    return parsed.toString().replace(/\/$/, '')
  } catch {
    return api.replace(/^https/, 'wss').replace(/^http/, 'ws').replace(/\/$/, '') + '/ws/events'
  }
}
