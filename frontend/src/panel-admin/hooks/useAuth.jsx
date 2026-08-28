import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import * as authService from '../services/authService'
import { setAccessToken, setUnauthorizedHandler } from '../../shared/services/apiClient'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [usuario, setUsuario] = useState(null)
  const [cargando, setCargando] = useState(false)

  const limpiarSesion = useCallback(() => {
    setAccessToken(null)
    setUsuario(null)
  }, [])

  useEffect(() => {
    setUnauthorizedHandler(limpiarSesion)
  }, [limpiarSesion])

  const iniciarSesion = useCallback(async (email, password) => {
    setCargando(true)
    try {
      const { access_token: token } = await authService.login(email, password)
      setAccessToken(token)
      const datosUsuario = await authService.obtenerUsuarioActual()
      setUsuario(datosUsuario)
    } finally {
      setCargando(false)
    }
  }, [])

  const cerrarSesion = useCallback(() => {
    authService.logout().catch(() => {})
    limpiarSesion()
  }, [limpiarSesion])

  const value = useMemo(
    () => ({
      usuario,
      cargando,
      autenticado: Boolean(usuario),
      iniciarSesion,
      cerrarSesion,
    }),
    [usuario, cargando, iniciarSesion, cerrarSesion],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth debe usarse dentro de un AuthProvider')
  }
  return context
}
