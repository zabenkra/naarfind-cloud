import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { fetchMe, login as apiLogin, register as apiRegister } from '../api/auth'
import { clearToken, getToken, setToken } from '../lib/authStorage'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  const loadUser = useCallback(async () => {
    const token = getToken()
    if (!token) {
      setUser(null)
      setLoading(false)
      return
    }
    try {
      setUser(await fetchMe())
    } catch {
      clearToken()
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadUser()
  }, [loadUser])

  const login = useCallback(async (email, password) => {
    const { access_token } = await apiLogin({ email, password })
    setToken(access_token)
    const me = await fetchMe()
    setUser(me)
    return me
  }, [])

  const register = useCallback(async (organizationName, fullName, email, password) => {
    const { access_token } = await apiRegister({
      organizationName,
      fullName,
      email,
      password,
    })
    setToken(access_token)
    const me = await fetchMe()
    setUser(me)
    return me
  }, [])

  const logout = useCallback(() => {
    clearToken()
    setUser(null)
  }, [])

  const value = useMemo(
    () => ({
      user,
      loading,
      isAuthenticated: Boolean(user),
      login,
      register,
      logout,
      refreshUser: loadUser,
    }),
    [user, loading, login, register, logout, loadUser],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}

export function useHasRole(...roles) {
  const { user } = useAuth()
  return user && roles.includes(user.role)
}
