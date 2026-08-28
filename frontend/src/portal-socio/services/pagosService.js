import { apiClient } from '../../shared/services/apiClient'

export function listarPagos(socioId) {
  return apiClient.get(`/pagos/${socioId}`).then((res) => res.data)
}

export function descargarFactura(facturaId) {
  return apiClient.get(`/facturas/${facturaId}`, { responseType: 'blob' }).then((res) => {
    const disposition = res.headers['content-disposition'] ?? ''
    const match = disposition.match(/filename="?([^"]+)"?/)
    return { blob: res.data, filename: match?.[1] ?? `factura-${facturaId}.pdf` }
  })
}
