import { apiClient } from '../../shared/services/apiClient'

export function listarAccesos(socioId) {
  return apiClient.get(`/accesos/${socioId}`).then((res) => res.data)
}
