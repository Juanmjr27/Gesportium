import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import * as dashboardService from '../services/dashboardService'
import * as sedesService from '../services/sedesService'
import * as sociosService from '../services/sociosService'
import * as clasesService from '../services/clasesService'
import KpiCard from '../components/KpiCard'
import { SelectInput } from '../components/Field'

function rangoSemanaActual() {
  const ahora = new Date()
  const diasDesdeLunes = (ahora.getDay() + 6) % 7
  const inicio = new Date(ahora)
  inicio.setHours(0, 0, 0, 0)
  inicio.setDate(inicio.getDate() - diasDesdeLunes)
  const fin = new Date(inicio)
  fin.setDate(fin.getDate() + 7)
  return [inicio, fin]
}

const KPI_DEFS = [
  { key: 'socios_activos', label: 'Socios activos', icon: 'group', format: (v) => Math.round(v) },
  { key: 'altas_mes', label: 'Altas este mes', icon: 'person_add', format: (v) => Math.round(v) },
  { key: 'bajas_mes', label: 'Bajas este mes', icon: 'person_remove', format: (v) => Math.round(v) },
  { key: 'ingresos_mes', label: 'Ingresos mes', icon: 'payments', format: (v) => `${v.toFixed(2)} €` },
  { key: 'ocupacion_media_clases', label: 'Ocupación media clases', icon: 'pie_chart', format: (v) => `${v.toFixed(0)}%` },
  { key: 'tasa_conversion_leads', label: 'Conversión de leads', icon: 'leaderboard', format: (v) => `${v.toFixed(0)}%` },
]

function TrendFor(kpi) {
  if (kpi.variacion_pct === null || kpi.variacion_pct === undefined) return undefined
  const positive = kpi.variacion_pct >= 0
  return { positive, label: `${positive ? '+' : ''}${kpi.variacion_pct.toFixed(0)}%` }
}

export default function DashboardPage() {
  const { usuario } = useAuth()
  const esEntrenador = usuario.rol === 'entrenador'

  const [sedes, setSedes] = useState([])
  const [sedeId, setSedeId] = useState('')
  const [kpis, setKpis] = useState(null)
  const [error, setError] = useState(null)
  const [totalSocios, setTotalSocios] = useState(null)
  const [totalClasesSemana, setTotalClasesSemana] = useState(null)

  useEffect(() => {
    if (esEntrenador) return
    if (usuario.rol === 'admin') {
      sedesService.listarSedes().then(setSedes).catch(() => {})
    }
  }, [esEntrenador, usuario.rol])

  useEffect(() => {
    if (!esEntrenador) return
    sociosService
      .listarSocios()
      .then((socios) => setTotalSocios(socios.length))
      .catch(() => setTotalSocios(null))
    clasesService
      .listarClases()
      .then((clases) => {
        const [inicioSemana, finSemana] = rangoSemanaActual()
        const enCurso = clases.filter((c) => {
          if (c.estado !== 'activa') return false
          const fecha = new Date(c.fecha_hora)
          return fecha >= inicioSemana && fecha < finSemana
        })
        setTotalClasesSemana(enCurso.length)
      })
      .catch(() => setTotalClasesSemana(null))
  }, [esEntrenador])

  useEffect(() => {
    if (esEntrenador) return
    dashboardService
      .obtenerKpis(sedeId ? { sede_id: sedeId } : undefined)
      .then(setKpis)
      .catch(() => setError('No se pudieron cargar los KPIs.'))
  }, [esEntrenador, sedeId])

  if (esEntrenador) {
    return (
      <div>
        <h2 className="text-headline-xl text-on-background mb-1">Bienvenido</h2>
        <p className="text-body-lg text-on-surface-variant mb-gp-lg">
          Consulta tus socios asignados y las clases que impartes.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-gp-lg">
          <Link
            to="/admin/socios"
            className="bg-surface-container-lowest border border-outline-variant rounded-lg p-gp-lg hover:border-primary transition-colors flex items-center gap-4"
          >
            <span className="material-symbols-outlined text-primary text-3xl">group</span>
            <div>
              <h3 className="text-headline-md text-on-surface">Mis socios</h3>
              <p className="text-body-md text-on-surface-variant">
                {totalSocios === null ? 'Socios que tienes asignados' : `${totalSocios} socio${totalSocios === 1 ? '' : 's'} asignado${totalSocios === 1 ? '' : 's'}`}
              </p>
            </div>
          </Link>
          <Link
            to="/admin/clases"
            className="bg-surface-container-lowest border border-outline-variant rounded-lg p-gp-lg hover:border-primary transition-colors flex items-center gap-4"
          >
            <span className="material-symbols-outlined text-primary text-3xl">event_repeat</span>
            <div>
              <h3 className="text-headline-md text-on-surface">Mis clases</h3>
              <p className="text-body-md text-on-surface-variant">
                {totalClasesSemana === null ? 'Clases que impartes' : `${totalClasesSemana} clase${totalClasesSemana === 1 ? '' : 's'} esta semana`}
              </p>
            </div>
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="mb-gp-lg flex justify-between items-end">
        <div>
          <h2 className="text-headline-xl text-on-surface mb-1">Panel General</h2>
          <p className="text-body-lg text-on-surface-variant">Resumen de métricas clave del negocio.</p>
        </div>
        {usuario.rol === 'admin' && (
          <SelectInput value={sedeId} onChange={(e) => setSedeId(e.target.value)} className="w-56">
            <option value="">Todas las sedes</option>
            {sedes.map((sede) => (
              <option key={sede.id} value={sede.id}>
                {sede.nombre}
              </option>
            ))}
          </SelectInput>
        )}
      </div>

      {error && <p className="text-error mb-gp-md">{error}</p>}

      {kpis && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-gp-lg">
          {KPI_DEFS.map((def) => {
            const kpi = kpis[def.key]
            return (
              <KpiCard
                key={def.key}
                label={def.label}
                icon={def.icon}
                value={def.format(kpi.valor)}
                trend={TrendFor(kpi)}
              />
            )
          })}
        </div>
      )}
    </div>
  )
}
