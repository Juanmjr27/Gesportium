import { useEffect, useMemo, useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import * as entrenadoresService from '../services/entrenadoresService'
import * as sedesService from '../services/sedesService'
import * as sociosService from '../services/sociosService'
import DataTable from '../components/DataTable'
import StatusPill from '../components/StatusPill'
import Modal from '../components/Modal'
import Button from '../components/Button'
import Field, { SelectInput, TextInput } from '../components/Field'

const ENTRENADOR_VACIO = { email: '', password: '', sede_id: '', especialidades: '' }

export default function EntrenadoresPage() {
  const { usuario } = useAuth()
  const [entrenadores, setEntrenadores] = useState([])
  const [sedes, setSedes] = useState([])
  const [socios, setSocios] = useState([])
  const [error, setError] = useState(null)
  const [modalAbierto, setModalAbierto] = useState(false)
  const [form, setForm] = useState(ENTRENADOR_VACIO)
  const [gestionando, setGestionando] = useState(null)
  const [asignados, setAsignados] = useState([])
  const [socioParaAsignar, setSocioParaAsignar] = useState('')

  function cargarEntrenadores() {
    entrenadoresService
      .listarEntrenadores()
      .then(setEntrenadores)
      .catch(() => setError('No se pudieron cargar los entrenadores.'))
  }

  useEffect(() => {
    cargarEntrenadores()
    sedesService.listarSedes().then(setSedes).catch(() => {})
    sociosService.listarSocios().then(setSocios).catch(() => {})
  }, [])

  const sedeNombre = useMemo(() => {
    const map = new Map(sedes.map((s) => [s.id, s.nombre]))
    return (id) => map.get(id) ?? id
  }, [sedes])

  const socioEmail = useMemo(() => {
    const map = new Map(socios.map((s) => [s.id, s.email]))
    return (id) => map.get(id) ?? id
  }, [socios])

  function abrirAlta() {
    setForm({ ...ENTRENADOR_VACIO, sede_id: usuario.rol === 'gestor_sede' ? usuario.sede_id : '' })
    setModalAbierto(true)
  }

  async function handleSubmit(event) {
    event.preventDefault()
    try {
      await entrenadoresService.crearEntrenador({
        email: form.email,
        password: form.password,
        sede_id: form.sede_id,
        especialidades: form.especialidades
          .split(',')
          .map((s) => s.trim())
          .filter(Boolean),
      })
      setModalAbierto(false)
      cargarEntrenadores()
    } catch (err) {
      if (err.response?.status === 409) {
        setError('Ese email ya está registrado.')
      } else {
        setError('No se pudo crear el entrenador.')
      }
    }
  }

  function abrirGestion(entrenador) {
    setGestionando(entrenador)
    setSocioParaAsignar('')
    entrenadoresService.listarSociosAsignados(entrenador.id).then(setAsignados).catch(() => setAsignados([]))
  }

  async function handleAsignar(event) {
    event.preventDefault()
    if (!socioParaAsignar) return
    await entrenadoresService.asignarSocio(gestionando.id, socioParaAsignar)
    entrenadoresService.listarSociosAsignados(gestionando.id).then(setAsignados)
    setSocioParaAsignar('')
  }

  async function handleDesasignar(socioId) {
    await entrenadoresService.desasignarSocio(gestionando.id, socioId)
    entrenadoresService.listarSociosAsignados(gestionando.id).then(setAsignados)
  }

  return (
    <div className="flex flex-col gap-gp-lg">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-headline-xl text-on-background">Entrenadores</h1>
          <p className="text-body-lg text-on-surface-variant mt-1">Personal técnico y sus socios asignados.</p>
        </div>
        <Button icon="add" onClick={abrirAlta}>
          Nuevo Entrenador
        </Button>
      </div>

      {error && <p className="text-error">{error}</p>}

      <DataTable
        rowKey="id"
        rows={entrenadores}
        emptyMessage="No hay entrenadores registrados."
        columns={[
          { key: 'email', label: 'Usuario' },
          { key: 'sede_id', label: 'Sede', render: (row) => sedeNombre(row.sede_id) },
          { key: 'especialidades', label: 'Especialidades', render: (row) => row.especialidades.join(', ') || '—' },
          {
            key: 'estado',
            label: 'Estado',
            render: (row) => <StatusPill variant={row.activo ? 'success' : 'neutral'}>{row.activo ? 'Activo' : 'Baja'}</StatusPill>,
          },
          {
            key: 'acciones',
            label: 'Acción',
            align: 'right',
            render: (row) => (
              <button onClick={() => abrirGestion(row)} className="text-primary hover:underline text-xs">
                Socios asignados
              </button>
            ),
          },
        ]}
      />

      {modalAbierto && (
        <Modal title="Nuevo entrenador" onClose={() => setModalAbierto(false)}>
          <form onSubmit={handleSubmit}>
            <Field label="Email" htmlFor="ent-email">
              <TextInput
                id="ent-email"
                type="email"
                required
                autoComplete="off"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                placeholder="entrenador@ejemplo.com"
              />
            </Field>
            <Field label="Contraseña" htmlFor="ent-password">
              <TextInput
                id="ent-password"
                type="password"
                required
                minLength={8}
                autoComplete="new-password"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                placeholder="Mínimo 8 caracteres"
              />
            </Field>
            <Field label="Sede" htmlFor="ent-sede">
              <SelectInput
                id="ent-sede"
                required
                disabled={usuario.rol === 'gestor_sede'}
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
            <Field label="Especialidades (separadas por coma)" htmlFor="ent-especialidades">
              <TextInput
                id="ent-especialidades"
                placeholder="yoga, hiit, nutrición"
                value={form.especialidades}
                onChange={(e) => setForm({ ...form, especialidades: e.target.value })}
              />
            </Field>
            <div className="flex justify-end gap-2 mt-gp-md">
              <Button type="button" variant="secondary" onClick={() => setModalAbierto(false)}>
                Cancelar
              </Button>
              <Button type="submit">Guardar</Button>
            </div>
          </form>
        </Modal>
      )}

      {gestionando && (
        <Modal title={`Socios asignados`} onClose={() => setGestionando(null)}>
          <ul className="flex flex-col gap-2 mb-gp-md">
            {asignados.length === 0 && <p className="text-on-surface-variant text-body-md">Sin socios asignados.</p>}
            {asignados.map((a) => (
              <li key={a.id} className="flex justify-between items-center border-b border-outline-variant/50 pb-2">
                <span className="text-body-md text-on-surface">{socioEmail(a.socio_id)}</span>
                <button onClick={() => handleDesasignar(a.socio_id)} className="text-error hover:underline text-xs">
                  Quitar
                </button>
              </li>
            ))}
          </ul>
          <form onSubmit={handleAsignar} className="flex gap-2">
            <SelectInput value={socioParaAsignar} onChange={(e) => setSocioParaAsignar(e.target.value)} className="flex-1">
              <option value="">Selecciona un socio</option>
              {socios.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.email ?? s.usuario_id}
                </option>
              ))}
            </SelectInput>
            <Button type="submit">Asignar</Button>
          </form>
        </Modal>
      )}
    </div>
  )
}
