import { apiClient } from '../../shared/services/apiClient'

export function listarSocios(params) {
  return apiClient.get('/socios', { params }).then((res) => res.data)
}

export function listarCandidatosAlta(q) {
  return apiClient.get('/socios/candidatos-alta', { params: q ? { q } : {} }).then((res) => res.data)
}

export function obtenerSocio(socioId) {
  return apiClient.get(`/socios/${socioId}`).then((res) => res.data)
}

export function obtenerFichaSocio(socioId) {
  return apiClient.get(`/socios/${socioId}/ficha`).then((res) => res.data)
}

export function crearSocio(body) {
  return apiClient.post('/socios', body).then((res) => res.data)
}

export function actualizarSocio(socioId, body) {
  return apiClient.put(`/socios/${socioId}`, body).then((res) => res.data)
}

export function eliminarSocio(socioId) {
  return apiClient.delete(`/socios/${socioId}`)
}

export function transferirSocio(socioId, nuevaSedeId) {
  return apiClient.post(`/socios/${socioId}/transferir`, { nueva_sede_id: nuevaSedeId }).then((res) => res.data)
}

export function anadirNota(socioId, contenido) {
  return apiClient.post(`/socios/${socioId}/notas`, { contenido }).then((res) => res.data)
}
