import { useEffect, useState } from 'react'
import { Cpu, RefreshCw } from 'lucide-react'
import { fetchDevices } from '../api/devices'
import ProductionDeviceCard from '../components/devices/ProductionDeviceCard'
import PageHeader from '../components/ui/PageHeader'
import { getApiErrorMessage } from '../utils/apiError'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import EmptyState from '../components/ui/EmptyState'

const REFRESH_MS = 15_000

export default function Devices() {
  const [devices, setDevices] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = async () => {
    try {
      setError(null)
      const data = await fetchDevices()
      setDevices(data)
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to load devices'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    const timer = setInterval(load, REFRESH_MS)
    return () => clearInterval(timer)
  }, [])

  const device = devices[0]

  if (loading) return <LoadingSpinner label="Loading devices..." />

  return (
    <div>
      <PageHeader
        title="Devices"
        description="Production fire detection unit — single Raspberry Pi deployment."
        action={
          <button
            type="button"
            onClick={load}
            className="inline-flex items-center gap-2 rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-slate-200 hover:bg-slate-700"
          >
            <RefreshCw size={16} />
            Refresh
          </button>
        }
      />

      {error && (
        <div className="mb-6 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {!error && !device ? (
        <EmptyState
          icon={Cpu}
          title="No production device"
          description="Register pi-001 in the database and start the edge agent with python agent.py --run."
        />
      ) : (
        device && <ProductionDeviceCard device={device} />
      )}

      {!error && devices.length > 1 && (
        <p className="mt-4 text-sm text-amber-400">
          {devices.length} devices found — showing primary unit ({device?.device_uid}).
        </p>
      )}
    </div>
  )
}
