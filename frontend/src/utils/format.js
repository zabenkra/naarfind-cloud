export function formatDate(value) {
  if (!value) return '—'
  return new Date(value).toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function formatPercent(value) {
  if (value == null) return '—'
  const pct = value <= 1 ? value * 100 : value
  return `${Math.round(pct)}%`
}
