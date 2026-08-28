import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import * as asistenteService from '../services/asistenteService'
import * as sociosService from '../services/sociosService'
import * as membresiasService from '../services/membresiasService'
import Button from '../components/Button'
import StatusPill from '../components/StatusPill'

const TIPO_LABEL = { rutina: 'Rutina', plan_nutricional: 'Plan nutricional' }

const SEXO_LABEL = { masculino: 'Masculino', femenino: 'Femenino', prefiero_no_decirlo: 'Prefiero no decirlo' }
const ACTIVIDAD_LABEL = { sedentario: 'Sedentario', activo: 'Activo', muy_activo: 'Muy activo' }
const EQUIPAMIENTO_LABEL = { gimnasio_completo: 'Gimnasio completo', casa_basico: 'Casa (material básico)', sin_material: 'Sin material' }
const PREFERENCIA_ALIMENTARIA_LABEL = { omnivoro: 'Omnívoro', vegetariano: 'Vegetariano', vegano: 'Vegano', otro: 'Otro' }
const OBJETIVO_LABEL = {
  perder_peso: 'Perder peso',
  ganar_masa_muscular: 'Ganar masa muscular',
  mantenimiento: 'Mantenimiento',
  rendimiento_deportivo: 'Rendimiento deportivo',
  salud_general: 'Salud general',
}

// Espeja backend/app/modules/asistente_ia/service.py::calcular_edad
function calcularEdad(fechaNacimientoIso) {
  const hoy = new Date()
  const nacimiento = new Date(fechaNacimientoIso)
  let edad = hoy.getFullYear() - nacimiento.getFullYear()
  const noHaCumplidoAun =
    hoy.getMonth() < nacimiento.getMonth() || (hoy.getMonth() === nacimiento.getMonth() && hoy.getDate() < nacimiento.getDate())
  if (noHaCumplidoAun) edad -= 1
  return edad
}

function Dato({ label, valor }) {
  return (
    <div>
      <p className="text-label-sm text-on-surface-variant uppercase">{label}</p>
      <p className="text-body-md text-on-surface">{valor ?? '—'}</p>
    </div>
  )
}

// Panel izquierdo: datos estructurados del socio (spec 016, "Vista del entrenador").
// `edad`/`tipo_membresia` no están en `datos_cuestionario` (viven en el perfil del
// socio, no en el wizard) y llegan aparte via `perfil`.
function DatosCuestionario({ borrador, perfil }) {
  const datos = borrador.datos_cuestionario
  const esRutina = borrador.tipo === 'rutina'

  return (
    <div className="border border-outline-variant/60 rounded-lg p-gp-sm grid grid-cols-1 sm:grid-cols-2 gap-gp-sm">
      <Dato label="Edad" valor={perfil?.edad != null ? `${perfil.edad} años` : null} />
      <Dato label="Membresía" valor={perfil?.tipoMembresia} />
      <Dato label="Sexo" valor={SEXO_LABEL[datos.sexo] ?? datos.sexo} />
      <Dato label="Peso" valor={datos.peso_kg != null ? `${datos.peso_kg} kg` : null} />
      <Dato label="Altura" valor={datos.altura_cm != null ? `${datos.altura_cm} cm` : null} />
      {esRutina ? (
        <>
          <Dato label="Nivel de actividad" valor={ACTIVIDAD_LABEL[datos.nivel_actividad_actual] ?? datos.nivel_actividad_actual} />
          <Dato label="Días disponibles/semana" valor={datos.dias_disponibles_semana} />
          <Dato label="Equipamiento" valor={EQUIPAMIENTO_LABEL[datos.equipamiento] ?? datos.equipamiento} />
          <Dato label="Lesiones o zonas a evitar" valor={datos.lesiones_zonas_evitar || 'Ninguna'} />
        </>
      ) : (
        <>
          <Dato label="Restricciones médicas" valor={datos.restricciones_medicas || 'Ninguna'} />
          <Dato
            label="Preferencia alimentaria"
            valor={PREFERENCIA_ALIMENTARIA_LABEL[datos.preferencia_alimentaria] ?? datos.preferencia_alimentaria}
          />
          <Dato label="Comidas al día" valor={datos.comidas_al_dia} />
          <Dato label="Alimentos a excluir" valor={datos.alimentos_excluir || 'Ninguno'} />
        </>
      )}
      <Dato label="Objetivo principal" valor={OBJETIVO_LABEL[datos.objetivo_principal] ?? datos.objetivo_principal} />
      <Dato label="Detalle del objetivo" valor={datos.objetivo_detalle || 'Sin detalle'} />
    </div>
  )
}

