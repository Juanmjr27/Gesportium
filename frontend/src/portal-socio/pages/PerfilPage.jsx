import { useEffect, useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import * as sociosService from '../services/sociosService'
import * as membresiasService from '../services/membresiasService'
import * as planesService from '../services/planesService'
import * as accesosService from '../services/accesosService'

const CAMPOS_EDITABLES = ['telefono', 'direccion', 'contacto_emergencia_nombre', 'contacto_emergencia_telefono']

const CAMPO_LABEL = {
  telefono: 'Teléfono',
  direccion: 'Dirección',
  contacto_emergencia_nombre: 'Contacto de emergencia',
  contacto_emergencia_telefono: 'Teléfono de emergencia',
}

function formatearFechaHora(fechaIso) {
  return new Date(fechaIso).toLocaleString('es-ES', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })
}

export default function PerfilPage() {
  const { usuario, socio, cerrarSesion } = useAuth()
  const [form, setForm] = useState(null)
  const [guardando, setGuardando] = useState(false)
  const [mensaje, setMensaje] = useState(null)
  const [error, setError] = useState(null)

  const [membresia, setMembresia] = useState(null)
  const [plan, setPlan] = useState(null)
  const [accesos, setAccesos] = useState([])
  const [accionMembresia, setAccionMembresia] = useState(false)

  useEffect(() => {
    if (!socio) return
    setForm({
      telefono: socio.telefono,
      direccion: socio.direccion,
      contacto_emergencia_nombre: socio.contacto_emergencia_nombre,
      contacto_emergencia_telefono: socio.contacto_emergencia_telefono,
    })

    Promise.all([membresiasService.listarMisMembresias(), planesService.listarPlanesPublico().catch(() => []), accesosService.listarAccesos(socio.id)])
      .then(([membresias, planes, accesosData]) => {
        const activa = membresias.find((m) => m.estado !== 'cancelada') ?? null
        setMembresia(activa)
        setPlan(activa ? planes.find((p) => p.id === activa.plan_id) ?? null : null)
        setAccesos(accesosData.slice(0, 10))
      })
      .catch(() => {})
  }, [socio])

  if (!socio || !form) {
    return <p className="py-16 text-on-surface-variant">Cargando perfil…</p>
  }

  async function handleGuardar(event) {
    event.preventDefault()
    setGuardando(true)
    setMensaje(null)
    setError(null)
    try {
      await sociosService.actualizarSocio(socio.id, form)
      setMensaje('Datos actualizados correctamente.')
    } catch {
      setError('No se pudieron guardar los cambios.')
    } finally {
      setGuardando(false)
    }
  }

  async function handleCongelar() {
    if (!membresia) return
    setAccionMembresia(true)
    setError(null)
    try {
      const actualizada = await membresiasService.congelarMembresia(membresia.id, 'Solicitud desde el portal de socio')
      setMembresia(actualizada)
      setMensaje('Membresía congelada.')
    } catch {
      setError('No se pudo congelar la membresía.')
    } finally {
      setAccionMembresia(false)
    }
  }

  async function handleReactivar() {
    if (!membresia) return
    setAccionMembresia(true)
    setError(null)
    try {
      const actualizada = await membresiasService.reactivarMembresia(membresia.id)
      setMembresia(actualizada)
      setMensaje('Membresía reactivada.')
    } catch {
      setError('No se pudo reactivar la membresía.')
    } finally {
      setAccionMembresia(false)
    }
  }

  async function handleCancelar() {
    if (!membresia) return
    if (!window.confirm('¿Seguro que quieres solicitar la cancelación de tu membresía?')) return
    setAccionMembresia(true)
    setError(null)
    try {
      const actualizada = await membresiasService.cancelarMembresia(membresia.id, 'Solicitud desde el portal de socio')
      setMembresia(actualizada)
      setMensaje('Cancelación registrada.')
    } catch {
      setError('No se pudo cancelar la membresía.')
    } finally {
      setAccionMembresia(false)
    }
  }

  return (
    <div className="py-8 md:py-16">
      <div className="mb-8 md:mb-12 text-center md:text-left">
        <h1 className="font-display text-4xl md:text-6xl text-primary-fixed mb-2">Mi Perfil</h1>
        <p className="text-on-surface-variant">Gestiona tu información personal y membresía.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-4 flex flex-col gap-6">
          <div className="glass-card rounded-xl p-6 flex flex-col items-center text-center">
            <div className="w-24 h-24 mb-4 rounded-full bg-surface-container-high border-2 border-primary-fixed flex items-center justify-center">
              <span className="material-symbols-outlined text-primary-fixed text-4xl">person</span>
            </div>
            <h2 className="font-display text-xl text-tertiary mb-1 break-all">{usuario?.email}</h2>
            {plan && (
              <span className="inline-block px-3 py-1 rounded-full border border-primary-fixed text-primary-fixed text-xs mb-2">
                {plan.nombre}
              </span>
            )}
            <p className="text-on-surface-variant text-sm">Socio desde {socio.fecha_alta}</p>
            <button onClick={cerrarSesion} className="mt-4 text-xs text-on-surface-variant hover:text-error transition-colors uppercase">
              Cerrar sesión
            </button>
          </div>

          {membresia && (
            <div className="glass-card rounded-xl p-6">
              <h3 className="font-display text-lg text-tertiary mb-4">Mi Membresía</h3>
              <p className="text-on-surface-variant mb-1">
                Estado: <span className="text-primary-fixed font-bold capitalize">{membresia.estado}</span>
              </p>
              {membresia.estado === 'activa' && (
                <p className="text-on-surface-variant text-sm mb-4">Renueva el {membresia.fecha_proxima_renovacion}</p>
              )}
              <div className="flex flex-col gap-2 mt-4">
                {membresia.estado === 'activa' && (
                  <button
                    onClick={handleCongelar}
                    disabled={accionMembresia}
                    className="w-full border border-outline-variant text-on-surface py-2 rounded uppercase text-sm font-bold hover:border-primary-fixed hover:text-primary-fixed transition-colors disabled:opacity-60"
                  >
                    Congelar membresía
                  </button>
                )}
                {membresia.estado === 'congelada' && (
                  <button
                    onClick={handleReactivar}
                    disabled={accionMembresia}
                    className="w-full bg-primary-fixed text-on-primary-fixed py-2 rounded uppercase text-sm font-bold hover:scale-[1.02] transition-transform disabled:opacity-60"
                  >
                    Reactivar membresía
                  </button>
                )}
                {membresia.estado !== 'cancelada' && (
                  <button
                    onClick={handleCancelar}
                    disabled={accionMembresia}
                    className="w-full border border-error text-error py-2 rounded uppercase text-sm font-bold hover:bg-error hover:text-on-error transition-colors disabled:opacity-60"
                  >
                    Solicitar cancelación
                  </button>
                )}
              </div>
            </div>
          )}

          {accesos.length > 0 && (
            <div className="glass-card rounded-xl p-6">
              <h3 className="font-display text-lg text-tertiary mb-4">Últimos accesos</h3>
              <ul className="flex flex-col gap-2">
                {accesos.map((acceso) => (
                  <li key={acceso.id} className="flex justify-between text-sm border-b border-white/5 pb-2 last:border-none">
                    <span className="text-on-surface-variant capitalize">{acceso.tipo}</span>
                    <span className="text-on-surface">{formatearFechaHora(acceso.fecha_hora)}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <div className="lg:col-span-8">
          <form onSubmit={handleGuardar} className="glass-card rounded-xl p-6 md:p-8">
            <h3 className="font-display text-xl text-tertiary mb-6 border-b border-white/10 pb-4">Información Personal</h3>

            {mensaje && <p className="text-primary-fixed mb-4">{mensaje}</p>}
            {error && <p className="text-error mb-4">{error}</p>}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
              {CAMPOS_EDITABLES.map((campo) => (
                <div key={campo} className="flex flex-col">
                  <label className="text-xs text-on-surface-variant mb-2 uppercase tracking-wider" htmlFor={campo}>
                    {CAMPO_LABEL[campo]}
                  </label>
                  <input
                    id={campo}
                    type="text"
                    value={form[campo] ?? ''}
                    onChange={(e) => setForm((prev) => ({ ...prev, [campo]: e.target.value }))}
                    className="bg-surface-container border-0 border-b-2 border-white/10 text-tertiary px-4 py-3 focus:ring-0 focus:outline-none input-energetic transition-colors rounded-t-lg"
                  />
                </div>
              ))}
            </div>

            <div className="flex justify-end pt-4 border-t border-white/10">
              <button
                type="submit"
                disabled={guardando}
                className="bg-primary-fixed text-on-primary font-display uppercase py-3 px-8 rounded-lg hover:scale-[1.02] active:scale-95 transition-all font-bold disabled:opacity-60"
              >
                {guardando ? 'Guardando…' : 'Guardar Cambios'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
