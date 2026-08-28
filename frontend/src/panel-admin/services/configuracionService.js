import { apiClient } from '../../shared/services/apiClient'

export function listarConfiguracion() {
  return apiClient.get('/configuracion').then((res) => res.data)
}

export function actualizarConfiguracion(clave, valor) {
  return apiClient.put(`/configuracion/${clave}`, { valor }).then((res) => res.data)
}
