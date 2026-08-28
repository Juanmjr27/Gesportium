import { useEffect, useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import * as crmService from '../services/crmService'
import * as sedesService from '../services/sedesService'
import Modal from '../components/Modal'
import Button from '../components/Button'
import Field, { SelectInput, TextInput } from '../components/Field'

const COLUMNAS = [
  { estado: 'nuevo', label: 'Nuevos' },
  { estado: 'contactado', label: 'Contactados' },
  { estado: 'en_negociacion', label: 'En negociación' },
  { estado: 'convertido', label: 'Convertido' },
  { estado: 'descartado', label: 'Descartado' },
]

const LEAD_VACIO = { nombre: '', email: '', telefono: '', sede_interes_id: '', origen: '' }
const CONVERSION_VACIA = {
  fecha_nacimiento: '',
  direccion: '',
  contacto_emergencia_nombre: '',
  contacto_emergencia_telefono: '',
}

export default function LeadsPage() {
  const { usuario } = useAuth()
  const [leads, setLeads] = useState([])
  const [sedes, setSedes] = useState([])
  const [error, setError] = useState(null)
  const [modalAltaAbierto, setModalAltaAbierto] = useState(false)
  const [form, setForm] = useState(LEAD_VACIO)
  const [leadConvirtiendo, setLeadConvirtiendo] = useState(null)
  const [conversionForm, setConversionForm] = useState(CONVERSION_VACIA)

  function cargarLeads() {
    crmService
      .listarLeads()
      .then(setLeads)
      .catch(() => setError('No se pudieron cargar los leads.'))
  }

  useEffect(() => {
    cargarLeads()
    sedesService.listarSedes().then(setSedes).catch(() => {})
  }, [])

  async function handleCrear(event) {
    event.preventDefault()
    try {
      await crmService.crearLead(form)
      setModalAltaAbierto(false)
      setForm(LEAD_VACIO)
      cargarLeads()
    } catch {
      setError('No se pudo crear el lead.')
    }
  }

  async function cambiarEstado(lead, nuevoEstado) {
    if (nuevoEstado === 'convertido') {
      setLeadConvirtiendo(lead)
      return
    }
    await crmService.actualizarLead(lead.id, { estado: nuevoEstado })
    cargarLeads()
  }

  async function handleConvertir(event) {
    event.preventDefault()
    try {
      await crmService.convertirLead(leadConvirtiendo.id, conversionForm)
      setLeadConvirtiendo(null)
      setConversionForm(CONVERSION_VACIA)
      cargarLeads()
    } catch {
      setError('No se pudo convertir el lead a socio.')
    }
  }

  return (
    <div className="flex flex-col gap-gp-lg h-full">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-gp-md">
        <div>
          <h2 className="text-headline-xl text-on-background">Pipeline de Leads</h2>
          <p className="text-body-md text-on-surface-variant mt-1">Seguimiento de prospectos hasta su conversión.</p>
        </div>
        <Button icon="add" onClick={() => setModalAltaAbierto(true)}>
          Nuevo Lead
        </Button>
      </div>

      {error && <p className="text-error">{error}</p>}

      <div className="flex-1 overflow-x-auto pb-4">
        <div className="flex gap-gp-lg min-w-[1000px] items-start">
          {COLUMNAS.map((col) => {
            const leadsColumna = leads.filter((l) => l.estado === col.estado)
            return (
              <div key={col.estado} className="w-[280px] flex-shrink-0 bg-surface-container-low rounded-xl flex flex-col">
                <div className="p-3 border-b border-outline-variant flex justify-between items-center bg-surface-container rounded-t-xl">
                  <h3 className="text-headline-md text-on-surface flex items-center gap-2">
                    {col.label}
                    <span className="bg-surface-container-highest text-on-surface-variant text-label-sm px-2 py-0.5 rounded-full">
                      {leadsColumna.length}
                    </span>
                  </h3>
                </div>
                <div className="p-3 flex flex-col gap-3">
                  {leadsColumna.map((lead) => (
                    <div key={lead.id} className="bg-surface-container-lowest border border-outline-variant rounded-lg p-3">
                      <h4 className="text-button text-on-surface mb-1">{lead.nombre}</h4>
                      <p className="text-body-md text-on-surface-variant mb-2">{lead.origen}</p>
                      <p className="text-label-sm text-on-surface-variant mb-2">{lead.email}</p>
                      {col.estado !== 'convertido' && col.estado !== 'descartado' && (
                        <select
                          value={lead.estado}
                          onChange={(e) => cambiarEstado(lead, e.target.value)}
                          className="w-full text-label-sm rounded border border-outline-variant bg-surface px-1 py-1"
                        >
                          {COLUMNAS.map((c) => (
                            <option key={c.estado} value={c.estado}>
                              {c.label}
                            </option>
                          ))}
                        </select>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {modalAltaAbierto && (
        <Modal title="Nuevo lead" onClose={() => setModalAltaAbierto(false)}>
          <form onSubmit={handleCrear}>
            <Field label="Nombre" htmlFor="lead-nombre">
              <TextInput
                id="lead-nombre"
                required
                value={form.nombre}
                onChange={(e) => setForm({ ...form, nombre: e.target.value })}
              />
            </Field>
            <Field label="Email" htmlFor="lead-email">
              <TextInput
                id="lead-email"
                type="email"
                required
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
              />
            </Field>
            <Field label="Teléfono" htmlFor="lead-telefono">
              <TextInput
                id="lead-telefono"
                required
                value={form.telefono}
                onChange={(e) => setForm({ ...form, telefono: e.target.value })}
              />
            </Field>
            <Field label="Sede de interés" htmlFor="lead-sede">
              <SelectInput
                id="lead-sede"
                required
                disabled={usuario.rol === 'gestor_sede'}
                value={form.sede_interes_id}
                onChange={(e) => setForm({ ...form, sede_interes_id: e.target.value })}
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
            <Field label="Origen" htmlFor="lead-origen">
              <TextInput
                id="lead-origen"
                required
                placeholder="web, referido, instagram..."
                value={form.origen}
                onChange={(e) => setForm({ ...form, origen: e.target.value })}
              />
            </Field>
            <div className="flex justify-end gap-2 mt-gp-md">
              <Button type="button" variant="secondary" onClick={() => setModalAltaAbierto(false)}>
                Cancelar
              </Button>
              <Button type="submit">Guardar</Button>
            </div>
          </form>
        </Modal>
      )}

      {leadConvirtiendo && (
        <Modal title={`Convertir a socio: ${leadConvirtiendo.nombre}`} onClose={() => setLeadConvirtiendo(null)}>
          <form onSubmit={handleConvertir}>
            <Field label="Fecha de nacimiento" htmlFor="conv-fecha-nac">
              <TextInput
                id="conv-fecha-nac"
                type="date"
                required
                value={conversionForm.fecha_nacimiento}
                onChange={(e) => setConversionForm({ ...conversionForm, fecha_nacimiento: e.target.value })}
              />
            </Field>
            <Field label="Dirección" htmlFor="conv-direccion">
              <TextInput
                id="conv-direccion"
                required
                value={conversionForm.direccion}
                onChange={(e) => setConversionForm({ ...conversionForm, direccion: e.target.value })}
              />
            </Field>
            <Field label="Contacto de emergencia" htmlFor="conv-contacto-nombre">
              <TextInput
                id="conv-contacto-nombre"
                required
                value={conversionForm.contacto_emergencia_nombre}
                onChange={(e) => setConversionForm({ ...conversionForm, contacto_emergencia_nombre: e.target.value })}
              />
            </Field>
            <Field label="Teléfono de emergencia" htmlFor="conv-contacto-telefono">
              <TextInput
                id="conv-contacto-telefono"
                required
                value={conversionForm.contacto_emergencia_telefono}
                onChange={(e) => setConversionForm({ ...conversionForm, contacto_emergencia_telefono: e.target.value })}
              />
            </Field>
            <div className="flex justify-end gap-2 mt-gp-md">
              <Button type="button" variant="secondary" onClick={() => setLeadConvirtiendo(null)}>
                Cancelar
              </Button>
              <Button type="submit">Convertir</Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  )
}
