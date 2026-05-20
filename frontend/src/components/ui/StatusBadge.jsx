const styles = {
  online: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  warning: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
  offline: 'bg-slate-500/15 text-slate-400 border-slate-500/30',
  new: 'bg-red-500/15 text-red-400 border-red-500/30',
  acknowledged: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
  false_alarm: 'bg-slate-500/15 text-slate-400 border-slate-500/30',
  resolved: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
}

const labels = {
  false_alarm: 'False alarm',
}

export default function StatusBadge({ status }) {
  const key = (status || 'unknown').toLowerCase()
  const className = styles[key] || 'bg-slate-500/15 text-slate-400 border-slate-500/30'
  const label = labels[key] || (status || 'unknown').replace(/_/g, ' ')

  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium capitalize ${className}`}
    >
      {label}
    </span>
  )
}
