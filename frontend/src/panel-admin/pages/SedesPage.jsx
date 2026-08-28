import { useEffect, useState } from 'react'
import * as sedesService from '../services/sedesService'
import DataTable from '../components/DataTable'
import StatusPill from '../components/StatusPill'
import Modal from '../components/Modal'
import Button from '../components/Button'
import Field, { TextInput } from '../components/Field'

const SEDE_VACIA = {
  nombre: '',
  direccion: '',
  ciudad: '',
  telefono: '',
  horario_apertura: '07:00',
  horario_cierre: '22:00',
  aforo_maximo: 100,
}

export default function SedesPage() {
  const [sedes, setSedes] = useState([])
  const [detalles, setDetalles] = useState({})
  const [error, setError] = useState(null)
  const [modalAbierto, setModalAbierto] = useState(false)
  const [editandoId, setEditandoId] = useState(null)
  const [form, setForm] = useState(SEDE_VACIA)
  const [guardando, setGuardando] = useState(false)

  function cargarSedes() {
    sedesService
      .listarSedes()
      .then(async (lista) => {
        setSedes(lista)
        const entradas = await Promise.all(
          lista.map((s) => sedesService.obtenerSede(s.id).then((detalle) => [s.id, detalle])),
        )
        setDetalles(Object.fromEntries(entradas))
      })
      .catch(() => setError('No se pudieron cargar las sedes.'))
  }

  useEffect(() => {
    cargarSedes()
  }, [])

  function abrirAlta() {
    setEditandoId(null)
    setForm(SEDE_VACIA)
    setModalAbierto(true)
  }

  function abrirEdicion(sedeId) {
    const detalle = detalles[sedeId]
    setEditandoId(sedeId)
    setForm({
      nombre: detalle.nombre,
      direccion: detalle.direccion,
      ciudad: detalle.ciudad,
      telefono: detalle.telefono,
      horario_apertura: detalle.horario_apertura,
      horario_cierre: detalle.horario_cierre,
      aforo_maximo: detalle.aforo_maximo,
    })
    setModalAbierto(true)
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setGuardando(true)
    const body = { ...form, aforo_maximo: Number(form.aforo_maximo) }
    try {
      if (editandoId) {
        await sedesService.actualizarSede(editandoId, body)
      } else {
        await sedesService.crearSede(body)
      }
      setModalAbierto(false)
      cargarSedes()
    } catch {
      setError('No se pudo guardar la sede.')
    } finally {
      setGuardando(false)
    }
  }

  return (
    <div className="flex flex-col gap-gp-lg">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-headline-xl text-on-background">Sedes</h1>
          <p className="text-body-lg text-on-surface-variant mt-1">Gestiona las instalaciones de la cadena.</p>
        </div>
        <Button icon="add" onClick={abrirAlta}>
          Nueva Sede
        </Button>
      </div>

      {error && <p className="text-error">{error}</p>}

      <DataTable
        rowKey="id"
        rows={sedes}
        emptyMessage="No hay sedes registradas."
        columns={[
          { key: 'nombre', label: 'Nombre' },
          { key: 'ciudad', label: 'Ciudad' },
          { key: 'direccion', label: 'Dirección' },
          {
            key: 'horario',
            label: 'Horario',
            render: (row) => `${row.horario_apertura} - ${row.horario_cierre}`,
          },
          {
            key: 'estado',
            label: 'Estado',
            render: (row) =>
              detalles[row.id] && (
                <StatusPill variant={detalles[row.id].activa ? 'success' : 'neutral'}>
                  {detalles[row.id].activa ? 'Activa' : 'Inactiva'}
                </StatusPill>
              ),
          },
          {
            key: 'acciones',
            label: 'Acción',
            align: 'right',
            render: (row) => (
              <button onClick={() => abrirEdicion(row.id)} className="text-primary hover:underline text-xs">
                Editar
              </button>
            ),
          },
        ]}
      />

      {modalAbierto && (
        <Modal title={editandoId ? 'Editar sede' : 'Nueva sede'} onClose={() => setModalAbierto(false)}>
          <form onSubmit={handleSubmit}>
            <Field label="Nombre" htmlFor="sede-nombre">
              <TextInput
                id="sede-nombre"
                required
                value={form.nombre}
                onChange={(e) => setForm({ ...form, nombre: e.target.value })}
              />
            </Field>
            <Field label="Dirección" htmlFor="sede-direccion">
              <TextInput
                id="sede-direccion"
                required
                value={form.direccion}
                onChange={(e) => setForm({ ...form, direccion: e.target.value })}
              />
            </Field>
            <Field label="Ciudad" htmlFor="sede-ciudad">
              <TextInput
                id="sede-ciudad"
                required
                value={form.ciudad}
                onChange={(e) => setForm({ ...form, ciudad: e.target.value })}
              />
            </Field>
            <Field label="Teléfono" htmlFor="sede-telefono">
              <TextInput
                id="sede-telefono"
                required
                value={form.telefono}
                onChange={(e) => setForm({ ...form, telefono: e.target.value })}
              />
            </Field>
            <div className="grid grid-cols-2 gap-gp-md">
              <Field label="Apertura" htmlFor="sede-apertura">
                <TextInput
                  id="sede-apertura"
                  type="time"
                  required
                  value={form.horario_apertura}
                  onChange={(e) => setForm({ ...form, horario_apertura: e.target.value })}
                />
              </Field>
              <Field label="Cierre" htmlFor="sede-cierre">
                <TextInput
                  id="sede-cierre"
                  type="time"
                  required
                  value={form.horario_cierre}
                  onChange={(e) => setForm({ ...form, horario_cierre: e.target.value })}
                />
              </Field>
            </div>
            <Field label="Aforo máximo" htmlFor="sede-aforo">
              <TextInput
                id="sede-aforo"
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
