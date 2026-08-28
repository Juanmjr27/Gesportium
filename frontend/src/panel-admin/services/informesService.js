import { apiClient } from '../../shared/services/apiClient'

export function obtenerInforme(tipo, params) {
  return apiClient.get(`/informes/${tipo}`, { params }).then((res) => res.data)
}

export function exportarInforme(tipo, params) {
  return apiClient.get(`/informes/${tipo}/exportar`, { params, responseType: 'blob' }).then((res) => res.data)
}

export function generarResumenIA(tipo, params) {
  return apiClient.post(`/informes/${tipo}/resumen-ia`, null, { params }).then((res) => res.data)
}
