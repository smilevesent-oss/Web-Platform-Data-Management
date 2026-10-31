import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { api, getToken, setToken } from './api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [ready, setReady] = useState(false)

  const refresh = useCallback(async () => {
    if (!getToken()) { setUser(null); setReady(true); return }
    try {
      setUser(await api('/auth/me'))
    } catch {
      setToken(null)
      setUser(null)
    } finally {
      setReady(true)
    }
  }, [])

  useEffect(() => { refresh() }, [refresh])

  const login = async (username, password) => {
    const res = await api('/auth/login', { method: 'POST', body: { username, password } })
    setToken(res.access_token)
    setUser(res.user)
    return res.user
  }
  const register = async (payload) => {
    const res = await api('/auth/register', { method: 'POST', body: payload })
    setToken(res.access_token)
    setUser(res.user)
    return res.user
  }
  const logout = () => { setToken(null); setUser(null) }

  const value = useMemo(() => {
    const perms = new Set(user?.permissions || [])
    return {
      user, ready, login, register, logout, refresh, setUser,
      can: (...codes) => codes.some((c) => perms.has(c)),
      isStaff: perms.size > 0,
    }
  }, [user, ready, refresh])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = () => useContext(AuthContext)
