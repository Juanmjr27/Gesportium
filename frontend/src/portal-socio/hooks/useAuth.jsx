import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import * as authService from '../services/authService'
import * as sociosService from '../services/sociosService'
import { setAccessToken, setUnauthorizedHandler } from '../../shared/services/apiClient'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [usuario, setUsuario] = useState(null)
  const [socio, setSocio] = useState(null)
  const [cargando, setCargando] = useState(false)

  const limpiarSesion = useCallback(() => {
    setAccessToken(null)
    setUsuario(null)
    setSocio(null)
  }, [])

  useEffect(() => {
    setUnauthorizedHandler(limpiarSesion)
  }, [limpiarSesion])

  const cargarSesion = useCallback(async (token) => {
    setAccessToken(token)
    const datosUsuario = await authService.obtenerUsuarioActual()
    setUsuario(datosUsuario)
    try {
      const datosSocio = await sociosService.obtenerSocioPropio()
      setSocio(datosSocio)
    } catch (error) {
      // 404: la cuenta existe pero un admin/gestor_sede aún no ha dado de
      // alta el Socio asociado (flujo normal, ver socioPendienteDeAlta).
      if (error.response?.status !== 404) throw error
      setSocio(null)
    }
  }, [])

  const iniciarSesion = useCallback(
    async (email, password) => {
      setCargando(true)
      try {
        const { access_token: token } = await authService.login(email, password)
        await cargarSesion(token)
      } finally {
        setCargando(false)
      }
    },
    [cargarSesion],
  )

  const registrar = useCallback(
    async (email, password, sedeId) => {
      setCargando(true)
      try {
        await authService.register(email, password, sedeId)
        const { access_token: token } = await authService.login(email, password)
        setAccessToken(token)
        try {
          const datosUsuario = await authService.obtenerUsuarioActual()
          setUsuario(datosUsuario)
        } finally {
          setCargando(false)
        }
      } catch (error) {
        setCargando(false)
        throw error
      }
    },
    [],
  )

  const cerrarSesion = useCallback(() => {
    authService.logout().catch(() => {})
    limpiarSesion()
  }, [limpiarSesion])

  const value = useMemo(
    () => ({
      usuario,
      socio,
      cargando,
      autenticado: Boolean(usuario),
      // Un usuario recién registrado tiene cuenta pero aún no tiene un
      // Socio dado de alta por un admin/gestor_sede (specs/003) — el
      // portal debe distinguir ambos estados en vez de tratarlo como error.
      socioPendienteDeAlta: Boolean(usuario) && !socio,
      iniciarSesion,
      registrar,
      cerrarSesion,
    }),
    [usuario, socio, cargando, iniciarSesion, registrar, cerrarSesion],
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
