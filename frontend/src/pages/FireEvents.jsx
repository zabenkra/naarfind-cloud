import { useEffect, useState } from 'react'
import { Flame } from 'lucide-react'
import { fetchFireEvents } from '../api/fireEvents'
import FireEventCard from '../components/fire/FireEventCard'
import PageHeader from '../components/ui/PageHeader'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import EmptyState from '../components/ui/EmptyState'
import { getApiErrorMessage } from '../utils/apiError'
import { useLiveFireEvents } from '../hooks/useLiveFireEvents'

export default function FireEvents() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const { events, setEvents, isNew } = useLiveFireEvents()

  useEffect(() => {
    async function load() {
      try {
        setLoading(true)
        setError(null)
        setEvents(await fetchFireEvents())
      } catch (err) {
        setError(getApiErrorMessage(err, 'Failed to load fire events'))
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [setEvents])

  if (loading && events.length === 0) {
    return <LoadingSpinner label="Loading fire events..." />
  }

  return (
    <div>
      <PageHeader
        title="Fire Events"
        description="Live fire detection events — updates instantly via WebSocket."
      />

      {error && (
        <div className="mb-6 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {!error && events.length === 0 ? (
        <EmptyState
          icon={Flame}
          title="No fire events"
          description="Fire detection events will appear here when sensors report activity."
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {events.map((event) => (
            <FireEventCard key={event.id} event={event} isNew={isNew(event.id)} />
          ))}
        </div>
      )}
    </div>
  )
}
