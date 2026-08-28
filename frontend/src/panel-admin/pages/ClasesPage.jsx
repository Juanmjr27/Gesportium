import { useEffect, useMemo, useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import * as clasesService from '../services/clasesService'
import * as sedesService from '../services/sedesService'
import * as entrenadoresService from '../services/entrenadoresService'
import StatusPill from '../components/StatusPill'
import Modal from '../components/Modal'
import Button from '../components/Button'
import Field, { SelectInput, TextInput } from '../components/Field'

const CLASE_VACIA = {
  sede_id: '',
  entrenador_id: '',
  nombre: '',
  tipo: '',
  fecha_hora: '',
  duracion_minutos: 60,
  aforo_maximo: 20,
  recurrente: false,
}

export default function ClasesPage() {
  const { usuario } = useAuth()
  const esGestorSede = usuario.rol === 'gestor_sede'
  const esEntrenador = usuario.rol === 'entrenador'

  const [clases, setClases] = useState([])
  const [sedes, setSedes] = useState([])
  const [entrenadores, setEntrenadores] = useState([])
  const [sedeId, setSedeId] = useState(esGestorSede ? usuario.sede_id : '')
  const [error, setError] = useState(null)
  const [modalAbierto, setModalAbierto] = useState(false)
  const [form, setForm] = useState(CLASE_VACIA)
  const [guardando, setGuardando] = useState(false)

  function cargarClases() {
    clasesService
      .listarClases(sedeId ? { sede_id: sedeId } : undefined)
      .then(setClases)
      .catch(() => setError('No se pudieron cargar las clases.'))
  }

  useEffect(() => {
    cargarClases()
  }, [sedeId])

  useEffect(() => {
    sedesService.listarSedes().then(setSedes).catch(() => {})
    // GET /entrenadores exige rol admin/gestor_sede (entrenadores/router.py) —
    // un entrenador no puede listar el catálogo completo, pero tampoco lo
    // necesita: GET /clases ya le devuelve solo sus propias clases
    // (clases/router.py filtra por entrenador_id), así que no hay nombres
    // ajenos que cruzar.
    if (!esEntrenador) {
      entrenadoresService.listarEntrenadores().then(setEntrenadores).catch(() => {})
    }
  }, [esEntrenador])

  const entrenadorNombre = useMemo(() => {
    const map = new Map(entrenadores.map((e) => [e.id, e.email]))
    return (id) => map.get(id) ?? id
  }, [entrenadores])

  const ordenadas = [...clases].sort((a, b) => new Date(a.fecha_hora) - new Date(b.fecha_hora))

  function abrirAlta() {
    setForm({ ...CLASE_VACIA, sede_id: esGestorSede ? usuario.sede_id : '' })
    setModalAbierto(true)
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setGuardando(true)
    try {
      await clasesService.crearClase({
        ...form,
        duracion_minutos: Number(form.duracion_minutos),
        aforo_maximo: Number(form.aforo_maximo),
        fecha_hora: new Date(form.fecha_hora).toISOString(),
      })
      setModalAbierto(false)
      cargarClases()
    } catch {
      setError('No se pudo crear la clase. Revisa los datos.')
    } finally {
      setGuardando(false)
    }
  }

  return (
    <div className="flex flex-col gap-gp-lg">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-gp-md">
        <div>
          <h2 className="text-headline-xl text-on-surface">Calendario de Clases</h2>
          <p className="text-body-md text-on-surface-variant mt-gp-xs">Programación y ocupación de las clases.</p>
        </div>
        {(usuario.rol === 'admin' || esGestorSede) && (
          <Button icon="add" onClick={abrirAlta}>
            Nueva Clase
          </Button>
        )}
      </div>

      {error && <p className="text-error">{error}</p>}

      {!esEntrenador && (
        <div className="bg-surface-container-lowest border border-outline-variant rounded-lg p-gp-sm flex items-center gap-gp-md">
          <SelectInput
            value={sedeId}
            disabled={esGestorSede}
            onChange={(e) => setSedeId(e.target.value)}
            className="w-64"
          >
            <option value="">Todas las sedes</option>
            {sedes.map((sede) => (
              <option key={sede.id} value={sede.id}>
                {sede.nombre}
              </option>
            ))}
          </SelectInput>
        </div>
      )}

      <div className="bg-surface-container-lowest border border-outline-variant rounded-xl divide-y divide-outline-variant">
        {ordenadas.length === 0 && <p className="p-gp-md text-on-surface-variant">No hay clases programadas.</p>}
        {ordenadas.map((clase) => (
          <div key={clase.id} className="p-gp-md flex items-center justify-between gap-gp-md">
            <div>
              <p className="text-body-md font-semibold text-on-surface">{clase.nombre}</p>
              <p className="text-label-sm text-on-surface-variant">
                {new Date(clase.fecha_hora).toLocaleString('es-ES', {
                  weekday: 'short',
                  day: '2-digit',
                  month: 'short',
                  hour: '2-digit',
                  minute: '2-digit',
                })}{' '}
                · {clase.duracion_minutos} min · {entrenadorNombre(clase.entrenador_id)}
              </p>
            </div>
            <div className="flex items-center gap-3">
              <StatusPill variant={clase.estado === 'programada' ? 'success' : 'neutral'}>{clase.estado}</StatusPill>
              <span className="text-label-sm text-on-surface-variant bg-surface-container px-2 py-1 rounded">
                {clase.aforo_maximo} plazas
              </span>
            </div>
          </div>
        ))}
      </div>

      {modalAbierto && (
        <Modal title="Nueva clase" onClose={() => setModalAbierto(false)}>
          <form onSubmit={handleSubmit}>
            <Field label="Sede" htmlFor="clase-sede">
              <SelectInput
                id="clase-sede"
                required
                disabled={esGestorSede}
                value={form.sede_id}
                onChange={(e) => setForm({ ...form, sede_id: e.target.value })}
              >
                <option value="" disabled>
                  Selecciona una sede
                </option>
                {sedes.map((sede) => (
                  <option key={sede.id} value={sede.id}>
                    {sede.nombre}
                  </option>
                ))}
              </SelectInput>
            </Field>
            <Field label="Entrenador" htmlFor="clase-entrenador">
              <SelectInput
                id="clase-entrenador"
                required
                value={form.entrenador_id}
                onChange={(e) => setForm({ ...form, entrenador_id: e.target.value })}
              >
                <option value="" disabled>
                  Selecciona un entrenador
                </option>
                {entrenadores.map((e) => (
                  <option key={e.id} value={e.id}>
                    {e.email ?? e.usuario_id}
                  </option>
                ))}
              </SelectInput>
            </Field>
            <Field label="Nombre" htmlFor="clase-nombre">
              <TextInput
                id="clase-nombre"
                required
                value={form.nombre}
                onChange={(e) => setForm({ ...form, nombre: e.target.value })}
              />
            </Field>
            <Field label="Tipo" htmlFor="clase-tipo">
              <TextInput
                id="clase-tipo"
                required
                placeholder="yoga, hiit, spinning..."
                value={form.tipo}
                onChange={(e) => setForm({ ...form, tipo: e.target.value })}
              />
            </Field>
            <Field label="Fecha y hora" htmlFor="clase-fecha">
              <TextInput
                id="clase-fecha"
                type="datetime-local"
                required
                value={form.fecha_hora}
                onChange={(e) => setForm({ ...form, fecha_hora: e.target.value })}
              />
            </Field>
            <Field label="Duración (minutos)" htmlFor="clase-duracion">
              <TextInput
                id="clase-duracion"
                type="number"
                min="1"
                required
                value={form.duracion_minutos}
                onChange={(e) => setForm({ ...form, duracion_minutos: e.target.value })}
              />
            </Field>
            <Field label="Aforo máximo" htmlFor="clase-aforo">
              <TextInput
                id="clase-aforo"
                type="number"
                min="1"
                required
                value={form.aforo_maximo}
                onChange={(e) => setForm({ ...form, aforo_maximo: e.target.value })}
              />
            </Field>
            <div className="flex justify-end gap-2 mt-gp-md">
              <Button type="button" variant="secondary" onClick={() => setModalAbierto(false)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={guardando}>
                {guardando ? 'Guardando…' : 'Guardar'}
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  )
}
