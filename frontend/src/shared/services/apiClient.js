import axios from 'axios'

// El JWT se guarda solo en memoria (ver hooks/useAuth.jsx): el backend
// devuelve un bearer token plano, no una cookie httpOnly, así que la opción
// más segura disponible sin tocar el backend es no persistirlo en
// localStorage/sessionStorage (vulnerable a XSS) — a costa de perder la
// sesión al recargar la página (plan.md Fase 2).
let accessToken = null

export function setAccessToken(token) {
  accessToken = token
}

export function getAccessToken() {
  return accessToken
}

export const apiClient = axios.create({
  baseURL: '/api',
})

apiClient.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  return config
})

let onUnauthorized = null

export function setUnauthorizedHandler(handler) {
  onUnauthorized = handler
}

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && onUnauthorized) {
      onUnauthorized()
    }
    return Promise.reject(error)
  },
)
