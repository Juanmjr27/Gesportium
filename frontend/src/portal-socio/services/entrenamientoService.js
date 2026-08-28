import { apiClient } from '../../shared/services/apiClient'

export function listarRutinas(socioId) {
  return apiClient.get(`/rutinas/${socioId}`).then((res) => res.data)
}

export function listarPlanesNutricionales(socioId) {
  return apiClient.get(`/planes-nutricionales/${socioId}`).then((res) => res.data)
}

export function completarEjercicio(rutinaId, ejercicioId, completado = true) {
  return apiClient
    .post(`/rutinas/${rutinaId}/completar`, { ejercicio_id: ejercicioId, completado })
    .then((res) => res.data)
}
