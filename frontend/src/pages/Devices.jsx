import { useEffect, useState } from 'react'
import { Cpu } from 'lucide-react'
import { fetchDevices } from '../api/devices'
import PageHeader from '../components/ui/PageHeader'
import { getApiErrorMessage } from '../utils/apiError'
import DataTable from '../components/ui/DataTable'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import EmptyState from '../components/ui/EmptyState'
import StatusBadge from '../components/ui/StatusBadge'
import { formatDate } from '../utils/format'

export default function Devices() {
  const [devices, setDevices] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function load() {
      try {
        setLoading(true)
        setError(null)
        setDevices(await fetchDevices())
      } catch (err) {
        setError(getApiErrorMessage(err, 'Failed to load devices'))
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const columns = [
    { key: 'name', label: 'Name' },
    { key: 'device_uid', label: 'Device UID' },
    {
      key: 'status',
      label: 'Status',
      render: (row) => (
        <StatusBadge status={row.is_online ? 'online' : 'offline'} />
      ),
    },
    {
      key: 'last_seen',
      label: 'Last Seen',
      render: (row) => formatDate(row.last_seen),
    },
    {
      key: 'created_at',
      label: 'Registered',
      render: (row) => formatDate(row.created_at),
    },
  ]

  if (loading) return <LoadingSpinner label="Loading devices..." />

  return (
    <div>
      <PageHeader
        title="Devices"
        description="Monitor your fire detection sensor fleet."
      />

      {error && (
        <div className="mb-6 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {!error && devices.length === 0 ? (
        <EmptyState
          icon={Cpu}
          title="No devices registered"
          description="Devices will appear here once they are added to the platform."
        />
      ) : (
        <DataTable columns={columns} rows={devices} emptyMessage="No devices found." />
      )}
    </div>
  )
}
