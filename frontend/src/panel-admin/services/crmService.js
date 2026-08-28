import { apiClient } from '../../shared/services/apiClient'

export function listarLeads(params) {
  return apiClient.get('/leads', { params }).then((res) => res.data)
}

export function crearLead(body) {
  return apiClient.post('/leads', body).then((res) => res.data)
}

export function actualizarLead(leadId, body) {
  return apiClient.put(`/leads/${leadId}`, body).then((res) => res.data)
}

export function anadirInteraccion(leadId, body) {
  return apiClient.post(`/leads/${leadId}/interacciones`, body).then((res) => res.data)
}

export function convertirLead(leadId, body) {
  return apiClient.post(`/leads/${leadId}/convertir`, body).then((res) => res.data)
}
