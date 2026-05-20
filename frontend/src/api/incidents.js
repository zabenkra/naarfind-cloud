import apiClient from './client'

export async function fetchIncidents(includeAll = false) {
  const { data } = await apiClient.get('/api/incidents', {
    params: includeAll ? { include_all: true } : {},
  })
  return data
}

export async function fetchIncident(id) {
  const { data } = await apiClient.get(`/api/incidents/${id}`)
  return data
}

export async function updateIncidentStatus(id, status) {
  const { data } = await apiClient.patch(`/api/incidents/${id}/status`, { status })
  return data
}

export async function fetchIncidentNotes(id) {
  const { data } = await apiClient.get(`/api/incidents/${id}/notes`)
  return data
}

export async function addIncidentNote(id, message) {
  const { data } = await apiClient.post(`/api/incidents/${id}/notes`, { message })
  return data
}
