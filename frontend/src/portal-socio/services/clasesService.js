import { apiClient } from '../../shared/services/apiClient'

export function listarClases({ sedeId, fecha } = {}) {
  return apiClient.get('/clases', { params: { sede_id: sedeId, fecha } }).then((res) => res.data)
}

export function obtenerClase(claseId) {
  return apiClient.get(`/clases/${claseId}`).then((res) => res.data)
}

export function reservarClase(claseId) {
  return apiClient.post(`/clases/${claseId}/reservar`).then((res) => res.data)
}

export function cancelarReserva(reservaId) {
  return apiClient.delete(`/reservas/${reservaId}`)
}

export function listarMisReservas() {
  return apiClient.get('/reservas').then((res) => res.data)
}
