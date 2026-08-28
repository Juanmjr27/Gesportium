import { apiClient } from '../../shared/services/apiClient'

export function listarPlanesPublico() {
  return apiClient.get('/planes-membresia').then((res) => res.data)
}
