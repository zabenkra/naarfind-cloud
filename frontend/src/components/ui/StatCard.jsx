export default function StatCard({ title, value, icon: Icon, accent = 'orange', loading }) {
  const accents = {
    orange: {
      icon: 'bg-orange-500/15 text-orange-400 ring-orange-500/20',
      glow: 'from-orange-500/10',
    },
    emerald: {
      icon: 'bg-emerald-500/15 text-emerald-400 ring-emerald-500/20',
      glow: 'from-emerald-500/10',
    },
    red: {
      icon: 'bg-red-500/15 text-red-400 ring-red-500/20',
      glow: 'from-red-500/10',
    },
    cyan: {
      icon: 'bg-cyan-500/15 text-cyan-400 ring-cyan-500/20',
      glow: 'from-cyan-500/10',
    },
  }

  const style = accents[accent] || accents.orange

  return (
    <div className="group relative overflow-hidden rounded-xl border border-slate-800 bg-slate-900/80 p-5 backdrop-blur-sm transition hover:border-slate-700">
      <div
        className={`pointer-events-none absolute -right-6 -top-6 h-24 w-24 rounded-full bg-gradient-to-br ${style.glow} to-transparent opacity-60`}
      />
      <div className="relative flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-slate-400">{title}</p>
          {loading ? (
            <div className="mt-3 h-9 w-16 animate-pulse rounded bg-slate-800" />
          ) : (
            <p className="mt-2 text-3xl font-bold tabular-nums tracking-tight text-white">
              {value ?? '—'}
            </p>
          )}
        </div>
        {Icon && (
          <div
            className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-lg ring-1 ${style.icon}`}
          >
            <Icon size={22} />
          </div>
        )}
      </div>
    </div>
  )
}
