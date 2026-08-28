import { apiClient } from '../../shared/services/apiClient'

export function crearRutina(body) {
  return apiClient.post('/rutinas', body).then((res) => res.data)
}

export function editarRutina(rutinaId, body) {
  return apiClient.put(`/rutinas/${rutinaId}`, body).then((res) => res.data)
}

export function crearPlanNutricional(body) {
  return apiClient.post('/planes-nutricionales', body).then((res) => res.data)
}

export function editarPlanNutricional(planId, body) {
  return apiClient.put(`/planes-nutricionales/${planId}`, body).then((res) => res.data)
}
