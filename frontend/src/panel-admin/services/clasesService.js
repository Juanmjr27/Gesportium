import { apiClient } from '../../shared/services/apiClient'

export function listarClases(params) {
  return apiClient.get('/clases', { params }).then((res) => res.data)
}

export function obtenerClase(claseId) {
  return apiClient.get(`/clases/${claseId}`).then((res) => res.data)
}

export function crearClase(body) {
  return apiClient.post('/clases', body).then((res) => res.data)
}

export function actualizarClase(claseId, body) {
  return apiClient.put(`/clases/${claseId}`, body).then((res) => res.data)
}
