import apiClient from './client'

export async function fetchDevices() {
  const { data } = await apiClient.get('/api/devices')
  return data
}
