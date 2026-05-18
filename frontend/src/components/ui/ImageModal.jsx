import { X } from 'lucide-react'

export default function ImageModal({ url, alt, onClose }) {
  if (!url) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-sm"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="Image preview"
    >
      <button
        type="button"
        onClick={onClose}
        className="absolute right-4 top-4 rounded-lg bg-slate-900/90 p-2 text-slate-300 hover:bg-slate-800 hover:text-white"
        aria-label="Close"
      >
        <X size={22} />
      </button>
      <img
        src={url}
        alt={alt || 'Fire event snapshot'}
        className="max-h-[90vh] max-w-full rounded-xl border border-slate-700 object-contain shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      />
    </div>
  )
}
