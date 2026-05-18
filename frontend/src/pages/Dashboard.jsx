import { useCallback, useEffect, useState } from 'react'
import { Cpu, Flame, ShieldAlert, Wifi } from 'lucide-react'
import { Link } from 'react-router-dom'
import { fetchDashboardStats } from '../api/dashboard'
import { fetchFireEvents } from '../api/fireEvents'
import {
  incrementStatsForEvent,
  useFireEventSubscription,
} from '../context/RealtimeProvider'
import PageHeader from '../components/ui/PageHeader'
import StatCard from '../components/ui/StatCard'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import StatusBadge from '../components/ui/StatusBadge'
import { formatDate, formatPercent } from '../utils/format'
import { getApiErrorMessage } from '../utils/apiError'

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [recentEvents, setRecentEvents] = useState([])
  const [newEventIds, setNewEventIds] = useState(() => new Set())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function load() {
      try {
        setLoading(true)
        setError(null)
        const [statsData, eventsData] = await Promise.all([
          fetchDashboardStats(),
          fetchFireEvents(),
        ])
        setStats(statsData)
        setRecentEvents(eventsData.slice(0, 5))
      } catch (err) {
        setError(getApiErrorMessage(err, 'Failed to load dashboard'))
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const markNew = useCallback((eventId) => {
    setNewEventIds((prev) => new Set(prev).add(eventId))
    setTimeout(() => {
      setNewEventIds((prev) => {
        const next = new Set(prev)
        next.delete(eventId)
        return next
      })
    }, 3000)
  }, [])

  useFireEventSubscription(
    useCallback(
      (event) => {
        setStats((prev) => incrementStatsForEvent(prev, event))
        setRecentEvents((prev) => {
          if (prev.some((e) => e.id === event.id)) return prev
          return [event, ...prev].slice(0, 5)
        })
        markNew(event.id)
      },
      [markNew],
    ),
  )

  if (loading && !stats) {
    return <LoadingSpinner label="Loading dashboard..." />
  }

  return (
    <div>
      <PageHeader
        title="Fire Monitoring Dashboard"
        description="Real-time overview of devices, fire events, and open incidents."
      />

      {error && (
        <div className="mb-6 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          {error} — ensure the API is running at {import.meta.env.VITE_API_URL || 'http://localhost:8000'}
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="Total Devices"
          value={stats?.total_devices ?? 0}
          icon={Cpu}
          accent="cyan"
          loading={loading}
        />
        <StatCard
          title="Online Devices"
          value={stats?.online_devices ?? 0}
          icon={Wifi}
          accent="emerald"
          loading={loading}
        />
        <StatCard
          title="Fire Events"
          value={stats?.fire_events ?? 0}
          icon={Flame}
          accent="red"
          loading={loading}
        />
        <StatCard
          title="Open Incidents"
          value={stats?.open_incidents ?? 0}
          icon={ShieldAlert}
          accent="orange"
          loading={loading}
        />
      </div>

      <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-3">
        <section className="lg:col-span-2 rounded-xl border border-slate-800 bg-slate-900/50 p-5">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-white">Recent Fire Events</h2>
            <Link
              to="/fire-events"
              className="text-sm font-medium text-orange-400 hover:text-orange-300"
            >
              View all →
            </Link>
          </div>

          {recentEvents.length === 0 ? (
            <p className="py-8 text-center text-sm text-slate-500">
              No fire events recorded yet.
            </p>
          ) : (
            <ul className="divide-y divide-slate-800">
              {recentEvents.map((event) => (
                <li
                  key={event.id}
                  className={`flex flex-wrap items-center justify-between gap-3 py-3 first:pt-0 last:pb-0 rounded-lg transition ${
                    newEventIds.has(event.id) ? 'animate-event-highlight px-2 -mx-2' : ''
                  }`}
                >
                  <div className="flex items-center gap-3">
                    {event.image_url ? (
                      <img
                        src={event.image_url}
                        alt=""
                        className="h-12 w-12 shrink-0 rounded-lg object-cover ring-1 ring-slate-700"
                      />
                    ) : (
                      <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-red-500/15 text-red-400">
                        <Flame size={16} />
                      </div>
                    )}
                    <div>
                      <p className="font-medium text-slate-200">
                        {event.device_name || `Device #${event.device_id}`}
                      </p>
                      <p className="text-xs text-slate-500">
                        {formatDate(event.created_at)} · {formatPercent(event.confidence)} confidence
                      </p>
                    </div>
                  </div>
                  <StatusBadge status={event.status} />
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
          <h2 className="mb-4 text-lg font-semibold text-white">Quick Actions</h2>
          <div className="space-y-2">
            {[
              { to: '/devices', label: 'Manage Devices', desc: 'View sensor fleet' },
              { to: '/incidents', label: 'Open Incidents', desc: 'Review active alerts' },
              { to: '/settings', label: 'Settings', desc: 'Configure platform' },
            ].map((item) => (
              <Link
                key={item.to}
                to={item.to}
                className="block rounded-lg border border-slate-800 bg-slate-950/50 px-4 py-3 transition hover:border-orange-500/30 hover:bg-slate-800/50"
              >
                <p className="text-sm font-medium text-slate-200">{item.label}</p>
                <p className="text-xs text-slate-500">{item.desc}</p>
              </Link>
            ))}
          </div>

          <div className="mt-6 rounded-lg border border-orange-500/20 bg-orange-500/5 p-4">
            <p className="text-xs font-semibold uppercase tracking-wider text-orange-400">
              Threat level
            </p>
            <p className="mt-1 text-2xl font-bold text-white">
              {(stats?.open_incidents ?? 0) > 0 ? 'Elevated' : 'Normal'}
            </p>
            <p className="mt-1 text-xs text-slate-500">
              Based on open incident count
            </p>
          </div>
        </section>
      </div>
    </div>
  )
}
