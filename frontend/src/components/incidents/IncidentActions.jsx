import StatusBadge from '../ui/StatusBadge'

const ACTIONS = [
  { status: 'acknowledged', label: 'Acknowledge', variant: 'amber' },
  { status: 'investigating', label: 'Investigating', variant: 'blue' },
  { status: 'resolved', label: 'Resolve', variant: 'green' },
  { status: 'false_alarm', label: 'False Alarm', variant: 'slate' },
]

const variants = {
  amber: 'border-amber-500/40 bg-amber-500/10 text-amber-300 hover:bg-amber-500/20',
  blue: 'border-blue-500/40 bg-blue-500/10 text-blue-300 hover:bg-blue-500/20',
  green: 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300 hover:bg-emerald-500/20',
  slate: 'border-slate-500/40 bg-slate-500/10 text-slate-300 hover:bg-slate-500/20',
}

export default function IncidentActions({ currentStatus, canEdit, busy, onStatusChange }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
      <div className="mb-4 flex items-center justify-between gap-3">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
          Actions
        </h3>
        <StatusBadge status={currentStatus} />
      </div>

      {!canEdit ? (
        <p className="text-sm text-slate-500">View-only access. Contact an operator to update.</p>
      ) : (
        <div className="flex flex-wrap gap-2">
          {ACTIONS.map((action) => (
            <button
              key={action.status}
              type="button"
              disabled={busy || currentStatus === action.status}
              onClick={() => onStatusChange(action.status)}
              className={`rounded-lg border px-3 py-2 text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-40 ${variants[action.variant]}`}
            >
              {action.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
