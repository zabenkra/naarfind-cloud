import { Flame, X } from 'lucide-react'
import { formatPercent } from '../../utils/format'

export default function ToastContainer({ toasts, onDismiss }) {
  if (!toasts.length) return null

  return (
    <div className="pointer-events-none fixed right-4 top-4 z-[100] flex w-full max-w-sm flex-col gap-3">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className="pointer-events-auto animate-slide-in-right overflow-hidden rounded-xl border border-red-500/40 bg-slate-900 shadow-xl shadow-red-500/10 ring-1 ring-red-500/20"
          role="alert"
        >
          <div className="flex items-start gap-3 p-4">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-red-500/20 text-red-400">
              <Flame size={20} />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-semibold text-red-400">Fire detected</p>
              <p className="mt-0.5 truncate text-sm font-medium text-white">
                {toast.device_name || `Device #${toast.device_id}`}
              </p>
              <p className="text-xs text-slate-400">
                Confidence {formatPercent(toast.confidence)}
                {toast.temperature != null && ` · ${toast.temperature}°C`}
              </p>
            </div>
            <button
              type="button"
              onClick={() => onDismiss(toast.id)}
              className="shrink-0 rounded p-1 text-slate-500 hover:bg-slate-800 hover:text-slate-300"
              aria-label="Dismiss"
            >
              <X size={16} />
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}
