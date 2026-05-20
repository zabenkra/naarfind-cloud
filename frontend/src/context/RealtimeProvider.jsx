import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react'
import { eventsWs } from '../lib/ws'
import { playAlertSound } from '../lib/alertSound'
import ToastContainer from '../components/ui/ToastContainer'

const RealtimeContext = createContext(null)

const OPEN_STATUSES = new Set(['new', 'acknowledged', 'investigating'])
const TOAST_TTL_MS = 6000

export function RealtimeProvider({ children }) {
  const [toasts, setToasts] = useState([])
  const [wsStatus, setWsStatus] = useState(eventsWs.status)
  const subscribersRef = useRef(new Set())

  const subscribe = useCallback((listener) => {
    subscribersRef.current.add(listener)
    return () => subscribersRef.current.delete(listener)
  }, [])

  const dismissToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const notifyFireEvent = useCallback((event) => {
    playAlertSound().catch(() => {})

    const toast = { ...event, id: `toast-${event.id}-${Date.now()}` }
    setToasts((prev) => [toast, ...prev].slice(0, 5))

    setTimeout(() => {
      dismissToast(toast.id)
    }, TOAST_TTL_MS)

    subscribersRef.current.forEach((listener) => {
      try {
        listener(event)
      } catch (err) {
        console.error('Realtime subscriber error:', err)
      }
    })
  }, [dismissToast])

  useEffect(() => {
    eventsWs.reconnect()

    const unsubMessage = eventsWs.subscribe((message) => {
      if (message?.type === 'fire_event' && message.event) {
        notifyFireEvent(message.event)
      }
    })

    const unsubStatus = eventsWs.onStatusChange(setWsStatus)

    const pingInterval = setInterval(() => eventsWs.sendPing(), 30000)

    return () => {
      clearInterval(pingInterval)
      unsubMessage()
      unsubStatus()
      eventsWs.disconnect()
    }
  }, [notifyFireEvent])

  return (
    <RealtimeContext.Provider value={{ subscribe, wsStatus }}>
      {children}
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </RealtimeContext.Provider>
  )
}

export function useRealtime() {
  const ctx = useContext(RealtimeContext)
  if (!ctx) {
    throw new Error('useRealtime must be used within RealtimeProvider')
  }
  return ctx
}

export function useFireEventSubscription(onFireEvent) {
  const { subscribe } = useRealtime()
  const handlerRef = useRef(onFireEvent)

  useEffect(() => {
    handlerRef.current = onFireEvent
  }, [onFireEvent])

  useEffect(() => {
    return subscribe((event) => handlerRef.current(event))
  }, [subscribe])
}

export function incrementStatsForEvent(stats, event) {
  if (!stats) return stats
  const isOpen = OPEN_STATUSES.has(event.status)
  return {
    ...stats,
    fire_events: (stats.fire_events ?? 0) + 1,
    open_incidents: isOpen
      ? (stats.open_incidents ?? 0) + 1
      : stats.open_incidents ?? 0,
  }
}
