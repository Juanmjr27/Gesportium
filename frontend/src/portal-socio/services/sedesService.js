import { apiClient } from '../../shared/services/apiClient'

export function listarSedesPublico() {
  return apiClient.get('/sedes').then((res) => res.data)
}
