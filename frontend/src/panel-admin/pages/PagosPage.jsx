import { useEffect, useMemo, useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import * as pagosService from '../services/pagosService'
import * as sociosService from '../services/sociosService'
import * as sedesService from '../services/sedesService'
import DataTable from '../components/DataTable'
import StatusPill from '../components/StatusPill'
import KpiCard from '../components/KpiCard'
import Modal from '../components/Modal'
import Button from '../components/Button'
import Field, { SelectInput, TextInput } from '../components/Field'

const ESTADO_VARIANTE = {
  confirmado: 'success',
  pendiente: 'warning',
  fallido: 'error',
}

export default function PagosPage() {
  const { usuario } = useAuth()
  const [remesas, setRemesas] = useState([])
  const [socios, setSocios] = useState([])
  const [sedes, setSedes] = useState([])
  const [socioId, setSocioId] = useState('')
  const [pagos, setPagos] = useState([])
  const [error, setError] = useState(null)
  const [modalRemesaAbierto, setModalRemesaAbierto] = useState(false)
  const [remesaForm, setRemesaForm] = useState({ sede_id: usuario.rol === 'gestor_sede' ? usuario.sede_id : '', fecha: '' })

  function cargarRemesas() {
    pagosService
      .listarRemesas()
      .then(setRemesas)
      .catch(() => setError('No se pudieron cargar las remesas.'))
  }

  useEffect(() => {
    cargarRemesas()
    sociosService.listarSocios().then(setSocios).catch(() => {})
    sedesService.listarSedes().then(setSedes).catch(() => {})
  }, [])

  useEffect(() => {
    if (!socioId) {
      setPagos([])
      return
    }
    pagosService
      .listarPagosDeSocio(socioId)
      .then(setPagos)
      .catch(() => setError('No se pudieron cargar los pagos de este socio.'))
  }, [socioId])

  const totales = useMemo(
    () => ({
      remesas: remesas.length,
      importe: remesas.reduce((acc, r) => acc + Number(r.total), 0),
      pagosIncluidos: remesas.reduce((acc, r) => acc + r.pagos_incluidos, 0),
    }),
    [remesas],
  )

  async function handleCrearRemesa(event) {
    event.preventDefault()
    try {
      await pagosService.crearRemesa(remesaForm)
      setModalRemesaAbierto(false)
      cargarRemesas()
    } catch {
      setError('No se pudo generar la remesa.')
    }
  }

  async function handleAnular(facturaId) {
    await pagosService.anularFactura(facturaId)
    pagosService.listarPagosDeSocio(socioId).then(setPagos)
  }

  async function handleReemitir(facturaId) {
    await pagosService.reemitirFactura(facturaId)
    pagosService.listarPagosDeSocio(socioId).then(setPagos)
  }

  return (
    <div className="flex flex-col gap-gp-lg">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-headline-xl text-on-background">Control de Pagos</h2>
          <p className="text-body-md text-on-surface-variant mt-1">Remesas de cobro y consulta de pagos por socio.</p>
        </div>
        <Button icon="add" onClick={() => setModalRemesaAbierto(true)}>
          Nueva Remesa
        </Button>
      </div>

      {error && <p className="text-error">{error}</p>}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-gp-lg">
        <KpiCard label="Remesas generadas" value={totales.remesas} icon="receipt_long" />
        <KpiCard label="Importe total" value={`${totales.importe.toFixed(2)} €`} icon="account_balance_wallet" />
        <KpiCard label="Pagos incluidos" value={totales.pagosIncluidos} icon="payments" />
      </div>

      <div>
        <h3 className="text-headline-md text-on-background mb-gp-sm">Remesas</h3>
        <DataTable
          rowKey="id"
          rows={remesas}
          emptyMessage="No hay remesas generadas."
          columns={[
            { key: 'fecha', label: 'Fecha' },
            { key: 'sede_id', label: 'Sede' },
            { key: 'pagos_incluidos', label: 'Pagos incluidos' },
            { key: 'total', label: 'Total', align: 'right', render: (row) => `${Number(row.total).toFixed(2)} €` },
          ]}
        />
      </div>

      <div>
        <div className="flex items-center gap-gp-md mb-gp-sm">
          <h3 className="text-headline-md text-on-background">Pagos por socio</h3>
          <SelectInput value={socioId} onChange={(e) => setSocioId(e.target.value)} className="w-64">
            <option value="">Selecciona un socio</option>
            {socios.map((s) => (
              <option key={s.id} value={s.id}>
                {s.email ?? s.usuario_id}
              </option>
            ))}
          </SelectInput>
        </div>
        <DataTable
          rowKey="id"
          rows={pagos}
          emptyMessage="Selecciona un socio para ver su historial de pagos."
          columns={[
            { key: 'concepto', label: 'Concepto' },
            { key: 'importe', label: 'Importe', align: 'right', render: (row) => `${Number(row.importe).toFixed(2)} €` },
            { key: 'fecha', label: 'Fecha' },
            {
              key: 'estado',
              label: 'Estado',
              render: (row) => <StatusPill variant={ESTADO_VARIANTE[row.estado] ?? 'neutral'}>{row.estado}</StatusPill>,
            },
            {
              key: 'acciones',
              label: 'Acción',
              align: 'right',
              render: (row) =>
                row.factura_id && (
                  <div className="flex gap-2 justify-end">
                    <button onClick={() => handleReemitir(row.factura_id)} className="text-primary hover:underline text-xs">
                      Reemitir
                    </button>
                    <button onClick={() => handleAnular(row.factura_id)} className="text-error hover:underline text-xs">
                      Anular
                    </button>
                  </div>
                ),
            },
          ]}
        />
      </div>

      {modalRemesaAbierto && (
        <Modal title="Generar remesa" onClose={() => setModalRemesaAbierto(false)}>
          <form onSubmit={handleCrearRemesa}>
            <Field label="Sede" htmlFor="remesa-sede">
              <SelectInput
                id="remesa-sede"
                required
                disabled={usuario.rol === 'gestor_sede'}
                value={remesaForm.sede_id}
                onChange={(e) => setRemesaForm({ ...remesaForm, sede_id: e.target.value })}
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
            <Field label="Fecha" htmlFor="remesa-fecha">
              <TextInput
                id="remesa-fecha"
                type="date"
                required
                value={remesaForm.fecha}
                onChange={(e) => setRemesaForm({ ...remesaForm, fecha: e.target.value })}
              />
            </Field>
            <div className="flex justify-end gap-2 mt-gp-md">
              <Button type="button" variant="secondary" onClick={() => setModalRemesaAbierto(false)}>
                Cancelar
              </Button>
              <Button type="submit">Generar</Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  )
}
