import { apiClient } from '../../shared/services/apiClient'

export function listarEntrenadores() {
  return apiClient.get('/entrenadores').then((res) => res.data)
}

export function obtenerEntrenador(entrenadorId) {
  return apiClient.get(`/entrenadores/${entrenadorId}`).then((res) => res.data)
}

export function crearEntrenador(body) {
  return apiClient.post('/entrenadores', body).then((res) => res.data)
}

export function actualizarEntrenador(entrenadorId, body) {
  return apiClient.put(`/entrenadores/${entrenadorId}`, body).then((res) => res.data)
}

export function darDeBajaEntrenador(entrenadorId, body) {
  return apiClient.delete(`/entrenadores/${entrenadorId}`, { data: body }).then((res) => res.data)
}

export function listarSociosAsignados(entrenadorId) {
  return apiClient.get(`/entrenadores/${entrenadorId}/socios`).then((res) => res.data)
}

export function asignarSocio(entrenadorId, socioId) {
  return apiClient.post(`/entrenadores/${entrenadorId}/socios`, { socio_id: socioId }).then((res) => res.data)
}

export function desasignarSocio(entrenadorId, socioId) {
  return apiClient.delete(`/entrenadores/${entrenadorId}/socios/${socioId}`)
}
