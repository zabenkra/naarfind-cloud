import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, Flame, MapPin, Thermometer } from 'lucide-react'
import {
  addIncidentNote,
  fetchIncident,
  updateIncidentStatus,
} from '../api/incidents'
import { useAuth } from '../context/AuthContext'
import IncidentActions from '../components/incidents/IncidentActions'
import IncidentNotes from '../components/incidents/IncidentNotes'
import IncidentTimeline from '../components/incidents/IncidentTimeline'
import ConfidenceBadge from '../components/incidents/ConfidenceBadge'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import StatusBadge from '../components/ui/StatusBadge'
import ImageModal from '../components/ui/ImageModal'
import { formatDate, formatPercent } from '../utils/format'
import { getApiErrorMessage } from '../utils/apiError'

const CAN_MANAGE = new Set(['operator', 'org_admin', 'super_admin'])

export default function IncidentDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const canEdit = CAN_MANAGE.has(user?.role)

  const [incident, setIncident] = useState(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [imageOpen, setImageOpen] = useState(false)

  const load = useCallback(async () => {
    try {
      setError(null)
      setIncident(await fetchIncident(id))
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to load incident'))
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    setLoading(true)
    load()
  }, [load])

  const handleStatusChange = async (status) => {
    setBusy(true)
    try {
      setIncident(await updateIncidentStatus(id, status))
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to update status'))
    } finally {
      setBusy(false)
    }
  }

  const handleAddNote = async (message) => {
    setBusy(true)
    try {
      await addIncidentNote(id, message)
      setIncident(await fetchIncident(id))
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to add note'))
    } finally {
      setBusy(false)
    }
  }

  if (loading) return <LoadingSpinner label="Loading incident..." />

  if (error && !incident) {
    return (
      <div>
        <Link to="/incidents" className="mb-4 inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white">
          <ArrowLeft size={16} /> Back to incidents
        </Link>
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-red-400">{error}</div>
      </div>
    )
  }

  if (!incident) return null

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={() => navigate('/incidents')}
          className="inline-flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800/50 px-3 py-2 text-sm text-slate-300 hover:bg-slate-800"
        >
          <ArrowLeft size={16} />
          Incidents
        </button>
        <span className="text-slate-600">/</span>
        <h1 className="text-xl font-bold text-white">Incident #{incident.id}</h1>
        <StatusBadge status={incident.status} />
      </div>

      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-5">
        <div className="lg:col-span-3 space-y-4">
          <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/50">
            <div className="relative aspect-video bg-slate-950">
              {incident.image_url ? (
                <button
                  type="button"
                  onClick={() => setImageOpen(true)}
                  className="group relative h-full w-full"
                >
                  <img
                    src={incident.image_url}
                    alt={`Incident ${incident.id} snapshot`}
                    className="h-full w-full object-cover transition group-hover:scale-[1.01]"
                  />
                  <span className="absolute bottom-3 right-3 rounded bg-black/70 px-2 py-1 text-xs text-white opacity-0 transition group-hover:opacity-100">
                    View full size
                  </span>
                </button>
              ) : (
                <div className="flex h-full flex-col items-center justify-center gap-2 text-slate-600">
                  <Flame size={40} />
                  <span className="text-sm">No snapshot available</span>
                </div>
              )}
            </div>
          </div>

          {incident.video_url && (
            <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                Video
              </p>
              <video
                src={incident.video_url}
                controls
                className="max-h-64 w-full rounded-lg bg-black"
              />
            </div>
          )}
        </div>

        <div className="lg:col-span-2 space-y-4">
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4 space-y-4">
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-500">Device</p>
              <p className="text-lg font-semibold text-white">
                {incident.device_name || `Device #${incident.device_id}`}
              </p>
            </div>
            <div className="flex items-start gap-2">
              <MapPin size={16} className="mt-0.5 text-slate-500" />
              <div>
                <p className="text-xs uppercase tracking-wide text-slate-500">Site</p>
                <p className="text-slate-200">{incident.site_name || '—'}</p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <p className="text-xs text-slate-500">Event type</p>
                <p className="font-medium capitalize text-slate-200">
                  {incident.event_type?.replace(/_/g, ' ')}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Confidence</p>
                <ConfidenceBadge value={incident.confidence} />
              </div>
              <div>
                <p className="text-xs text-slate-500">Temperature</p>
                <p className="flex items-center gap-1 text-slate-200">
                  <Thermometer size={14} className="text-red-400" />
                  {incident.temperature != null ? `${incident.temperature}°C` : '—'}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Detected</p>
                <p className="text-slate-200">{formatDate(incident.created_at)}</p>
              </div>
            </div>
          </div>

          <IncidentActions
            currentStatus={incident.status}
            canEdit={canEdit}
            busy={busy}
            onStatusChange={handleStatusChange}
          />
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
          <h3 className="mb-4 text-sm font-semibold uppercase tracking-wide text-slate-400">
            Timeline
          </h3>
          <IncidentTimeline entries={incident.timeline} />
        </div>

        <IncidentNotes
          notes={incident.notes}
          canEdit={canEdit}
          busy={busy}
          onAdd={handleAddNote}
        />
      </div>

      {imageOpen && incident.image_url && (
        <ImageModal
          url={incident.image_url}
          alt={`Incident ${incident.id}`}
          onClose={() => setImageOpen(false)}
        />
      )}
    </div>
  )
}
