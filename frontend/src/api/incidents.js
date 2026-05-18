import apiClient from './client'

export async function fetchIncidents() {
  const { data } = await apiClient.get('/api/incidents')
  return data
}
