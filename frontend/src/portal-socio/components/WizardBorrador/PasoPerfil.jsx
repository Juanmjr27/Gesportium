import { useEffect, useState } from 'react'
import { useAuth } from '../../hooks/useAuth'
import * as sociosService from '../../services/sociosService'
import * as membresiasService from '../../services/membresiasService'
import * as planesService from '../../services/planesService'

// Espeja backend/app/modules/asistente_ia/service.py::calcular_edad
function calcularEdad(fechaNacimientoIso) {
  const hoy = new Date()
  const nacimiento = new Date(fechaNacimientoIso)
  let edad = hoy.getFullYear() - nacimiento.getFullYear()
  const noHaCumplidoAun =
    hoy.getMonth() < nacimiento.getMonth() || (hoy.getMonth() === nacimiento.getMonth() && hoy.getDate() < nacimiento.getDate())
  if (noHaCumplidoAun) edad -= 1
  return edad
}

export default function PasoPerfil({ titulo, actualizarRespuestas }) {
  const { socio } = useAuth()

  const [fechaNacimiento, setFechaNacimiento] = useState(socio?.fecha_nacimiento ?? null)
  const [tipoMembresia, setTipoMembresia] = useState(null)
  const [cargandoMembresia, setCargandoMembresia] = useState(true)

  const [fechaEditada, setFechaEditada] = useState('')
  const [guardando, setGuardando] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!socio) return
    Promise.all([membresiasService.listarMisMembresias(), planesService.listarPlanesPublico().catch(() => [])])
      .then(([membresias, planes]) => {
        const activa = membresias.find((m) => m.estado === 'activa') ?? null
        const plan = activa ? (planes.find((p) => p.id === activa.plan_id) ?? null) : null
        setTipoMembresia(plan?.nombre ?? 'Sin membresía activa')
      })
      .catch(() => setTipoMembresia('Sin membresía activa'))
      .finally(() => setCargandoMembresia(false))
  }, [socio])

  useEffect(() => {
    actualizarRespuestas({ fecha_nacimiento_ok: Boolean(fechaNacimiento) })
  }, [fechaNacimiento, actualizarRespuestas])

  async function handleGuardarFecha(event) {
    event.preventDefault()
    if (!fechaEditada || !socio) return
    setGuardando(true)
    setError(null)
    try {
      await sociosService.actualizarSocio(socio.id, { fecha_nacimiento: fechaEditada })
      setFechaNacimiento(fechaEditada)
    } catch {
      setError('No se pudo guardar tu fecha de nacimiento. Inténtalo de nuevo.')
    } finally {
      setGuardando(false)
    }
  }

  return (
    <div className="py-6 flex flex-col gap-4">
      <h3 className="font-display text-xl text-on-surface">{titulo}</h3>
      <p className="text-sm text-on-surface-variant">Confirma que estos datos, que ya tenemos de ti, son correctos.</p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="rounded-lg border border-outline-variant px-4 py-3">
          <p className="text-xs uppercase tracking-widest text-on-surface-variant mb-1">Edad</p>
          {fechaNacimiento ? (
            <p className="text-on-surface font-bold">{calcularEdad(fechaNacimiento)} años</p>
          ) : (
            <p className="text-on-surface-variant text-sm italic">Sin registrar</p>
          )}
        </div>
        <div className="rounded-lg border border-outline-variant px-4 py-3">
          <p className="text-xs uppercase tracking-widest text-on-surface-variant mb-1">Membresía</p>
          <p className="text-on-surface font-bold">{cargandoMembresia ? 'Cargando…' : tipoMembresia}</p>
        </div>
      </div>

      {!fechaNacimiento && (
        <form onSubmit={handleGuardarFecha} className="rounded-lg border border-outline-variant px-4 py-4 flex flex-col gap-3">
          <p className="text-sm text-on-surface-variant">
            Nos falta tu fecha de nacimiento para calcular tu edad. Indícala para continuar.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center">
            <input
              type="date"
              value={fechaEditada}
              onChange={(e) => setFechaEditada(e.target.value)}
              required
              className="bg-surface-container border-0 border-b-2 border-white/10 text-tertiary px-4 py-3 focus:ring-0 focus:outline-none input-energetic transition-colors rounded-t-lg"
            />
            <button
              type="submit"
              disabled={guardando || !fechaEditada}
              className="px-4 py-2 rounded-lg bg-primary-fixed text-on-primary-fixed font-bold disabled:opacity-60"
            >
              {guardando ? 'Guardando…' : 'Guardar'}
            </button>
          </div>
          {error && <p className="text-error text-sm">{error}</p>}
        </form>
      )}
    </div>
  )
}
