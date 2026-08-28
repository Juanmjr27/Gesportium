import { useEffect, useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import * as pagosService from '../services/pagosService'

const ESTADO_LABEL = {
  exitoso: 'Pagado',
  pendiente: 'Pendiente',
  fallido: 'Fallido',
}

function formatearFecha(fechaIso) {
  return new Date(fechaIso).toLocaleDateString('es-ES', { day: '2-digit', month: 'short', year: 'numeric' })
}

function formatearImporte(importe) {
  return new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR' }).format(Number(importe))
}

export default function PagosPage() {
  const { socio } = useAuth()
  const [pagos, setPagos] = useState([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState(null)
  const [descargando, setDescargando] = useState(null)

  useEffect(() => {
    if (!socio) return
    pagosService
      .listarPagos(socio.id)
      .then(setPagos)
      .catch(() => setError('No se pudo cargar el historial de pagos.'))
      .finally(() => setCargando(false))
  }, [socio])

  const alDia = pagos.length === 0 || pagos[0]?.estado === 'exitoso'

  async function handleDescargar(facturaId) {
    setDescargando(facturaId)
    setError(null)
    try {
      const { blob, filename } = await pagosService.descargarFactura(facturaId)
      const url = URL.createObjectURL(blob)
      const enlace = document.createElement('a')
      enlace.href = url
      enlace.download = filename
      document.body.appendChild(enlace)
      enlace.click()
      enlace.remove()
      URL.revokeObjectURL(url)
    } catch {
      setError('No se pudo descargar la factura.')
    } finally {
      setDescargando(null)
    }
  }

  return (
    <div className="py-8 md:py-16">
      <div className="mb-10 flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-4xl md:text-6xl text-primary uppercase tracking-tighter">Historial de Pagos</h1>
          <p className="text-on-surface-variant mt-2">Revisa tus transacciones y descarga tus facturas.</p>
        </div>
        <div className="glass-card rounded-xl p-6 flex items-center gap-6 w-full md:w-auto">
          <div className={`w-12 h-12 rounded-full flex items-center justify-center ${alDia ? 'bg-primary-fixed/20 pulse-green' : 'bg-error/20'}`}>
            <span
              className={`material-symbols-outlined ${alDia ? 'text-primary-fixed' : 'text-error'}`}
              style={{ fontVariationSettings: "'FILL' 1" }}
            >
              {alDia ? 'check_circle' : 'error'}
            </span>
          </div>
          <div>
            <p className="text-xs text-on-surface-variant uppercase tracking-wider">Estado de Cuenta</p>
            <p className="font-display text-2xl text-primary">{alDia ? 'Al día' : 'Requiere atención'}</p>
          </div>
        </div>
      </div>

      {error && <p className="text-error mb-6">{error}</p>}
      {cargando && <p className="text-on-surface-variant">Cargando pagos…</p>}
      {!cargando && pagos.length === 0 && <p className="text-on-surface-variant">Todavía no tienes pagos registrados.</p>}

      {pagos.length > 0 && (
        <div className="glass-card rounded-xl overflow-hidden">
          <div className="px-6 py-4 border-b border-white/10 bg-surface-container/50 hidden md:grid grid-cols-12 gap-4">
            <div className="col-span-4 text-xs text-on-surface-variant uppercase tracking-wider">Concepto</div>
            <div className="col-span-3 text-xs text-on-surface-variant uppercase tracking-wider">Fecha</div>
            <div className="col-span-3 text-xs text-on-surface-variant uppercase tracking-wider text-right">Monto</div>
            <div className="col-span-2 text-xs text-on-surface-variant uppercase tracking-wider text-center">Factura</div>
          </div>
          <div className="flex flex-col">
            {pagos.map((pago) => (
              <div
                key={pago.id}
                className="border-b border-white/5 last:border-none px-6 py-5 flex flex-col md:grid md:grid-cols-12 gap-4 items-start md:items-center hover:bg-white/5 transition-colors"
              >
                <div className="col-span-4 w-full flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-surface-container flex items-center justify-center">
                    <span className="material-symbols-outlined text-on-surface-variant">fitness_center</span>
                  </div>
                  <div>
                    <p className="text-primary font-bold">{pago.concepto}</p>
                    <p className="text-xs text-on-surface-variant md:hidden">{formatearFecha(pago.fecha)}</p>
                    <p className="text-xs text-on-surface-variant">{ESTADO_LABEL[pago.estado] ?? pago.estado}</p>
                  </div>
                </div>
                <div className="col-span-3 hidden md:block">
                  <p className="text-on-surface">{formatearFecha(pago.fecha)}</p>
                </div>
                <div className="col-span-3 w-full flex justify-between md:block md:text-right">
                  <span className="md:hidden text-xs text-on-surface-variant">Monto:</span>
                  <p className="font-display text-2xl text-primary-fixed">{formatearImporte(pago.importe)}</p>
                </div>
                <div className="col-span-2 w-full md:w-auto flex justify-end md:justify-center mt-2 md:mt-0">
                  {pago.factura_id ? (
                    <button
                      onClick={() => handleDescargar(pago.factura_id)}
                      disabled={descargando === pago.factura_id}
                      title="Descargar Factura"
                      className="w-10 h-10 rounded-full border border-primary-fixed text-primary-fixed flex items-center justify-center hover:bg-primary-fixed hover:text-background transition-colors disabled:opacity-60"
                    >
                      <span className="material-symbols-outlined">download</span>
                    </button>
                  ) : (
                    <span className="text-xs text-on-surface-variant">—</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
