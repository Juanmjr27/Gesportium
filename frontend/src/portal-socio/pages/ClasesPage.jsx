import { useEffect, useMemo, useState } from 'react'
import * as clasesService from '../services/clasesService'

// Debe reflejar HORAS_LIMITE_CANCELACION_CONFIRMADA del backend
// (backend/app/modules/clases/service.py). Solo aplica a reservas
// confirmadas (plaza ocupada); salir de la lista de espera no tiene límite.
const HORAS_LIMITE_CANCELACION_CONFIRMADA = 1

function formatearHora(fechaHoraIso) {
  return new Date(fechaHoraIso).toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })
}

function formatearFecha(fechaHoraIso) {
  return new Date(fechaHoraIso).toLocaleDateString('es-ES', { day: '2-digit', month: 'short' })
}

function claveDia(fechaHoraIso) {
  const d = new Date(fechaHoraIso)
  return `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`
}

function formatearFechaGrupo(fechaHoraIso) {
  const texto = new Date(fechaHoraIso).toLocaleDateString('es-ES', {
    weekday: 'long',
    day: '2-digit',
    month: 'long',
  })
  return texto.charAt(0).toUpperCase() + texto.slice(1)
}

export default function ClasesPage() {
  const [clases, setClases] = useState([])
  const [reservas, setReservas] = useState([])
  const [filtro, setFiltro] = useState('todas')
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState(null)
  const [accionPendiente, setAccionPendiente] = useState(null)

  async function recargar() {
    setCargando(true)
    setError(null)
    try {
      const listado = await clasesService.listarClases()
      const detalles = await Promise.all(listado.map((c) => clasesService.obtenerClase(c.id)))
      const misReservas = await clasesService.listarMisReservas()
      // El catálogo solo muestra clases futuras y activas: las pasadas o
      // canceladas no son reservables y no deben aparecer junto a un
      // contador de "plazas libres" que induce a confusión. Se preserva la
      // visibilidad de una clase ya pasada si el socio tiene reserva sobre
      // ella, para que pueda verla/cancelarla.
      const idsReservados = new Set(misReservas.map((r) => r.clase_id))
      const visibles = detalles.filter(
        (c) => idsReservados.has(c.id) || (c.estado === 'activa' && new Date(c.fecha_hora) >= new Date())
      )
      setClases(visibles)
      setReservas(misReservas)
    } catch {
      setError('No se pudieron cargar las clases.')
    } finally {
      setCargando(false)
    }
  }

  useEffect(() => {
    recargar()
  }, [])

  const tipos = useMemo(() => ['todas', ...new Set(clases.map((c) => c.tipo))], [clases])
  const clasesFiltradas = filtro === 'todas' ? clases : clases.filter((c) => c.tipo === filtro)
  const reservaPorClase = useMemo(() => {
    const mapa = new Map()
    reservas.forEach((r) => mapa.set(r.clase_id, r))
    return mapa
  }, [reservas])

  // Agrupa el catálogo en "Hoy", "Mañana" y el resto por fecha concreta,
  // cada grupo ordenado cronológicamente, para que el socio ubique de un
  // vistazo cuándo es cada clase en vez de una lista plana.
  const grupos = useMemo(() => {
    const claveHoy = claveDia(new Date())
    const fechaManana = new Date()
    fechaManana.setDate(fechaManana.getDate() + 1)
    const claveManana = claveDia(fechaManana)

    const ordenadas = [...clasesFiltradas].sort((a, b) => new Date(a.fecha_hora) - new Date(b.fecha_hora))

    const porDia = new Map()
    ordenadas.forEach((clase) => {
      const clave = claveDia(clase.fecha_hora)
      if (!porDia.has(clave)) porDia.set(clave, [])
      porDia.get(clave).push(clase)
    })

    const resultado = []
    if (porDia.has(claveHoy)) resultado.push({ titulo: 'Hoy', clases: porDia.get(claveHoy) })
    if (porDia.has(claveManana)) resultado.push({ titulo: 'Mañana', clases: porDia.get(claveManana) })
    porDia.forEach((clasesDelDia, clave) => {
      if (clave === claveHoy || clave === claveManana) return
      resultado.push({ titulo: formatearFechaGrupo(clasesDelDia[0].fecha_hora), clases: clasesDelDia })
    })
    return resultado
  }, [clasesFiltradas])

  async function reservar(claseId) {
    setAccionPendiente(claseId)
    setError(null)
    try {
      await clasesService.reservarClase(claseId)
      await recargar()
    } catch (err) {
      if (err.response?.status === 403) setError('Necesitas una membresía activa para reservar.')
      else if (err.response?.status === 409) setError(err.response.data?.detail ?? 'No se pudo reservar esta clase.')
      else setError('No se pudo completar la reserva.')
    } finally {
      setAccionPendiente(null)
    }
  }

  async function cancelar(reservaId) {
    setAccionPendiente(reservaId)
    setError(null)
    try {
      await clasesService.cancelarReserva(reservaId)
      await recargar()
    } catch {
      setError('No se pudo cancelar la reserva.')
    } finally {
      setAccionPendiente(null)
    }
  }

  return (
    <div className="py-8 md:py-16 relative">
      <div className="mb-10 md:mb-14">
        <h2 className="font-display text-4xl md:text-6xl text-primary uppercase mb-4 tracking-tight">
          Catálogo de <span className="text-primary-fixed italic">Clases</span>
        </h2>
        <p className="text-lg text-on-surface-variant max-w-2xl">
          Reserva tu lugar en las sesiones de entrenamiento. Encuentra la disciplina perfecta para superar tus límites
          hoy.
        </p>

        <div className="flex gap-4 mt-8 overflow-x-auto pb-4">
          {tipos.map((tipo) => (
            <button
              key={tipo}
              onClick={() => setFiltro(tipo)}
              className={`shrink-0 rounded-full border px-6 py-2 font-bold text-sm uppercase tracking-wide transition-colors ${
                filtro === tipo
                  ? 'border-primary-fixed bg-primary-fixed text-on-primary-fixed'
                  : 'border-outline-variant bg-transparent text-on-surface hover:border-primary-fixed hover:text-primary-fixed'
              }`}
            >
              {tipo === 'todas' ? 'Todas' : tipo}
            </button>
          ))}
        </div>
      </div>

      {error && <p className="text-error mb-6">{error}</p>}
      {cargando && <p className="text-on-surface-variant">Cargando clases…</p>}
      {!cargando && clasesFiltradas.length === 0 && <p className="text-on-surface-variant">No hay clases disponibles.</p>}

      {grupos.map((grupo) => (
        <div key={grupo.titulo} className="mb-10 md:mb-14">
          <h3 className="font-display text-xl md:text-2xl text-primary-fixed uppercase tracking-wide mb-4">
            {grupo.titulo}
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 md:gap-8">
            {grupo.clases.map((clase) => {
              const miReserva = reservaPorClase.get(clase.id)
              const agotada = clase.plazas_disponibles <= 0
              const esPasada = new Date(clase.fecha_hora) < new Date() || clase.estado !== 'activa'
              const horasParaInicio = (new Date(clase.fecha_hora) - new Date()) / 3600000
              const cancelacionBloqueadaPorTiempo =
                miReserva?.estado === 'confirmada' && horasParaInicio < HORAS_LIMITE_CANCELACION_CONFIRMADA

              return (
                <article key={clase.id} className="glass-card rounded-xl overflow-hidden flex flex-col glow-hover transition-all duration-300">
                  <div className="p-6 flex flex-col flex-grow">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <span className="text-xs text-on-surface-variant uppercase tracking-wider block mb-1">{clase.tipo}</span>
                        <h3 className="font-display text-2xl text-primary m-0">{clase.nombre}</h3>
                      </div>
                      <div className="text-right">
                        <span className="block font-display text-2xl text-primary-fixed">{formatearHora(clase.fecha_hora)}</span>
                        <span className="text-xs text-on-surface-variant">
                          {formatearFecha(clase.fecha_hora)} · {clase.duracion_minutos} min
                        </span>
                      </div>
                    </div>

                    <div className="mb-6 mt-auto flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${agotada ? 'bg-error' : 'bg-primary-fixed animate-pulse'}`} />
                      <span className={`text-xs uppercase tracking-wider ${agotada ? 'text-error' : 'text-primary-fixed'}`}>
                        {agotada ? 'Agotado' : `${clase.plazas_disponibles} plazas libres`}
                      </span>
                      {clase.en_lista_espera > 0 && (
                        <span className="text-xs text-on-surface-variant">· {clase.en_lista_espera} en espera</span>
                      )}
                    </div>

                    {miReserva && esPasada ? (
                      <button disabled className="w-full bg-surface-variant text-on-surface-variant font-display font-bold py-4 rounded-lg uppercase tracking-wider cursor-not-allowed">
                        Finalizada
                      </button>
                    ) : miReserva ? (
                      <button
                        onClick={() => cancelar(miReserva.id)}
                        disabled={accionPendiente === miReserva.id || cancelacionBloqueadaPorTiempo}
                        title={
                          cancelacionBloqueadaPorTiempo
                            ? `No se puede cancelar una reserva confirmada con menos de ${HORAS_LIMITE_CANCELACION_CONFIRMADA}h de antelación`
                            : undefined
                        }
                        className="w-full border border-error text-error font-display font-bold py-4 rounded-lg uppercase tracking-wider hover:bg-error hover:text-on-error transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                      >
                        {accionPendiente === miReserva.id
                          ? 'Cancelando…'
                          : cancelacionBloqueadaPorTiempo
                            ? 'Reservada · No cancelable (<1h)'
                            : miReserva.estado === 'lista_espera'
                              ? 'En lista de espera · Cancelar'
                              : 'Reservada · Cancelar'}
                      </button>
                    ) : esPasada ? (
                      <button disabled className="w-full bg-surface-variant text-on-surface-variant font-display font-bold py-4 rounded-lg uppercase tracking-wider cursor-not-allowed">
                        Finalizada
                      </button>
                    ) : (
                      <button
                        onClick={() => reservar(clase.id)}
                        disabled={accionPendiente === clase.id}
                        className="w-full bg-primary-fixed text-on-primary-fixed font-display font-bold py-4 rounded-lg uppercase tracking-wider hover:scale-[1.02] active:scale-95 transition-transform disabled:opacity-60"
                      >
                        {accionPendiente === clase.id ? 'Reservando…' : agotada ? 'Lista de Espera' : 'Reservar'}
                      </button>
                    )}
                  </div>
                </article>
              )
            })}
          </div>
        </div>
      ))}
    </div>
  )
}
