import { useEffect, useMemo, useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import * as entrenamientoService from '../services/entrenamientoService'

const DIAS = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
const DIAS_LABEL = {
  lunes: 'Lunes',
  martes: 'Martes',
  miercoles: 'Miércoles',
  jueves: 'Jueves',
  viernes: 'Viernes',
  sabado: 'Sábado',
  domingo: 'Domingo',
}

function diaDeHoy() {
  // getDay(): 0=domingo..6=sábado
  return DIAS[(new Date().getDay() + 6) % 7]
}

export default function EntrenamientoPage() {
  const { socio } = useAuth()
  const [rutinas, setRutinas] = useState([])
  const [planes, setPlanes] = useState([])
  const [diaSeleccionado, setDiaSeleccionado] = useState(diaDeHoy())
  const [completados, setCompletados] = useState(new Set())
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState(null)
  const [enviando, setEnviando] = useState(null)

  useEffect(() => {
    if (!socio) return
    setCargando(true)
    Promise.all([entrenamientoService.listarRutinas(socio.id), entrenamientoService.listarPlanesNutricionales(socio.id)])
      .then(([rutinasData, planesData]) => {
        setRutinas(rutinasData.filter((r) => r.activa))
        setPlanes(planesData)
      })
      .catch(() => setError('No se pudo cargar tu entrenamiento.'))
      .finally(() => setCargando(false))
  }, [socio])

  const ejerciciosDelDia = useMemo(() => {
    return rutinas.flatMap((rutina) =>
      rutina.ejercicios.filter((ej) => ej.dia_semana === diaSeleccionado).map((ej) => ({ ...ej, rutinaId: rutina.id, rutinaNombre: rutina.nombre })),
    )
  }, [rutinas, diaSeleccionado])

  const progreso = ejerciciosDelDia.length === 0 ? 0 : Math.round((completados.size / ejerciciosDelDia.length) * 100)

  async function toggleEjercicio(ejercicio) {
    const yaCompletado = completados.has(ejercicio.id)
    setEnviando(ejercicio.id)
    try {
      await entrenamientoService.completarEjercicio(ejercicio.rutinaId, ejercicio.id, !yaCompletado)
      setCompletados((prev) => {
        const siguiente = new Set(prev)
        if (yaCompletado) siguiente.delete(ejercicio.id)
        else siguiente.add(ejercicio.id)
        return siguiente
      })
    } catch {
      setError('No se pudo registrar el ejercicio.')
    } finally {
      setEnviando(null)
    }
  }

  return (
    <div className="py-8 flex flex-col gap-10">
      <section className="flex flex-col gap-2 mt-4 relative">
        <p className="text-primary-fixed uppercase tracking-widest text-xs font-bold">Mi plan semanal</p>
        <h2 className="font-display text-4xl md:text-6xl text-on-surface uppercase tracking-tighter">Mi Entrenamiento</h2>

        <div className="flex gap-2 mt-4 overflow-x-auto pb-2">
          {DIAS.map((dia) => (
            <button
              key={dia}
              onClick={() => setDiaSeleccionado(dia)}
              className={`shrink-0 rounded-full border px-4 py-2 text-sm font-bold uppercase transition-colors ${
                diaSeleccionado === dia
                  ? 'border-primary-fixed bg-primary-fixed text-on-primary-fixed'
                  : 'border-outline-variant text-on-surface-variant hover:border-primary-fixed hover:text-primary-fixed'
              }`}
            >
              {DIAS_LABEL[dia]}
            </button>
          ))}
        </div>

        <div className="mt-4 flex flex-col gap-1 w-full max-w-md">
          <div className="flex justify-between items-center">
            <span className="text-sm text-on-surface-variant">Progreso del día</span>
            <span className="font-bold text-primary-fixed">{progreso}%</span>
          </div>
          <div className="h-1 bg-surface-container-high rounded-full overflow-hidden">
            <div className="h-full bg-primary-fixed transition-all duration-500 ease-out" style={{ width: `${progreso}%` }} />
          </div>
        </div>
      </section>

      {error && <p className="text-error">{error}</p>}

      <section className="flex flex-col gap-4">
        <h3 className="font-display text-2xl text-on-surface flex items-center gap-2">
          <span className="material-symbols-outlined text-primary-fixed">list_alt</span>
          Ejercicios
        </h3>

        {cargando && <p className="text-on-surface-variant">Cargando…</p>}
        {!cargando && ejerciciosDelDia.length === 0 && (
          <p className="text-on-surface-variant">No tienes ejercicios asignados para {DIAS_LABEL[diaSeleccionado].toLowerCase()}.</p>
        )}

        <div className="flex flex-col gap-4">
          {ejerciciosDelDia.map((ejercicio) => {
            const marcado = completados.has(ejercicio.id)
            return (
              <article
                key={ejercicio.id}
                className="glass-card rounded-xl p-4 md:p-6 flex flex-col md:flex-row gap-4 justify-between items-start md:items-center transition-all duration-300"
              >
                <div className="flex-1 flex flex-col gap-2 w-full">
                  <span className="inline-block w-fit px-2 py-1 border border-primary-fixed text-primary-fixed text-xs rounded-full">
                    {ejercicio.rutinaNombre}
                  </span>
                  <h4 className="font-display text-xl text-on-surface uppercase leading-none">{ejercicio.nombre}</h4>
                  <div className="grid grid-cols-3 gap-2 mt-2 bg-surface-container-highest/50 rounded-lg p-2">
                    <div className="flex flex-col items-center p-1">
                      <span className="text-xs text-on-surface-variant">Sets</span>
                      <span className="font-bold text-on-surface">{ejercicio.series}</span>
                    </div>
                    <div className="flex flex-col items-center p-1 border-x border-white/5">
                      <span className="text-xs text-on-surface-variant">Reps</span>
                      <span className="font-bold text-on-surface">{ejercicio.repeticiones}</span>
                    </div>
                    <div className="flex flex-col items-center p-1">
                      <span className="text-xs text-on-surface-variant">Descanso</span>
                      <span className="font-bold text-on-surface">{ejercicio.descanso_segundos}s</span>
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => toggleEjercicio(ejercicio)}
                  disabled={enviando === ejercicio.id}
                  className="flex items-center justify-center p-2 hover:scale-110 transition-transform disabled:opacity-60"
                  aria-label={marcado ? 'Marcar como no completado' : 'Marcar como completado'}
                >
                  <div
                    className={`w-10 h-10 rounded-full border-2 flex items-center justify-center transition-colors ${
                      marcado ? 'bg-primary-fixed border-primary-fixed' : 'border-on-surface-variant'
                    }`}
                  >
                    {marcado && (
                      <span className="material-symbols-outlined text-on-primary-fixed" style={{ fontVariationSettings: "'FILL' 1" }}>
                        check
                      </span>
                    )}
                  </div>
                </button>
              </article>
            )
          })}
        </div>
      </section>

      <hr className="border-t border-white/5" />

      <section className="flex flex-col gap-4">
        <h3 className="font-display text-2xl text-on-surface flex items-center gap-2">
          <span className="material-symbols-outlined text-primary-fixed">restaurant</span>
          Plan Nutricional
        </h3>

        {!cargando && planes.length === 0 && <p className="text-on-surface-variant">No tienes planes nutricionales asignados.</p>}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {planes
            .filter((p) => p.activo)
            .map((plan) => (
              <div key={plan.id} className="glass-card rounded-xl p-4 md:p-6 flex flex-col gap-2">
                <h4 className="font-bold text-on-surface">{plan.nombre}</h4>
                {plan.notas && <p className="text-on-surface-variant text-sm">{plan.notas}</p>}
              </div>
            ))}
        </div>
      </section>
    </div>
  )
}
