import { apiClient } from '../../shared/services/apiClient'

export function listarPagosDeSocio(socioId) {
  return apiClient.get(`/pagos/${socioId}`).then((res) => res.data)
}

export function obtenerFactura(facturaId) {
  return apiClient.get(`/facturas/${facturaId}`).then((res) => res.data)
}

export function anularFactura(facturaId) {
  return apiClient.post(`/facturas/${facturaId}/anular`).then((res) => res.data)
}

export function reemitirFactura(facturaId) {
  return apiClient.post(`/facturas/${facturaId}/reemitir`).then((res) => res.data)
}

export function listarRemesas(params) {
  return apiClient.get('/remesas', { params }).then((res) => res.data)
}

export function crearRemesa(body) {
  return apiClient.post('/remesas', body).then((res) => res.data)
}
