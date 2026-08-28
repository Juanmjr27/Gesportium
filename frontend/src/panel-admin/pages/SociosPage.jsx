import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import * as sociosService from '../services/sociosService'
import * as sedesService from '../services/sedesService'
import DataTable from '../components/DataTable'
import StatusPill from '../components/StatusPill'
import Modal from '../components/Modal'
import Button from '../components/Button'
import Field, { TextInput, SelectInput } from '../components/Field'

const SOCIO_VACIO = {
  usuario_id: '',
  sede_id: '',
  fecha_nacimiento: '',
  telefono: '',
  direccion: '',
  contacto_emergencia_nombre: '',
  contacto_emergencia_telefono: '',
}

export default function SociosPage() {
  const { usuario } = useAuth()
  const navigate = useNavigate()
  const [socios, setSocios] = useState([])
  const [sedes, setSedes] = useState([])
  const [busqueda, setBusqueda] = useState('')
  const [error, setError] = useState(null)
  const [modalAbierto, setModalAbierto] = useState(false)
  const [form, setForm] = useState(SOCIO_VACIO)
  const [guardando, setGuardando] = useState(false)
  const [candidatoQuery, setCandidatoQuery] = useState('')
  const [candidatos, setCandidatos] = useState([])
  const [candidatosAbierto, setCandidatosAbierto] = useState(false)

  const puedeCrear = usuario.rol === 'admin' || usuario.rol === 'gestor_sede'

  function cargarSocios() {
    sociosService
      .listarSocios()
      .then(setSocios)
      .catch(() => setError('No se pudieron cargar los socios.'))
  }

  useEffect(() => {
    cargarSocios()
    sedesService.listarSedes().then(setSedes).catch(() => {})
  }, [])

  const sedeNombre = useMemo(() => {
    const map = new Map(sedes.map((s) => [s.id, s.nombre]))
    return (id) => map.get(id) ?? id
  }, [sedes])

  const filtrados = socios.filter((s) => (s.email ?? s.usuario_id).toLowerCase().includes(busqueda.toLowerCase()))

  useEffect(() => {
    if (!modalAbierto) return
    const timeout = setTimeout(() => {
      sociosService
        .listarCandidatosAlta(candidatoQuery)
        .then(setCandidatos)
        .catch(() => setCandidatos([]))
    }, 250)
    return () => clearTimeout(timeout)
  }, [candidatoQuery, modalAbierto])

  function abrirAlta() {
    setForm({
      ...SOCIO_VACIO,
      sede_id: usuario.rol === 'gestor_sede' ? usuario.sede_id : '',
    })
    setCandidatoQuery('')
    setCandidatos([])
    setCandidatosAbierto(false)
    setModalAbierto(true)
  }

  function seleccionarCandidato(candidato) {
    setForm({ ...form, usuario_id: candidato.id })
    setCandidatoQuery(candidato.email)
    setCandidatosAbierto(false)
  }

  async function handleSubmit(event) {
    event.preventDefault()
    if (!form.usuario_id) {
      setError('Selecciona un usuario de la lista de sugerencias.')
      return
    }
    setGuardando(true)
    try {
      await sociosService.crearSocio(form)
      setModalAbierto(false)
      cargarSocios()
    } catch {
      setError('No se pudo crear el socio. Revisa los datos.')
    } finally {
      setGuardando(false)
    }
  }

  return (
    <div className="flex flex-col gap-gp-lg">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-gp-md">
        <div>
          <h1 className="text-headline-xl text-on-background">Gestión de Socios</h1>
          <p className="text-body-lg text-on-surface-variant mt-1">Consulta y gestiona los socios del gimnasio.</p>
        </div>
        {puedeCrear && (
          <Button icon="add" onClick={abrirAlta}>
            Alta de Socio
          </Button>
        )}
      </div>

      {error && <p className="text-error">{error}</p>}

      <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-gp-md flex gap-gp-md items-center shadow-sm">
        <div className="relative w-full lg:w-64">
          <span className="material-symbols-outlined absolute left-gp-sm top-1/2 -translate-y-1/2 text-on-surface-variant">
            search
          </span>
          <input
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            placeholder="Buscar por email..."
            className="w-full pl-gp-xl pr-gp-sm py-gp-sm rounded border border-outline-variant bg-surface focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none text-body-md text-on-surface transition-all"
          />
        </div>
      </div>

      <DataTable
        rowKey="id"
        rows={filtrados}
        emptyMessage="No hay socios que mostrar."
        onRowClick={(row) => navigate(`/admin/socios/${row.id}`)}
        columns={[
          { key: 'email', label: 'Usuario' },
          {
            key: 'sede_id',
            label: 'Sede',
            render: (row) => sedeNombre(row.sede_id),
          },
          {
            key: 'estado',
            label: 'Estado',
            render: (row) => (
              <StatusPill variant={row.activo ? 'success' : 'neutral'}>{row.activo ? 'Activo' : 'Inactivo'}</StatusPill>
            ),
          },
          { key: 'fecha_alta', label: 'Fecha alta' },
        ]}
      />

      {modalAbierto && (
        <Modal title="Alta de socio" onClose={() => setModalAbierto(false)}>
          <form onSubmit={handleSubmit}>
            <Field label="Usuario" htmlFor="usuario_id">
              <div className="relative">
                <TextInput
                  id="usuario_id"
                  required
                  autoComplete="off"
                  value={candidatoQuery}
                  onFocus={() => setCandidatosAbierto(true)}
                  onBlur={() => setTimeout(() => setCandidatosAbierto(false), 150)}
                  onChange={(e) => {
                    setCandidatoQuery(e.target.value)
                    setForm({ ...form, usuario_id: '' })
                    setCandidatosAbierto(true)
                  }}
                  placeholder="Busca por email…"
                />
                {candidatosAbierto && candidatos.length > 0 && (
                  <ul className="absolute z-10 mt-1 w-full max-h-48 overflow-auto rounded border border-outline-variant bg-surface shadow-md">
                    {candidatos.map((c) => (
                      <li key={c.id}>
                        <button
                          type="button"
                          onClick={() => seleccionarCandidato(c)}
                          className="w-full text-left px-gp-sm py-gp-sm text-body-md text-on-surface hover:bg-surface-container-lowest"
                        >
                          {c.email}
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
                {candidatosAbierto && candidatoQuery && candidatos.length === 0 && (
                  <p className="absolute z-10 mt-1 w-full rounded border border-outline-variant bg-surface shadow-md px-gp-sm py-gp-sm text-body-md text-on-surface-variant">
                    Sin resultados
                  </p>
                )}
              </div>
            </Field>
            <Field label="Sede" htmlFor="sede_id">
              <SelectInput
                id="sede_id"
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
            <Field label="Fecha de nacimiento" htmlFor="fecha_nacimiento">
              <TextInput
                id="fecha_nacimiento"
                type="date"
                required
                value={form.fecha_nacimiento}
                onChange={(e) => setForm({ ...form, fecha_nacimiento: e.target.value })}
              />
            </Field>
            <Field label="Teléfono" htmlFor="telefono">
              <TextInput
                id="telefono"
                required
                value={form.telefono}
                onChange={(e) => setForm({ ...form, telefono: e.target.value })}
              />
            </Field>
            <Field label="Dirección" htmlFor="direccion">
              <TextInput
                id="direccion"
                required
                value={form.direccion}
                onChange={(e) => setForm({ ...form, direccion: e.target.value })}
              />
            </Field>
            <Field label="Nombre del contacto de emergencia" htmlFor="contacto_emergencia_nombre">
              <TextInput
                id="contacto_emergencia_nombre"
                required
                value={form.contacto_emergencia_nombre}
                onChange={(e) => setForm({ ...form, contacto_emergencia_nombre: e.target.value })}
              />
            </Field>
            <Field label="Teléfono de emergencia" htmlFor="contacto_emergencia_telefono">
              <TextInput
                id="contacto_emergencia_telefono"
                required
                value={form.contacto_emergencia_telefono}
                onChange={(e) => setForm({ ...form, contacto_emergencia_telefono: e.target.value })}
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
