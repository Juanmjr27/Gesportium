import { apiClient } from '../../shared/services/apiClient'

export function obtenerSocioPropio() {
  return apiClient.get('/socios/me').then((res) => res.data)
}

export function actualizarSocio(socioId, cambios) {
  return apiClient.put(`/socios/${socioId}`, cambios).then((res) => res.data)
}
