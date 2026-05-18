import apiClient from './client'

export async function register({ organizationName, fullName, email, password }) {
  const { data } = await apiClient.post('/api/auth/register', {
    organization_name: organizationName,
    full_name: fullName,
    email,
    password,
  })
  return data
}

export async function login({ email, password }) {
  const { data } = await apiClient.post('/api/auth/login', { email, password })
  return data
}

export async function fetchMe() {
  const { data } = await apiClient.get('/api/auth/me')
  return data
}
