import { apiClient } from '../../shared/services/apiClient'

export function listarMisMembresias() {
  return apiClient.get('/membresias').then((res) => res.data)
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
