import apiClient from './client'

export async function fetchFireEvents() {
  const { data } = await apiClient.get('/api/events/fire')
  return data
}

export async function updateFireEventStatus(eventId, status) {
  const { data } = await apiClient.patch(`/api/events/fire/${eventId}/status`, {
    status,
  })
  return data
}
