import { useCallback, useState } from 'react'
import { useFireEventSubscription } from '../context/RealtimeProvider'

export function useLiveFireEvents(initialEvents = []) {
  const [events, setEvents] = useState(initialEvents)
  const [newEventIds, setNewEventIds] = useState(() => new Set())

  const handleNewEvent = useCallback((event) => {
    setEvents((prev) => {
      if (prev.some((e) => e.id === event.id)) return prev
      return [event, ...prev]
    })
    setNewEventIds((prev) => new Set(prev).add(event.id))
    setTimeout(() => {
      setNewEventIds((prev) => {
        const next = new Set(prev)
        next.delete(event.id)
        return next
      })
    }, 3000)
  }, [])

  useFireEventSubscription(handleNewEvent)

  return { events, setEvents, newEventIds, isNew: (id) => newEventIds.has(id) }
}
