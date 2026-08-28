import { apiClient } from '../../shared/services/apiClient'

export function obtenerHistorial() {
  return apiClient.get('/asistente/historial').then((res) => res.data)
}

export function enviarMensaje(contenido) {
  return apiClient.post('/asistente/mensaje', { contenido }).then((res) => res.data)
}

export function solicitarBorrador(datosWizard) {
  return apiClient.post('/asistente/borrador', datosWizard).then((res) => res.data)
}
