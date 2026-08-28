import { useEffect, useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import * as informesService from '../services/informesService'
import * as sedesService from '../services/sedesService'
import DataTable from '../components/DataTable'
import Button from '../components/Button'
import Field, { SelectInput, TextInput } from '../components/Field'

const TIPOS = [
  { value: 'socios', label: 'Socios' },
  { value: 'financiero', label: 'Financiero' },
  { value: 'ocupacion', label: 'Ocupación' },
  { value: 'comercial', label: 'Comercial' },
]

const RESUMEN_KEYS = new Set(['sede_id', 'fecha_inicio', 'fecha_fin', 'detalle', 'resumen_ia'])

function hoyMenos(dias) {
  const d = new Date()
  d.setDate(d.getDate() - dias)
  return d.toISOString().slice(0, 10)
}

export default function InformesPage() {
  const { usuario } = useAuth()
  const [sedes, setSedes] = useState([])
  const [tipo, setTipo] = useState('socios')
  const [sedeId, setSedeId] = useState('')
  const [fechaInicio, setFechaInicio] = useState(hoyMenos(30))
  const [fechaFin, setFechaFin] = useState(hoyMenos(0))
  const [informe, setInforme] = useState(null)
  const [error, setError] = useState(null)
  const [cargando, setCargando] = useState(false)
  const [generandoResumen, setGenerandoResumen] = useState(false)

  useEffect(() => {
    if (usuario.rol === 'admin') sedesService.listarSedes().then(setSedes).catch(() => {})
  }, [usuario.rol])

  const params = { fecha_inicio: fechaInicio, fecha_fin: fechaFin, ...(sedeId ? { sede_id: sedeId } : {}) }

  async function handleGenerar(event) {
    event.preventDefault()
    setCargando(true)
    setError(null)
    try {
      const data = await informesService.obtenerInforme(tipo, params)
      setInforme(data)
    } catch {
      setError('No se pudo generar el informe.')
    } finally {
      setCargando(false)
    }
  }

  async function handleResumenIA() {
    setGenerandoResumen(true)
    try {
      const data = await informesService.generarResumenIA(tipo, params)
      setInforme(data)
    } catch {
      setError('No se pudo generar el resumen con IA.')
    } finally {
      setGenerandoResumen(false)
    }
  }

  async function handleExportar(formato) {
    const blob = await informesService.exportarInforme(tipo, { ...params, formato })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `informe-${tipo}.${formato === 'pdf' ? 'pdf' : 'xlsx'}`
    a.click()
    URL.revokeObjectURL(url)
  }

  const resumenEntries = informe ? Object.entries(informe).filter(([k]) => !RESUMEN_KEYS.has(k)) : []
  const detalle = informe?.detalle ?? []
  const columnas =
    detalle.length > 0
      ? Object.keys(detalle[0]).map((key) => ({ key, label: key.replace(/_/g, ' ') }))
      : []

  return (
    <div className="flex flex-col gap-gp-lg">
      <div>
        <h1 className="text-headline-xl text-on-background">Informes</h1>
        <p className="text-body-lg text-on-surface-variant mt-1">Genera informes y resúmenes con IA.</p>
      </div>

      <form onSubmit={handleGenerar} className="bg-surface-container-lowest border border-outline-variant rounded-xl p-gp-md flex flex-wrap items-end gap-gp-md">
        <Field label="Tipo" htmlFor="informe-tipo">
          <SelectInput id="informe-tipo" value={tipo} onChange={(e) => setTipo(e.target.value)}>
            {TIPOS.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </SelectInput>
        </Field>
        <Field label="Desde" htmlFor="informe-desde">
          <TextInput id="informe-desde" type="date" required value={fechaInicio} onChange={(e) => setFechaInicio(e.target.value)} />
        </Field>
        <Field label="Hasta" htmlFor="informe-hasta">
          <TextInput id="informe-hasta" type="date" required value={fechaFin} onChange={(e) => setFechaFin(e.target.value)} />
        </Field>
        {usuario.rol === 'admin' && (
          <Field label="Sede" htmlFor="informe-sede">
            <SelectInput id="informe-sede" value={sedeId} onChange={(e) => setSedeId(e.target.value)}>
              <option value="">Todas</option>
              {sedes.map((sede) => (
                <option key={sede.id} value={sede.id}>
                  {sede.nombre}
                </option>
              ))}
            </SelectInput>
          </Field>
        )}
        <Button type="submit" disabled={cargando} className="mb-gp-md">
          {cargando ? 'Generando…' : 'Generar informe'}
        </Button>
      </form>

      {error && <p className="text-error">{error}</p>}

      {informe && (
        <>
          <div className="flex flex-wrap gap-gp-md items-center justify-between">
            <div className="flex flex-wrap gap-gp-md">
              {resumenEntries.map(([key, value]) => (
                <div key={key} className="bg-surface-container-lowest border border-outline-variant rounded-lg p-gp-md min-w-[140px]">
                  <p className="text-label-sm text-on-surface-variant uppercase">{key.replace(/_/g, ' ')}</p>
                  <p className="text-headline-md text-on-surface">{typeof value === 'number' ? value.toLocaleString('es-ES') : String(value)}</p>
                </div>
              ))}
            </div>
            <div className="flex gap-2">
              <Button variant="secondary" icon="auto_awesome" onClick={handleResumenIA} disabled={generandoResumen}>
                {generandoResumen ? 'Generando…' : 'Resumen IA'}
              </Button>
              <Button variant="secondary" icon="picture_as_pdf" onClick={() => handleExportar('pdf')}>
                PDF
              </Button>
              <Button variant="secondary" icon="grid_on" onClick={() => handleExportar('excel')}>
                Excel
              </Button>
            </div>
          </div>

          {informe.resumen_ia && (
            <div className="bg-surface-container-low border border-outline-variant rounded-lg p-gp-md">
              <h3 className="text-label-sm text-on-surface-variant uppercase mb-2">Resumen generado por IA</h3>
              <p className="text-body-md text-on-surface whitespace-pre-wrap">{informe.resumen_ia}</p>
            </div>
          )}

          {columnas.length > 0 && <DataTable rowKey={columnas[0].key} rows={detalle} columns={columnas} />}
        </>
      )}
    </div>
  )
}
