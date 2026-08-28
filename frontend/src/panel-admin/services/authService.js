import { apiClient } from '../../shared/services/apiClient'

export function login(email, password) {
  return apiClient.post('/auth/login', { email, password }).then((res) => res.data)
}

export function logout() {
  return apiClient.post('/auth/logout')
}

export function obtenerUsuarioActual() {
  return apiClient.get('/auth/me').then((res) => res.data)
}
