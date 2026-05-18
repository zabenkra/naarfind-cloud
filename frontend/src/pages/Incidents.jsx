import { useCallback, useEffect, useState } from 'react'
import { ShieldAlert } from 'lucide-react'
import { fetchIncidents } from '../api/incidents'
import { useFireEventSubscription } from '../context/RealtimeProvider'
import PageHeader from '../components/ui/PageHeader'
import DataTable from '../components/ui/DataTable'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import EmptyState from '../components/ui/EmptyState'
import StatusBadge from '../components/ui/StatusBadge'
import { formatDate, formatPercent } from '../utils/format'
import { getApiErrorMessage } from '../utils/apiError'

const OPEN_STATUSES = new Set(['new', 'acknowledged'])

export default function Incidents() {
  const [incidents, setIncidents] = useState([])
  const [highlightIds, setHighlightIds] = useState(() => new Set())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function load() {
      try {
        setLoading(true)
        setError(null)
        setIncidents(await fetchIncidents())
      } catch (err) {
        setError(getApiErrorMessage(err, 'Failed to load incidents'))
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

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
    { key: 'id', label: 'ID' },
    {
      key: 'device',
      label: 'Device',
      render: (row) => row.device_name || `Device #${row.device_id}`,
    },
    {
      key: 'confidence',
      label: 'Confidence',
      render: (row) => formatPercent(row.confidence),
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
    _rowClass: highlightIds.has(row.id) ? 'animate-event-highlight' : '',
  }))

  if (loading) return <LoadingSpinner label="Loading incidents..." />

  return (
    <div>
      <PageHeader
        title="Incidents"
        description="Open fire incidents requiring review — updates live via WebSocket."
      />

      {error && (
        <div className="mb-6 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {!error && incidents.length === 0 ? (
        <EmptyState
          icon={ShieldAlert}
          title="No open incidents"
          description="All clear — no incidents need attention right now."
        />
      ) : (
        <DataTable
          columns={columns}
          rows={rows}
          rowClassName={(row) => row._rowClass}
          emptyMessage="No open incidents."
        />
      )}
    </div>
  )
}
