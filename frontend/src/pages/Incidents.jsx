import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ShieldAlert } from 'lucide-react'
import { fetchIncidents } from '../api/incidents'
import { useFireEventSubscription } from '../context/RealtimeProvider'
import PageHeader from '../components/ui/PageHeader'
import DataTable from '../components/ui/DataTable'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import EmptyState from '../components/ui/EmptyState'
import StatusBadge from '../components/ui/StatusBadge'
import ConfidenceBadge from '../components/incidents/ConfidenceBadge'
import { formatDate } from '../utils/format'
import { getApiErrorMessage } from '../utils/apiError'

const OPEN_STATUSES = new Set(['new', 'acknowledged', 'investigating'])

export default function Incidents() {
  const navigate = useNavigate()
  const [incidents, setIncidents] = useState([])
  const [highlightIds, setHighlightIds] = useState(() => new Set())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showAll, setShowAll] = useState(false)

  useEffect(() => {
    async function load() {
      try {
        setLoading(true)
        setError(null)
        setIncidents(await fetchIncidents(showAll))
      } catch (err) {
        setError(getApiErrorMessage(err, 'Failed to load incidents'))
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [showAll])

  const highlight = useCallback((id) => {
    setHighlightIds((prev) => new Set(prev).add(id))
    setTimeout(() => {
      setHighlightIds((prev) => {
        const next = new Set(prev)
        next.delete(id)
        return next
      })
    }, 3000)
  }, [])

  useFireEventSubscription(
    useCallback(
      (event) => {
        if (!OPEN_STATUSES.has(event.status)) return
        setIncidents((prev) => {
          if (prev.some((i) => i.id === event.id)) return prev
          return [event, ...prev]
        })
        highlight(event.id)
      },
      [highlight],
    ),
  )

  const columns = [
    {
      key: 'thumb',
      label: '',
      render: (row) =>
        row.image_url ? (
          <img
            src={row.image_url}
            alt=""
            className="h-10 w-14 rounded object-cover ring-1 ring-slate-700"
            loading="lazy"
          />
        ) : (
          <span className="inline-block h-10 w-14 rounded bg-slate-800" />
        ),
    },
    {
      key: 'id',
      label: 'ID',
      render: (row) => (
        <Link
          to={`/incidents/${row.id}`}
          onClick={(e) => e.stopPropagation()}
          className="font-mono text-orange-400/90 hover:text-orange-300 hover:underline"
        >
          #{row.id}
        </Link>
      ),
    },
    {
      key: 'device',
      label: 'Device',
      render: (row) => row.device_name || `Device #${row.device_id}`,
    },
    {
      key: 'event_type',
      label: 'Type',
      render: (row) => (
        <span className="capitalize text-slate-300">
          {row.event_type?.replace(/_/g, ' ') || '—'}
        </span>
      ),
    },
    {
      key: 'confidence',
      label: 'Confidence',
      render: (row) => <ConfidenceBadge value={row.confidence} />,
    },
    {
      key: 'status',
      label: 'Status',
      render: (row) => <StatusBadge status={row.status} />,
    },
    {
      key: 'created_at',
      label: 'Opened',
      render: (row) => formatDate(row.created_at),
    },
  ]

  const rows = incidents.map((row) => ({
    ...row,
    _rowClass: `cursor-pointer ${highlightIds.has(row.id) ? 'animate-event-highlight' : ''}`,
  }))

  if (loading) return <LoadingSpinner label="Loading incidents..." />

  return (
    <div>
      <PageHeader
        title="Incidents"
        description="Review and manage fire detection incidents from your devices."
        action={
          <label className="flex items-center gap-2 text-sm text-slate-400">
            <input
              type="checkbox"
              checked={showAll}
              onChange={(e) => setShowAll(e.target.checked)}
              className="rounded border-slate-600 bg-slate-800 text-orange-600"
            />
            Show resolved / false alarms
          </label>
        }
      />

      {error && (
        <div className="mb-6 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {!error && incidents.length === 0 ? (
        <EmptyState
          icon={ShieldAlert}
          title="No incidents"
          description="All clear — no incidents match your filter."
        />
      ) : (
        <DataTable
          columns={columns}
          rows={rows}
          rowClassName={(row) => row._rowClass}
          onRowClick={(row) => {
            if (row?.id) navigate(`/incidents/${row.id}`)
          }}
          emptyMessage="No incidents."
        />
      )}
    </div>
  )
}
