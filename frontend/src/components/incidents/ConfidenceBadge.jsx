export default function ConfidenceBadge({ value }) {
  if (value == null) return <span className="text-slate-500">—</span>

  const pct = value <= 1 ? Math.round(value * 100) : Math.round(value)
  let tone = 'bg-slate-500/15 text-slate-300 border-slate-500/30'

  if (pct >= 75) tone = 'bg-red-500/15 text-red-400 border-red-500/30'
  else if (pct >= 55) tone = 'bg-orange-500/15 text-orange-400 border-orange-500/30'
  else if (pct >= 40) tone = 'bg-amber-500/15 text-amber-400 border-amber-500/30'

  return (
    <span
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-semibold tabular-nums ${tone}`}
    >
      {pct}%
    </span>
  )
}
