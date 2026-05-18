import apiClient from './client'

export async function fetchDashboardStats() {
  const { data } = await apiClient.get('/api/dashboard/stats')
  return data
}
