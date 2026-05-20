import { useState } from 'react'
import { formatDate } from '../../utils/format'

export default function IncidentNotes({ notes, canEdit, busy, onAdd }) {
  const [message, setMessage] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    const text = message.trim()
    if (!text) return
    await onAdd(text)
    setMessage('')
  }

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
      <h3 className="mb-4 text-sm font-semibold uppercase tracking-wide text-slate-400">
        Notes
      </h3>

      {canEdit && (
        <form onSubmit={handleSubmit} className="mb-4 space-y-2">
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Add operator note..."
            rows={3}
            disabled={busy}
            className="w-full resize-y rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200 placeholder:text-slate-600 focus:border-orange-500/50 focus:outline-none focus:ring-1 focus:ring-orange-500/30"
          />
          <button
            type="submit"
            disabled={busy || !message.trim()}
            className="rounded-lg bg-orange-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-orange-500 disabled:opacity-50"
          >
            Add note
          </button>
        </form>
      )}

      <ul className="space-y-3">
        {notes.length === 0 ? (
          <li className="text-sm text-slate-500">No notes yet.</li>
        ) : (
          notes.map((note) => (
            <li
              key={note.id}
              className="rounded-lg border border-slate-800 bg-slate-950/60 px-4 py-3"
            >
              <p className="text-sm text-slate-200 whitespace-pre-wrap">{note.message}</p>
              <p className="mt-2 text-xs text-slate-500">
                {note.user_name || 'Operator'} · {formatDate(note.created_at)}
              </p>
            </li>
          ))
        )}
      </ul>
    </div>
  )
}
