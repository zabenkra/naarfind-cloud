import { AlertCircle, FileText, RefreshCw, ShieldAlert } from 'lucide-react'
import { formatDate } from '../../utils/format'

const icons = {
  created: ShieldAlert,
  audit: RefreshCw,
  note: FileText,
}

export default function IncidentTimeline({ entries }) {
  if (!entries?.length) {
    return (
      <p className="text-sm text-slate-500">No timeline activity yet.</p>
    )
  }

  return (
    <ol className="relative space-y-0 border-l border-slate-700 pl-6">
      {entries.map((entry) => {
        const Icon = icons[entry.type] || AlertCircle
        return (
          <li key={entry.id} className="relative pb-6 last:pb-0">
            <span className="absolute -left-[1.65rem] flex h-7 w-7 items-center justify-center rounded-full border border-slate-600 bg-slate-900">
              <Icon size={14} className="text-slate-400" />
            </span>
            <div className="rounded-lg border border-slate-800 bg-slate-950/50 px-4 py-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="text-sm font-medium text-slate-200">
                  {entry.message || entry.action || entry.type}
                </p>
                <time className="text-xs text-slate-500">{formatDate(entry.created_at)}</time>
              </div>
              {entry.user_name && (
                <p className="mt-1 text-xs text-slate-500">by {entry.user_name}</p>
              )}
            </div>
          </li>
        )
      })}
    </ol>
  )
}
