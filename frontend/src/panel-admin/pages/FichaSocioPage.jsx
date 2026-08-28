import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import * as sociosService from '../services/sociosService'
import * as sedesService from '../services/sedesService'
import * as membresiasService from '../services/membresiasService'
import * as entrenamientoService from '../services/entrenamientoService'
import StatusPill from '../components/StatusPill'
import Modal from '../components/Modal'
import Button from '../components/Button'
import Field, { TextInput, TextareaInput, SelectInput } from '../components/Field'

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

const ESTADO_MEMBRESIA_VARIANT = {
  activa: 'success',
  congelada: 'warning',
  cancelada: 'error',
  vencida: 'neutral',
}

const EJERCICIO_VACIO = { nombre: '', series: 3, repeticiones: 10, dia_semana: 'lunes', descanso_segundos: 60 }

export default function FichaSocioPage() {
  const { socioId } = useParams()
  const navigate = useNavigate()
  const { usuario } = useAuth()
  const puedeGestionarEntrenamiento = usuario.rol === 'entrenador'

  const [ficha, setFicha] = useState(null)
  const [sedes, setSedes] = useState([])
  const [planesMembresia, setPlanesMembresia] = useState([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState(null)

  const [modalRutina, setModalRutina] = useState(null) // null | 'nueva' | rutina a editar
  const [formRutina, setFormRutina] = useState({ nombre: '', ejercicios: [{ ...EJERCICIO_VACIO }] })
  const [formEditarRutina, setFormEditarRutina] = useState({ nombre: '', activa: true })

  const [modalPlan, setModalPlan] = useState(null) // null | 'nuevo' | plan a editar
  const [formPlan, setFormPlan] = useState({ nombre: '', notas: '' })
  const [formEditarPlan, setFormEditarPlan] = useState({ nombre: '', notas: '', activo: true })

  function cargarFicha() {
    return sociosService
      .obtenerFichaSocio(socioId)
      .then(setFicha)
      .catch(() => setError('No se pudo cargar la ficha de este socio.'))
  }

  useEffect(() => {
    setCargando(true)
    setFicha(null)
    setError(null)
    Promise.all([cargarFicha(), sedesService.listarSedes().catch(() => []), membresiasService.listarPlanes().catch(() => [])]).then(
      ([, sedesData, planesData]) => {
        if (sedesData) setSedes(sedesData)
        if (planesData) setPlanesMembresia(planesData)
        setCargando(false)
      },
    )
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [socioId])

  const sedeNombre = useMemo(() => {
    const map = new Map(sedes.map((s) => [s.id, s.nombre]))
    return (id) => map.get(id) ?? id
  }, [sedes])

  const planMembresiaNombre = useMemo(() => {
    const map = new Map(planesMembresia.map((p) => [p.id, p.nombre]))
    return (id) => map.get(id) ?? id
  }, [planesMembresia])

  function abrirNuevaRutina() {
    setFormRutina({ nombre: '', ejercicios: [{ ...EJERCICIO_VACIO }] })
    setModalRutina('nueva')
  }

  function abrirEditarRutina(rutina) {
    setFormEditarRutina({ nombre: rutina.nombre, activa: rutina.activa })
    setModalRutina(rutina)
  }

  function actualizarEjercicio(index, campo, valor) {
    setFormRutina((prev) => {
      const ejercicios = [...prev.ejercicios]
      ejercicios[index] = { ...ejercicios[index], [campo]: valor }
      return { ...prev, ejercicios }
    })
  }

  function anadirEjercicio() {
    setFormRutina((prev) => ({ ...prev, ejercicios: [...prev.ejercicios, { ...EJERCICIO_VACIO }] }))
  }

  function quitarEjercicio(index) {
    setFormRutina((prev) => ({ ...prev, ejercicios: prev.ejercicios.filter((_, i) => i !== index) }))
  }

  async function handleCrearRutina(event) {
    event.preventDefault()
    try {
      await entrenamientoService.crearRutina({
        socio_id: socioId,
        nombre: formRutina.nombre,
        ejercicios: formRutina.ejercicios.map((e) => ({
          ...e,
          series: Number(e.series),
          repeticiones: Number(e.repeticiones),
          descanso_segundos: Number(e.descanso_segundos),
        })),
      })
      setModalRutina(null)
      cargarFicha()
    } catch {
      setError('No se pudo crear la rutina.')
    }
  }

  async function handleEditarRutina(event) {
    event.preventDefault()
    try {
      await entrenamientoService.editarRutina(modalRutina.id, formEditarRutina)
      setModalRutina(null)
      cargarFicha()
    } catch {
      setError('No se pudo actualizar la rutina.')
    }
  }

  function abrirNuevoPlan() {
    setFormPlan({ nombre: '', notas: '' })
    setModalPlan('nuevo')
  }

  function abrirEditarPlan(plan) {
    setFormEditarPlan({ nombre: plan.nombre, notas: plan.notas ?? '', activo: plan.activo })
    setModalPlan(plan)
  }

  async function handleCrearPlan(event) {
    event.preventDefault()
    try {
      await entrenamientoService.crearPlanNutricional({ socio_id: socioId, nombre: formPlan.nombre, notas: formPlan.notas || null })
      setModalPlan(null)
      cargarFicha()
    } catch {
      setError('No se pudo crear el plan nutricional.')
    }
  }

  async function handleEditarPlan(event) {
    event.preventDefault()
    try {
      await entrenamientoService.editarPlanNutricional(modalPlan.id, {
        ...formEditarPlan,
        notas: formEditarPlan.notas || null,
      })
      setModalPlan(null)
      cargarFicha()
    } catch {
      setError('No se pudo actualizar el plan nutricional.')
    }
  }

  return (
    <div className="flex flex-col gap-gp-lg">
      <div className="flex items-center gap-gp-md">
        <button
          onClick={() => navigate('/admin/socios')}
          aria-label="Volver a Socios"
          className="w-9 h-9 flex items-center justify-center rounded-full text-on-surface-variant hover:bg-surface-container-highest transition-colors"
        >
          <span className="material-symbols-outlined">arrow_back</span>
        </button>
        <div>
          <h1 className="text-headline-xl text-on-background">Ficha de socio</h1>
          <p className="text-body-lg text-on-surface-variant mt-1">Datos, membresía, entrenador y entrenamiento del socio.</p>
        </div>
      </div>

      {error && <p className="text-error">{error}</p>}
      {cargando && <p className="text-on-surface-variant">Cargando…</p>}

      {!cargando && ficha && (
        <>
          <section className="bg-surface-container-lowest border border-outline-variant rounded-xl p-gp-md shadow-sm">
            <h2 className="text-headline-md text-on-surface mb-gp-md">Datos personales</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-gp-md">
              <Dato label="Sede" valor={sedeNombre(ficha.sede_id)} />
              <div>
                <p className="text-label-sm text-on-surface-variant uppercase">Estado</p>
                <StatusPill variant={ficha.activo ? 'success' : 'neutral'}>{ficha.activo ? 'Activo' : 'Inactivo'}</StatusPill>
              </div>
              <Dato label="Fecha de alta" valor={ficha.fecha_alta} />
              <Dato label="Fecha de nacimiento" valor={ficha.fecha_nacimiento} />
              <Dato label="Teléfono" valor={ficha.telefono} />
              <Dato label="Dirección" valor={ficha.direccion} />
              <Dato label="Contacto de emergencia" valor={ficha.contacto_emergencia_nombre} />
              <Dato label="Teléfono de emergencia" valor={ficha.contacto_emergencia_telefono} />
            </div>
          </section>

          <section className="bg-surface-container-lowest border border-outline-variant rounded-xl p-gp-md shadow-sm">
            <h2 className="text-headline-md text-on-surface mb-gp-md">Membresía</h2>
            {!ficha.membresia && <p className="text-on-surface-variant text-body-md">Sin membresía registrada.</p>}
            {ficha.membresia && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-gp-md">
                <Dato label="Plan" valor={planMembresiaNombre(ficha.membresia.plan_id)} />
                <div>
                  <p className="text-label-sm text-on-surface-variant uppercase">Estado</p>
                  <StatusPill variant={ESTADO_MEMBRESIA_VARIANT[ficha.membresia.estado] ?? 'neutral'}>{ficha.membresia.estado}</StatusPill>
                </div>
                <Dato label="Próxima renovación" valor={ficha.membresia.fecha_proxima_renovacion} />
              </div>
            )}
          </section>

          <section className="bg-surface-container-lowest border border-outline-variant rounded-xl p-gp-md shadow-sm">
            <h2 className="text-headline-md text-on-surface mb-gp-md">Entrenador asignado</h2>
            {!ficha.entrenador_asignado && <p className="text-on-surface-variant text-body-md">Sin entrenador asignado.</p>}
            {ficha.entrenador_asignado && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-gp-md">
                <Dato label="Entrenador" valor={ficha.entrenador_asignado.email} />
                <Dato label="Especialidades" valor={ficha.entrenador_asignado.especialidades.join(', ') || '—'} />
              </div>
            )}
          </section>

          <section className="bg-surface-container-lowest border border-outline-variant rounded-xl p-gp-md shadow-sm">
            <div className="flex justify-between items-center mb-gp-md">
              <h2 className="text-headline-md text-on-surface">Rutinas</h2>
              {puedeGestionarEntrenamiento && (
                <Button icon="add" onClick={abrirNuevaRutina}>
                  Nueva rutina
                </Button>
              )}
            </div>
            {ficha.rutinas.length === 0 && <p className="text-on-surface-variant text-body-md">Sin rutinas registradas.</p>}
            <div className="flex flex-col gap-gp-md">
              {ficha.rutinas.map((rutina) => (
                <div key={rutina.id} className="border border-outline-variant/60 rounded-lg p-gp-sm">
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-2">
                      <span className="text-body-md font-bold text-on-surface">{rutina.nombre}</span>
                      <StatusPill variant={rutina.activa ? 'success' : 'neutral'}>{rutina.activa ? 'Activa' : 'Archivada'}</StatusPill>
                    </div>
                    {puedeGestionarEntrenamiento && (
                      <button onClick={() => abrirEditarRutina(rutina)} className="text-primary hover:underline text-xs">
                        Editar
                      </button>
                    )}
                  </div>
                  <ul className="mt-2 flex flex-col gap-1">
                    {rutina.ejercicios.map((ej) => (
                      <li key={ej.id} className="text-body-md text-on-surface-variant">
                        {DIAS_LABEL[ej.dia_semana]} · {ej.nombre} · {ej.series}x{ej.repeticiones} · descanso {ej.descanso_segundos}s
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </section>

          <section className="bg-surface-container-lowest border border-outline-variant rounded-xl p-gp-md shadow-sm">
            <div className="flex justify-between items-center mb-gp-md">
              <h2 className="text-headline-md text-on-surface">Planes nutricionales</h2>
              {puedeGestionarEntrenamiento && (
                <Button icon="add" onClick={abrirNuevoPlan}>
                  Nuevo plan
                </Button>
              )}
            </div>
            {ficha.planes_nutricionales.length === 0 && <p className="text-on-surface-variant text-body-md">Sin planes nutricionales registrados.</p>}
            <div className="flex flex-col gap-gp-md">
              {ficha.planes_nutricionales.map((plan) => (
                <div key={plan.id} className="border border-outline-variant/60 rounded-lg p-gp-sm">
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-2">
                      <span className="text-body-md font-bold text-on-surface">{plan.nombre}</span>
                      <StatusPill variant={plan.activo ? 'success' : 'neutral'}>{plan.activo ? 'Activo' : 'Archivado'}</StatusPill>
                    </div>
                    {puedeGestionarEntrenamiento && (
                      <button onClick={() => abrirEditarPlan(plan)} className="text-primary hover:underline text-xs">
                        Editar
                      </button>
                    )}
                  </div>
                  {plan.notas && <p className="mt-2 text-body-md text-on-surface-variant">{plan.notas}</p>}
                </div>
              ))}
            </div>
          </section>
        </>
      )}

      {modalRutina === 'nueva' && (
        <Modal title="Nueva rutina" onClose={() => setModalRutina(null)}>
          <form onSubmit={handleCrearRutina}>
            <Field label="Nombre" htmlFor="rutina-nombre">
              <TextInput
                id="rutina-nombre"
                required
                value={formRutina.nombre}
                onChange={(e) => setFormRutina({ ...formRutina, nombre: e.target.value })}
              />
            </Field>
            <p className="text-label-sm text-on-surface-variant uppercase mb-2">Ejercicios</p>
            {formRutina.ejercicios.map((ej, index) => (
              <div key={index} className="border border-outline-variant/60 rounded-lg p-gp-sm mb-gp-sm flex flex-col gap-2">
                <TextInput
                  required
                  placeholder="Nombre del ejercicio"
                  value={ej.nombre}
                  onChange={(e) => actualizarEjercicio(index, 'nombre', e.target.value)}
                />
                <div className="grid grid-cols-2 gap-2">
                  <TextInput
                    type="number"
                    min={1}
                    required
                    placeholder="Series"
                    value={ej.series}
                    onChange={(e) => actualizarEjercicio(index, 'series', e.target.value)}
                  />
                  <TextInput
                    type="number"
                    min={1}
                    required
                    placeholder="Repeticiones"
                    value={ej.repeticiones}
                    onChange={(e) => actualizarEjercicio(index, 'repeticiones', e.target.value)}
                  />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <SelectInput value={ej.dia_semana} onChange={(e) => actualizarEjercicio(index, 'dia_semana', e.target.value)}>
                    {DIAS.map((dia) => (
                      <option key={dia} value={dia}>
                        {DIAS_LABEL[dia]}
                      </option>
                    ))}
                  </SelectInput>
                  <TextInput
                    type="number"
                    min={0}
                    required
                    placeholder="Descanso (s)"
                    value={ej.descanso_segundos}
                    onChange={(e) => actualizarEjercicio(index, 'descanso_segundos', e.target.value)}
                  />
                </div>
                {formRutina.ejercicios.length > 1 && (
                  <button type="button" onClick={() => quitarEjercicio(index)} className="text-error hover:underline text-xs self-start">
                    Quitar ejercicio
                  </button>
                )}
              </div>
            ))}
            <Button type="button" variant="secondary" onClick={anadirEjercicio} className="mb-gp-md">
              Añadir ejercicio
            </Button>
            <div className="flex justify-end gap-2 mt-gp-md">
              <Button type="button" variant="secondary" onClick={() => setModalRutina(null)}>
                Cancelar
              </Button>
              <Button type="submit">Guardar</Button>
            </div>
          </form>
        </Modal>
      )}

      {modalRutina && modalRutina !== 'nueva' && (
        <Modal title="Editar rutina" onClose={() => setModalRutina(null)}>
          <form onSubmit={handleEditarRutina}>
            <Field label="Nombre" htmlFor="editar-rutina-nombre">
              <TextInput
                id="editar-rutina-nombre"
                required
                value={formEditarRutina.nombre}
                onChange={(e) => setFormEditarRutina({ ...formEditarRutina, nombre: e.target.value })}
              />
            </Field>
            <label className="flex items-center gap-2 text-body-md text-on-surface mb-gp-md">
              <input
                type="checkbox"
                checked={formEditarRutina.activa}
                onChange={(e) => setFormEditarRutina({ ...formEditarRutina, activa: e.target.checked })}
              />
              Rutina activa
            </label>
            <div className="flex justify-end gap-2 mt-gp-md">
              <Button type="button" variant="secondary" onClick={() => setModalRutina(null)}>
                Cancelar
              </Button>
              <Button type="submit">Guardar</Button>
            </div>
          </form>
        </Modal>
      )}

      {modalPlan === 'nuevo' && (
        <Modal title="Nuevo plan nutricional" onClose={() => setModalPlan(null)}>
          <form onSubmit={handleCrearPlan}>
            <Field label="Nombre" htmlFor="plan-nombre">
              <TextInput id="plan-nombre" required value={formPlan.nombre} onChange={(e) => setFormPlan({ ...formPlan, nombre: e.target.value })} />
            </Field>
            <Field label="Notas" htmlFor="plan-notas">
              <TextareaInput id="plan-notas" rows={4} value={formPlan.notas} onChange={(e) => setFormPlan({ ...formPlan, notas: e.target.value })} />
            </Field>
            <div className="flex justify-end gap-2 mt-gp-md">
              <Button type="button" variant="secondary" onClick={() => setModalPlan(null)}>
                Cancelar
              </Button>
              <Button type="submit">Guardar</Button>
            </div>
          </form>
        </Modal>
      )}

      {modalPlan && modalPlan !== 'nuevo' && (
        <Modal title="Editar plan nutricional" onClose={() => setModalPlan(null)}>
          <form onSubmit={handleEditarPlan}>
            <Field label="Nombre" htmlFor="editar-plan-nombre">
              <TextInput
                id="editar-plan-nombre"
                required
                value={formEditarPlan.nombre}
                onChange={(e) => setFormEditarPlan({ ...formEditarPlan, nombre: e.target.value })}
              />
            </Field>
            <Field label="Notas" htmlFor="editar-plan-notas">
              <TextareaInput
                id="editar-plan-notas"
                rows={4}
                value={formEditarPlan.notas}
                onChange={(e) => setFormEditarPlan({ ...formEditarPlan, notas: e.target.value })}
              />
            </Field>
            <label className="flex items-center gap-2 text-body-md text-on-surface mb-gp-md">
              <input
                type="checkbox"
                checked={formEditarPlan.activo}
                onChange={(e) => setFormEditarPlan({ ...formEditarPlan, activo: e.target.checked })}
              />
              Plan activo
            </label>
            <div className="flex justify-end gap-2 mt-gp-md">
              <Button type="button" variant="secondary" onClick={() => setModalPlan(null)}>
                Cancelar
              </Button>
              <Button type="submit">Guardar</Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  )
}

function Dato({ label, valor }) {
  return (
    <div>
      <p className="text-label-sm text-on-surface-variant uppercase">{label}</p>
      <p className="text-body-md text-on-surface">{valor}</p>
    </div>
  )
}
