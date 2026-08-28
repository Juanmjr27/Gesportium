import { apiClient } from '../../shared/services/apiClient'

export function listarPlanes() {
  return apiClient.get('/planes-membresia').then((res) => res.data)
}

export function crearPlan(body) {
  return apiClient.post('/planes-membresia', body).then((res) => res.data)
}

export function actualizarPlan(planId, body) {
  return apiClient.put(`/planes-membresia/${planId}`, body).then((res) => res.data)
}

export function listarMembresias(params) {
  return apiClient.get('/membresias', { params }).then((res) => res.data)
}

export function obtenerMembresia(membresiaId) {
  return apiClient.get(`/membresias/${membresiaId}`).then((res) => res.data)
}

export function crearMembresia(body) {
  return apiClient.post('/membresias', body).then((res) => res.data)
}

export function congelarMembresia(membresiaId, motivo) {
  return apiClient.post(`/membresias/${membresiaId}/congelar`, { motivo }).then((res) => res.data)
}

export function reactivarMembresia(membresiaId) {
  return apiClient.post(`/membresias/${membresiaId}/reactivar`).then((res) => res.data)
}

export function cancelarMembresia(membresiaId, motivo) {
  return apiClient.post(`/membresias/${membresiaId}/cancelar`, { motivo }).then((res) => res.data)
}
