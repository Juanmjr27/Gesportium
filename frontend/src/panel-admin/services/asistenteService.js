import { apiClient } from '../../shared/services/apiClient'

export function listarBorradoresPendientes() {
  return apiClient.get('/asistente/borradores-pendientes').then((res) => res.data)
}

export function editarBorrador(borradorId, contenido) {
  return apiClient.patch(`/asistente/borradores/${borradorId}`, { contenido }).then((res) => res.data)
}

export function aprobarBorrador(borradorId) {
  return apiClient.post(`/asistente/borradores/${borradorId}/aprobar`).then((res) => res.data)
}

export function rechazarBorrador(borradorId, motivo) {
  return apiClient.post(`/asistente/borradores/${borradorId}/rechazar`, { motivo }).then((res) => res.data)
}
