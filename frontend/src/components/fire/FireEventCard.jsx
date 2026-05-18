import { useState } from 'react'
import { Flame, Thermometer } from 'lucide-react'
import StatusBadge from '../ui/StatusBadge'
import ImageModal from '../ui/ImageModal'
import { formatDate, formatPercent } from '../../utils/format'

export default function FireEventCard({ event, isNew = false }) {
  const [imageOpen, setImageOpen] = useState(false)

  return (
    <>
      <article
        className={`overflow-hidden rounded-xl border bg-slate-900/60 transition hover:border-slate-700 ${
          isNew
            ? 'animate-event-highlight border-orange-500/60 ring-2 ring-orange-500/40'
            : 'border-slate-800'
        }`}
      >
        <div className="relative aspect-video bg-slate-950">
          {event.image_url ? (
            <button
              type="button"
              onClick={() => setImageOpen(true)}
              className="group h-full w-full"
            >
              <img
                src={event.image_url}
                alt={`Fire event ${event.id}`}
                className="h-full w-full object-cover transition group-hover:scale-[1.02]"
                loading="lazy"
              />
              <span className="absolute inset-0 bg-black/0 transition group-hover:bg-black/20" />
              <span className="absolute bottom-2 right-2 rounded bg-black/60 px-2 py-0.5 text-xs text-slate-200 opacity-0 transition group-hover:opacity-100">
                View full size
              </span>
            </button>
          ) : (
            <div className="flex h-full flex-col items-center justify-center gap-2 text-slate-600">
              <Flame size={32} />
              <span className="text-xs">No snapshot</span>
            </div>
          )}
        </div>

        <div className="space-y-3 p-4">
          <div className="flex items-start justify-between gap-2">
            <div>
              <p className="font-semibold text-white">
                {event.device_name || `Device #${event.device_id}`}
              </p>
              <p className="text-xs text-slate-500">{formatDate(event.created_at)}</p>
            </div>
            <StatusBadge status={event.status} />
          </div>

          <div className="grid grid-cols-2 gap-2 text-sm">
            <div className="rounded-lg bg-slate-950/80 px-3 py-2">
              <p className="text-xs text-slate-500">Confidence</p>
              <p className="font-medium text-orange-400">{formatPercent(event.confidence)}</p>
            </div>
            <div className="rounded-lg bg-slate-950/80 px-3 py-2">
              <p className="text-xs text-slate-500">Temperature</p>
              <p className="flex items-center gap-1 font-medium text-slate-200">
                <Thermometer size={14} className="text-red-400" />
                {event.temperature != null ? `${event.temperature}°C` : '—'}
              </p>
            </div>
          </div>

          {event.video_url && (
            <div className="rounded-lg border border-slate-800 bg-slate-950/50 p-2">
              <p className="mb-2 text-xs font-medium text-slate-400">Video clip</p>
              <video
                src={event.video_url}
                controls
                preload="metadata"
                className="max-h-48 w-full rounded-md bg-black"
              >
                Your browser does not support video playback.
              </video>
            </div>
          )}
        </div>
      </article>

      {imageOpen && (
        <ImageModal
          url={event.image_url}
          alt={`Fire event ${event.id}`}
          onClose={() => setImageOpen(false)}
        />
      )}
    </>
  )
}
