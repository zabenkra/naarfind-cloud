export function getApiErrorMessage(error, fallback = 'Something went wrong') {
  if (!error) return fallback

  if (!error.response) {
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
    if (error.code === 'ECONNABORTED') {
      return 'Request timed out. The API may be slow or unavailable.'
    }
    return `Cannot reach the API at ${apiUrl}. Check that the backend is running and VITE_API_URL is correct.`
  }

  const detail = error.response?.data?.detail
  if (typeof detail === 'string') {
    if (error.response?.status === 404 && detail === 'Not Found') {
      return 'Incident not found or you do not have access'
    }
    return detail
  }
  if (Array.isArray(detail)) {
    return detail.map((d) => d.msg || JSON.stringify(d)).join(', ')
  }
  if (detail && typeof detail === 'object') {
    if (typeof detail.detail === 'string') return detail.detail
    if (detail.requested_id != null && detail.reason) {
      return `${detail.detail || fallback} (id: ${detail.requested_id})`
    }
    return detail.message || JSON.stringify(detail)
  }

  return error.message || fallback
}
