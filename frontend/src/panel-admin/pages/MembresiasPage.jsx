import { useEffect, useMemo, useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import * as membresiasService from '../services/membresiasService'
import * as sociosService from '../services/sociosService'
import * as sedesService from '../services/sedesService'
import DataTable from '../components/DataTable'
import StatusPill from '../components/StatusPill'
import Modal from '../components/Modal'
import Button from '../components/Button'
import Field, { SelectInput, TextInput } from '../components/Field'

const PLAN_VACIO = { nombre: '', precio: '', duracion: 'mensual', alcance: 'toda_cadena', sede_id: '', preaviso_cancelacion_dias: 0 }
const MEMBRESIA_VACIA = { socio_id: '', plan_id: '', renovacion_automatica: true }

const ESTADO_VARIANTE = {
  activa: 'success',
  congelada: 'warning',
  cancelada: 'error',
  vencida: 'neutral',
}

export default function MembresiasPage() {
  const { usuario } = useAuth()
  const [planes, setPlanes] = useState([])
  const [membresias, setMembresias] = useState([])
  const [socios, setSocios] = useState([])
  const [sedes, setSedes] = useState([])
  const [error, setError] = useState(null)
  const [modalPlanAbierto, setModalPlanAbierto] = useState(false)
  const [planForm, setPlanForm] = useState(PLAN_VACIO)
  const [modalMembresiaAbierto, setModalMembresiaAbierto] = useState(false)
  const [membresiaForm, setMembresiaForm] = useState(MEMBRESIA_VACIA)

  function cargarTodo() {
    membresiasService.listarPlanes().then(setPlanes).catch(() => setError('No se pudieron cargar los planes.'))
    membresiasService.listarMembresias().then(setMembresias).catch(() => setError('No se pudieron cargar las membresías.'))
  }

  useEffect(() => {
    cargarTodo()
    sociosService.listarSocios().then(setSocios).catch(() => {})
    sedesService.listarSedes().then(setSedes).catch(() => {})
  }, [])

  const planNombre = useMemo(() => {
    const map = new Map(planes.map((p) => [p.id, p.nombre]))
    return (id) => map.get(id) ?? id
  }, [planes])

  const socioEmail = useMemo(() => {
    const map = new Map(socios.map((s) => [s.id, s.email]))
    return (id) => map.get(id) ?? id
  }, [socios])

  async function handleCrearPlan(event) {
    event.preventDefault()
    try {
      await membresiasService.crearPlan({
        ...planForm,
        precio: Number(planForm.precio),
        preaviso_cancelacion_dias: Number(planForm.preaviso_cancelacion_dias),
        sede_id: planForm.alcance === 'sede_unica' ? planForm.sede_id : null,
      })
      setModalPlanAbierto(false)
      setPlanForm(PLAN_VACIO)
      cargarTodo()
    } catch {
      setError('No se pudo crear el plan.')
    }
  }

  async function handleCrearMembresia(event) {
    event.preventDefault()
    try {
      await membresiasService.crearMembresia(membresiaForm)
      setModalMembresiaAbierto(false)
      setMembresiaForm(MEMBRESIA_VACIA)
      cargarTodo()
    } catch {
      setError('No se pudo asignar la membresía.')
    }
  }

  async function accionMembresia(id, accion) {
    if (accion === 'congelar') await membresiasService.congelarMembresia(id)
    if (accion === 'reactivar') await membresiasService.reactivarMembresia(id)
    if (accion === 'cancelar') await membresiasService.cancelarMembresia(id)
    cargarTodo()
  }

  return (
    <div className="flex flex-col gap-gp-lg">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-headline-xl text-on-background">Membresías</h1>
          <p className="text-body-lg text-on-surface-variant mt-1">Planes y membresías activas de los socios.</p>
        </div>
      </div>

      {error && <p className="text-error">{error}</p>}

      <div>
        <div className="flex justify-between items-center mb-gp-sm">
          <h3 className="text-headline-md text-on-background">Planes</h3>
          <Button icon="add" onClick={() => setModalPlanAbierto(true)}>
            Nuevo Plan
          </Button>
        </div>
        <DataTable
          rowKey="id"
          rows={planes}
          emptyMessage="No hay planes de membresía."
          columns={[
            { key: 'nombre', label: 'Nombre' },
            { key: 'precio', label: 'Precio', align: 'right', render: (row) => `${Number(row.precio).toFixed(2)} €` },
            { key: 'duracion', label: 'Duración' },
            { key: 'alcance', label: 'Alcance' },
            {
              key: 'estado',
              label: 'Estado',
              render: (row) => <StatusPill variant={row.activo ? 'success' : 'neutral'}>{row.activo ? 'Activo' : 'Inactivo'}</StatusPill>,
            },
          ]}
        />
      </div>

      <div>
        <div className="flex justify-between items-center mb-gp-sm">
          <h3 className="text-headline-md text-on-background">Membresías de socios</h3>
          <Button icon="add" onClick={() => setModalMembresiaAbierto(true)}>
            Asignar Membresía
          </Button>
        </div>
        <DataTable
          rowKey="id"
          rows={membresias}
          emptyMessage="No hay membresías registradas."
          columns={[
            { key: 'socio_id', label: 'Socio', render: (row) => socioEmail(row.socio_id) },
            { key: 'plan_id', label: 'Plan', render: (row) => planNombre(row.plan_id) },
            { key: 'fecha_proxima_renovacion', label: 'Próxima renovación' },
            {
              key: 'estado',
              label: 'Estado',
              render: (row) => <StatusPill variant={ESTADO_VARIANTE[row.estado] ?? 'neutral'}>{row.estado}</StatusPill>,
            },
            {
              key: 'acciones',
              label: 'Acción',
              align: 'right',
              render: (row) => (
                <div className="flex gap-2 justify-end">
                  {row.estado === 'activa' && (
                    <>
                      <button onClick={() => accionMembresia(row.id, 'congelar')} className="text-primary hover:underline text-xs">
                        Congelar
                      </button>
                      <button onClick={() => accionMembresia(row.id, 'cancelar')} className="text-error hover:underline text-xs">
                        Cancelar
                      </button>
                    </>
                  )}
                  {row.estado === 'congelada' && (
                    <button onClick={() => accionMembresia(row.id, 'reactivar')} className="text-primary hover:underline text-xs">
                      Reactivar
                    </button>
                  )}
                </div>
              ),
            },
          ]}
        />
      </div>

      {modalPlanAbierto && (
        <Modal title="Nuevo plan de membresía" onClose={() => setModalPlanAbierto(false)}>
          <form onSubmit={handleCrearPlan}>
            <Field label="Nombre" htmlFor="plan-nombre">
              <TextInput
                id="plan-nombre"
                required
                value={planForm.nombre}
                onChange={(e) => setPlanForm({ ...planForm, nombre: e.target.value })}
              />
            </Field>
            <Field label="Precio" htmlFor="plan-precio">
              <TextInput
                id="plan-precio"
                type="number"
                min="0.01"
                step="0.01"
                required
                value={planForm.precio}
                onChange={(e) => setPlanForm({ ...planForm, precio: e.target.value })}
              />
            </Field>
            <Field label="Duración" htmlFor="plan-duracion">
              <SelectInput
                id="plan-duracion"
                value={planForm.duracion}
                onChange={(e) => setPlanForm({ ...planForm, duracion: e.target.value })}
              >
                <option value="mensual">Mensual</option>
                <option value="trimestral">Trimestral</option>
                <option value="anual">Anual</option>
              </SelectInput>
            </Field>
            <Field label="Alcance" htmlFor="plan-alcance">
              <SelectInput
                id="plan-alcance"
                value={planForm.alcance}
                onChange={(e) => setPlanForm({ ...planForm, alcance: e.target.value })}
              >
                <option value="toda_cadena">Toda la cadena</option>
                <option value="sede_unica">Sede única</option>
              </SelectInput>
            </Field>
            {planForm.alcance === 'sede_unica' && (
              <Field label="Sede" htmlFor="plan-sede">
                <SelectInput
                  id="plan-sede"
                  required
                  disabled={usuario.rol === 'gestor_sede'}
                  value={planForm.sede_id}
                  onChange={(e) => setPlanForm({ ...planForm, sede_id: e.target.value })}
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
            )}
            <Field label="Preaviso de cancelación (días)" htmlFor="plan-preaviso">
              <TextInput
                id="plan-preaviso"
                type="number"
                min="0"
                value={planForm.preaviso_cancelacion_dias}
                onChange={(e) => setPlanForm({ ...planForm, preaviso_cancelacion_dias: e.target.value })}
              />
            </Field>
            <div className="flex justify-end gap-2 mt-gp-md">
              <Button type="button" variant="secondary" onClick={() => setModalPlanAbierto(false)}>
                Cancelar
              </Button>
              <Button type="submit">Guardar</Button>
            </div>
          </form>
        </Modal>
      )}

      {modalMembresiaAbierto && (
        <Modal title="Asignar membresía" onClose={() => setModalMembresiaAbierto(false)}>
          <form onSubmit={handleCrearMembresia}>
            <Field label="Socio" htmlFor="mem-socio">
              <SelectInput
                id="mem-socio"
                required
                value={membresiaForm.socio_id}
                onChange={(e) => setMembresiaForm({ ...membresiaForm, socio_id: e.target.value })}
              >
                <option value="" disabled>
                  Selecciona un socio
                </option>
                {socios.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.email ?? s.usuario_id}
                  </option>
                ))}
              </SelectInput>
            </Field>
            <Field label="Plan" htmlFor="mem-plan">
              <SelectInput
                id="mem-plan"
                required
                value={membresiaForm.plan_id}
                onChange={(e) => setMembresiaForm({ ...membresiaForm, plan_id: e.target.value })}
              >
                <option value="" disabled>
                  Selecciona un plan
                </option>
                {planes.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.nombre}
                  </option>
                ))}
              </SelectInput>
            </Field>
            <div className="flex justify-end gap-2 mt-gp-md">
              <Button type="button" variant="secondary" onClick={() => setModalMembresiaAbierto(false)}>
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
