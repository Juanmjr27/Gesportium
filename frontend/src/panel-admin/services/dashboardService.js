import { apiClient } from '../../shared/services/apiClient'

export function obtenerKpis(params) {
  return apiClient.get('/dashboard/kpis', { params }).then((res) => res.data)
}
