import apiClient from './client'

const INCIDENT_NOT_FOUND = 'Incident not found for this organization'

function parseIncidentId(id) {
  const incidentId = Number(id)
  if (!Number.isInteger(incidentId) || incidentId <= 0) {
    throw new Error('Invalid incident ID')
  }
  return incidentId
}

function enrichIncidentError(err, fallback) {
  if (err.response?.status === 404) {
    const next = new Error(INCIDENT_NOT_FOUND)
    next.response = err.response
    return next
  }
  if (!err.response && err.message) {
    return err
  }
  return err
}

export async function fetchIncidents(includeAll = false) {
  const { data } = await apiClient.get('/api/incidents', {
    params: includeAll ? { include_all: true } : {},
  })
  return data
}

export async function fetchIncident(id) {
  const incidentId = parseIncidentId(id)
  try {
    const { data } = await apiClient.get(`/api/incidents/${incidentId}`)
    if (!data?.id) {
      throw new Error(INCIDENT_NOT_FOUND)
    }
    return data
  } catch (err) {
    throw enrichIncidentError(err, INCIDENT_NOT_FOUND)
  }
}

export async function updateIncidentStatus(id, status) {
  const incidentId = parseIncidentId(id)
  try {
    const { data } = await apiClient.patch(`/api/incidents/${incidentId}/status`, {
      status,
    })
    return data
  } catch (err) {
    throw enrichIncidentError(err, 'Failed to update incident status')
  }
}

export async function fetchIncidentNotes(id) {
  const incidentId = parseIncidentId(id)
  const { data } = await apiClient.get(`/api/incidents/${incidentId}/notes`)
  return data
}

export async function addIncidentNote(id, message) {
  const incidentId = parseIncidentId(id)
  const { data } = await apiClient.post(`/api/incidents/${incidentId}/notes`, {
    message,
  })
  return data
}
