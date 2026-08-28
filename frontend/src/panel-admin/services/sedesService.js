import { apiClient } from '../../shared/services/apiClient'

export function listarSedes() {
  return apiClient.get('/sedes').then((res) => res.data)
}

export function obtenerSede(sedeId) {
  return apiClient.get(`/sedes/${sedeId}`).then((res) => res.data)
}

export function crearSede(body) {
  return apiClient.post('/sedes', body).then((res) => res.data)
}

export function actualizarSede(sedeId, body) {
  return apiClient.put(`/sedes/${sedeId}`, body).then((res) => res.data)
}

export function eliminarSede(sedeId) {
  return apiClient.delete(`/sedes/${sedeId}`)
}
