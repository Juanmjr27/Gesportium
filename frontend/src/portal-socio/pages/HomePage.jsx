import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { listarMisMembresias } from '../services/membresiasService'
import { listarPlanesPublico } from '../services/planesService'
import { listarMisReservas } from '../services/clasesService'
import { listarRutinas, listarPlanesNutricionales } from '../services/entrenamientoService'

const ESTADO_LABEL = {
  activa: 'Activa',
  congelada: 'Congelada',
  cancelada: 'Cancelada',
}

export default function HomePage() {
  const { usuario, socio, socioPendienteDeAlta } = useAuth()
  const [membresia, setMembresia] = useState(null)
  const [plan, setPlan] = useState(null)
  const [reservas, setReservas] = useState([])
  const [rutinasActivas, setRutinasActivas] = useState(0)
  const [planesActivos, setPlanesActivos] = useState(0)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!socio) {
      setCargando(false)
      return
    }

    let cancelado = false
    setCargando(true)
    setError(null)

    Promise.all([
      listarMisMembresias(),
      listarPlanesPublico().catch(() => []),
      listarMisReservas(),
      listarRutinas(socio.id).catch(() => []),
      listarPlanesNutricionales(socio.id).catch(() => []),
    ])
      .then(([membresias, planes, misReservas, rutinas, planesNutricionales]) => {
        if (cancelado) return
        const activa = membresias.find((m) => m.estado === 'activa') ?? membresias[0] ?? null
        setMembresia(activa)
        setPlan(activa ? planes.find((p) => p.id === activa.plan_id) ?? null : null)
        setReservas(misReservas)
        setRutinasActivas(rutinas.filter((r) => r.activa).length)
        setPlanesActivos(planesNutricionales.filter((p) => p.activo).length)
      })
      .catch(() => !cancelado && setError('No se pudo cargar tu información. Inténtalo de nuevo más tarde.'))
      .finally(() => !cancelado && setCargando(false))

    return () => {
      cancelado = true
    }
  }, [socio])

  const nombre = usuario?.email?.split('@')[0] ?? 'socio'

  if (socioPendienteDeAlta) {
    return (
      <div className="py-16 max-w-xl mx-auto text-center">
        <h1 className="font-display text-3xl uppercase text-primary mb-4">¡Bienvenido, {nombre}!</h1>
        <div className="glass-card rounded-xl p-6">
          <span className="material-symbols-outlined text-primary-fixed text-4xl mb-2">hourglass_top</span>
          <p className="text-on-surface-variant">
            Tu cuenta se ha creado correctamente. Un gestor de tu sede debe completar tu alta como socio antes de que
            puedas acceder a clases, membresía y entrenamiento.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="py-8 md:py-16 flex flex-col gap-6">
      <div>
        <h1 className="font-display text-4xl md:text-6xl text-primary mb-2 uppercase italic tracking-tighter">
          ¡Hola, {nombre}!
        </h1>
        <p className="text-lg text-on-surface-variant">Listo para destrozar tus límites hoy.</p>
      </div>

      {error && <p className="text-error">{error}</p>}

      {!cargando && membresia && (
        <div className="glass-card rounded-xl p-6 relative overflow-hidden">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="material-symbols-outlined text-primary-fixed" style={{ fontVariationSettings: "'FILL' 1" }}>
                  workspace_premium
                </span>
                <h2 className="font-display text-2xl text-primary uppercase">{plan?.nombre ?? 'Membresía'}</h2>
              </div>
              <p className="text-on-surface-variant">
                Estado: <strong className="text-primary-fixed">{ESTADO_LABEL[membresia.estado] ?? membresia.estado}</strong>
                {membresia.estado === 'activa' && (
                  <>
                    {' '}
                    · Renueva el <strong className="text-primary-fixed">{membresia.fecha_proxima_renovacion}</strong>
                  </>
                )}
              </p>
            </div>
            <Link
              to="/perfil"
              className="bg-primary-fixed text-on-primary-fixed font-display font-bold uppercase px-6 py-3 rounded hover:scale-105 transition-transform"
            >
              Ver Detalles
            </Link>
          </div>
        </div>
      )}

      {!cargando && !membresia && (
        <div className="glass-card rounded-xl p-6 text-on-surface-variant">
          Todavía no tienes ninguna membresía asociada. Habla con tu sede para darte de alta.
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Link
          to="/clases"
          className="glass-card rounded-xl p-6 glow-hover flex flex-col justify-between min-h-[200px] transition-all duration-300"
        >
          <div>
            <span className="material-symbols-outlined text-primary-fixed text-4xl mb-4" style={{ fontVariationSettings: "'FILL' 1" }}>
              event_available
            </span>
            <h3 className="font-display text-2xl text-primary uppercase">Reservar Clase</h3>
            <p className="text-on-surface-variant mt-2">
              {reservas.length > 0 ? `Tienes ${reservas.length} reserva(s) activas.` : 'Explora el catálogo de clases.'}
            </p>
          </div>
          <div className="mt-4 flex justify-end">
            <span className="material-symbols-outlined text-primary-fixed">arrow_forward</span>
          </div>
        </Link>

        <Link
          to="/entrenamiento"
          className="glass-card rounded-xl p-6 glow-hover flex flex-col justify-between min-h-[200px] transition-all duration-300"
        >
          <div>
            <span className="material-symbols-outlined text-primary-fixed text-4xl mb-4" style={{ fontVariationSettings: "'FILL' 1" }}>
              fitness_center
            </span>
            <h3 className="font-display text-2xl text-primary uppercase">Mi Entrenamiento</h3>
            <p className="text-on-surface-variant mt-2">
              {rutinasActivas} rutina(s) activa(s) · {planesActivos} plan(es) nutricional(es)
            </p>
          </div>
          <div className="mt-4 flex justify-end">
            <span className="material-symbols-outlined text-primary-fixed">arrow_forward</span>
          </div>
        </Link>
      </div>

      <div className="mt-4">
        <h4 className="font-display text-2xl text-primary uppercase mb-6 border-b border-white/5 pb-2">Tu resumen</h4>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div className="glass-card rounded-lg p-4 flex flex-col items-center justify-center text-center">
            <span className="font-display text-3xl text-primary-fixed">{reservas.length}</span>
            <span className="text-xs text-on-surface-variant uppercase mt-1">Reservas activas</span>
          </div>
          <div className="glass-card rounded-lg p-4 flex flex-col items-center justify-center text-center">
            <span className="font-display text-3xl text-primary-fixed">{rutinasActivas}</span>
            <span className="text-xs text-on-surface-variant uppercase mt-1">Rutinas activas</span>
          </div>
          <div className="glass-card rounded-lg p-4 flex flex-col items-center justify-center text-center">
            <span className="font-display text-3xl text-primary-fixed">{planesActivos}</span>
            <span className="text-xs text-on-surface-variant uppercase mt-1">Planes nutricionales</span>
          </div>
        </div>
      </div>
    </div>
  )
}