// Panel derecho: borrador generado por el asistente, editable en pantalla por el
// entrenador. El guardado real (PATCH /asistente/borradores/{id}) llega en T19;
// por ahora solo mantiene el texto editado en estado local propio por borrador.
function EditorBorrador({ texto, onCambiar }) {
  return (
    <textarea
      value={texto}
      onChange={(e) => onCambiar(e.target.value)}
      rows={10}
      spellCheck={false}
      className="w-full rounded-lg border border-outline-variant bg-surface px-3 py-2 text-body-md text-on-surface font-mono outline-none focus:border-primary"
    />
  )
}

export default function BorradoresPendientesPage() {
  const [borradores, setBorradores] = useState([])
  const [sociosPorId, setSociosPorId] = useState(new Map())
  const [perfilesPorSocioId, setPerfilesPorSocioId] = useState(new Map())
  const [borradoresEditados, setBorradoresEditados] = useState({})
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState(null)
  const [procesando, setProcesando] = useState(null)
  const [motivos, setMotivos] = useState({})
  const [erroresEdicion, setErroresEdicion] = useState({})

  function cargar() {
    setCargando(true)
    setError(null)
    return Promise.all([asistenteService.listarBorradoresPendientes(), sociosService.listarSocios(), membresiasService.listarPlanes()])
      .then(([borradoresData, sociosData, planesData]) => {
        setBorradores(borradoresData)
        setSociosPorId(new Map(sociosData.map((s) => [s.id, s])))
        setBorradoresEditados(
          Object.fromEntries(borradoresData.map((b) => [b.id, JSON.stringify(b.contenido, null, 2)])),
        )

        const planNombrePorId = new Map(planesData.map((p) => [p.id, p.nombre]))
        const idsSocios = [...new Set(borradoresData.map((b) => b.socio_id))]
        return Promise.all(idsSocios.map((socioId) => sociosService.obtenerFichaSocio(socioId).catch(() => null))).then((fichas) => {
          const perfiles = new Map()
          idsSocios.forEach((socioId, i) => {
            const ficha = fichas[i]
            if (!ficha) return
            perfiles.set(socioId, {
              edad: ficha.fecha_nacimiento ? calcularEdad(ficha.fecha_nacimiento) : null,
              tipoMembresia: ficha.membresia ? (planNombrePorId.get(ficha.membresia.plan_id) ?? 'Sin membresía activa') : 'Sin membresía activa',
            })
          })
          setPerfilesPorSocioId(perfiles)
        })
      })
      .catch(() => setError('No se pudieron cargar los borradores pendientes.'))
      .finally(() => setCargando(false))
  }

  useEffect(() => {
    cargar()
  }, [])

  async function handleAprobar(borrador) {
    setProcesando(borrador.id)
    setError(null)
    try {
      await asistenteService.aprobarBorrador(borrador.id)
      setBorradores((prev) => prev.filter((b) => b.id !== borrador.id))
    } catch {
      setError('No se pudo aprobar el borrador.')
    } finally {
      setProcesando(null)
    }
  }

  async function handleGuardarYAprobar(borrador) {
    setErroresEdicion((prev) => ({ ...prev, [borrador.id]: null }))
    let contenidoEditado
    try {
      contenidoEditado = JSON.parse(borradoresEditados[borrador.id] ?? '')
    } catch {
      setErroresEdicion((prev) => ({ ...prev, [borrador.id]: 'El contenido no es un JSON válido.' }))
      return
    }
    setProcesando(borrador.id)
    setError(null)
    try {
      await asistenteService.editarBorrador(borrador.id, contenidoEditado)
    } catch {
      setErroresEdicion((prev) => ({ ...prev, [borrador.id]: 'No se pudieron guardar los cambios del borrador.' }))
      setProcesando(null)
      return
    }
    await handleAprobar(borrador)
  }

  async function handleRechazar(borrador) {
    const motivo = (motivos[borrador.id] ?? '').trim()
    if (!motivo) return
    setProcesando(borrador.id)
    setError(null)
    try {
      await asistenteService.rechazarBorrador(borrador.id, motivo)
      setBorradores((prev) => prev.filter((b) => b.id !== borrador.id))
      setMotivos((prev) => {
        const next = { ...prev }
        delete next[borrador.id]
        return next
      })
    } catch {
      setError('No se pudo rechazar el borrador.')
    } finally {
      setProcesando(null)
    }
  }

  return (
    <div className="flex flex-col gap-gp-lg">
      <div>
        <h1 className="text-headline-xl text-on-background">Borradores IA pendientes</h1>
        <p className="text-body-lg text-on-surface-variant mt-1">
          Rutinas y planes nutricionales generados por el asistente para tus socios asignados, a la espera de tu revisión.
        </p>
      </div>

      {error && <p className="text-error">{error}</p>}
      {cargando && <p className="text-on-surface-variant">Cargando…</p>}
      {!cargando && borradores.length === 0 && <p className="text-on-surface-variant">No tienes borradores pendientes de revisión.</p>}

      <div className="flex flex-col gap-gp-md">
        {borradores.map((borrador) => {
          const socio = sociosPorId.get(borrador.socio_id)
          return (
            <div
              key={borrador.id}
              className="bg-surface-container-lowest border border-outline-variant rounded-xl p-gp-md shadow-sm flex flex-col gap-gp-sm"
            >
              <div className="flex justify-between items-start gap-gp-md flex-wrap">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <StatusPill variant="warning">Pendiente</StatusPill>
                    <span className="text-label-sm text-on-surface-variant uppercase">{TIPO_LABEL[borrador.tipo] ?? borrador.tipo}</span>
                  </div>
                  {socio ? (
                    <Link to={`/admin/socios/${socio.id}`} className="text-body-md font-bold text-primary hover:underline">
                      {socio.email}
                    </Link>
                  ) : (
                    <p className="text-body-md font-bold text-on-surface">{borrador.socio_id}</p>
                  )}
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="secondary"
                    disabled={procesando === borrador.id}
                    onClick={() => handleGuardarYAprobar(borrador)}
                  >
                    Guardar cambios y aprobar
                  </Button>
                  <Button disabled={procesando === borrador.id} onClick={() => handleAprobar(borrador)}>
                    Aprobar
                  </Button>
                </div>
              </div>
              <p className="text-label-sm text-on-surface-variant">Borrador generado por IA, pendiente de revisión profesional.</p>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-gp-sm">
                <div className="flex flex-col gap-1">
                  <p className="text-label-sm text-on-surface-variant uppercase">Datos del cuestionario</p>
                  <DatosCuestionario borrador={borrador} perfil={perfilesPorSocioId.get(borrador.socio_id)} />
                </div>
                <div className="flex flex-col gap-1">
                  <p className="text-label-sm text-on-surface-variant uppercase">Borrador</p>
                  <EditorBorrador
                    texto={borradoresEditados[borrador.id] ?? ''}
                    onCambiar={(texto) => setBorradoresEditados((prev) => ({ ...prev, [borrador.id]: texto }))}
                  />
                  {erroresEdicion[borrador.id] && <p className="text-error text-label-sm">{erroresEdicion[borrador.id]}</p>}
                </div>
              </div>
              <div className="flex flex-col sm:flex-row gap-2 items-start sm:items-end">
                <textarea
                  value={motivos[borrador.id] ?? ''}
                  onChange={(e) => setMotivos((prev) => ({ ...prev, [borrador.id]: e.target.value }))}
                  placeholder="Motivo del rechazo (obligatorio)"
                  disabled={procesando === borrador.id}
                  className="flex-1 w-full rounded-lg border border-outline-variant bg-surface px-3 py-2 text-body-md text-on-surface outline-none focus:border-primary disabled:opacity-60"
                  rows={2}
                />
                <Button
                  variant="secondary"
                  disabled={procesando === borrador.id || !(motivos[borrador.id] ?? '').trim()}
                  onClick={() => handleRechazar(borrador)}
                >
                  Rechazar
                </Button>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
