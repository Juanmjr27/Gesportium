import { useCallback, useState } from 'react'
import PasoTipo from './PasoTipo'
import PasoPerfil from './PasoPerfil'
import PasoDatosFisicos from './PasoDatosFisicos'
import PasoPreferencias from './PasoPreferencias'
import PasoObjetivo from './PasoObjetivo'
import PasoResumen from './PasoResumen'

const TOTAL_PASOS = 6

// Registro de pasos del wizard (spec 016, "Cuestionario guiado de solicitud
// de borrador"). Cada entrada asigna su componente real (import +
// asignación a `componente`), sin tocar el resto de este contenedor.
const PASOS = [
  { id: 'tipo', titulo: 'Paso 1: Tipo de borrador', componente: PasoTipo },
  { id: 'perfil', titulo: 'Paso 2: Datos de tu perfil', componente: PasoPerfil },
  { id: 'datos_fisicos', titulo: 'Paso 3: Datos físicos', componente: PasoDatosFisicos },
  { id: 'preferencias', titulo: 'Paso 4: Preferencias', componente: PasoPreferencias },
  { id: 'objetivo', titulo: 'Paso 5: Objetivo', componente: PasoObjetivo },
  { id: 'resumen', titulo: 'Paso 6: Resumen y envío', componente: PasoResumen },
]

// Estado inicial de las respuestas acumuladas por el wizard, agrupando los
// campos de `WizardBorradorRequest` (backend) más los de perfil del paso 1.
const RESPUESTAS_INICIALES = {
  tipo_borrador: 'rutina',
  nombre: '',
  edad: '',
  sexo: '',
  tipo_membresia: '',
  peso_kg: '',
  altura_cm: '',
  nivel_actividad_actual: 'activo',
  restricciones_medicas: '',
  dias_disponibles_semana: '3',
  equipamiento: 'gimnasio_completo',
  lesiones_zonas_evitar: '',
  preferencia_alimentaria: 'omnivoro',
  comidas_al_dia: '3',
  alimentos_excluir: '',
  objetivo_principal: 'mantenimiento',
  objetivo_detalle: '',
}

function enRango(valor, min, max) {
  if (valor === '' || valor === null || valor === undefined) return false
  const numero = Number(valor)
  return !Number.isNaN(numero) && numero >= min && numero <= max
}

// Replica las validaciones de `WizardBorradorRequest` (backend/app/modules/asistente_ia/schemas.py)
// para que el socio nunca llegue al envío final con datos que el backend rechazaría con 422.
function validarPaso(pasoId, respuestas) {
  const esRutina = respuestas.tipo_borrador === 'rutina'

  switch (pasoId) {
    case 'tipo':
      if (!respuestas.tipo_borrador) return 'Elige un tipo de borrador para continuar.'
      return null

    case 'perfil':
      if (!respuestas.fecha_nacimiento_ok) return 'Indica tu fecha de nacimiento para continuar.'
      return null

    case 'datos_fisicos':
      if (!respuestas.sexo) return 'Selecciona tu sexo.'
      if (!enRango(respuestas.peso_kg, 20, 300)) return 'Indica un peso entre 20 y 300 kg.'
      if (!enRango(respuestas.altura_cm, 100, 250)) return 'Indica una altura entre 100 y 250 cm.'
      if (esRutina && !respuestas.nivel_actividad_actual) return 'Selecciona tu nivel de actividad actual.'
      return null

    case 'preferencias':
      if (esRutina) {
        if (!enRango(respuestas.dias_disponibles_semana, 1, 7)) return 'Indica entre 1 y 7 días disponibles a la semana.'
        if (!respuestas.equipamiento) return 'Selecciona el equipamiento disponible.'
      } else {
        if (!respuestas.preferencia_alimentaria) return 'Selecciona tu preferencia alimentaria.'
        if (!enRango(respuestas.comidas_al_dia, 2, 6)) return 'Indica entre 2 y 6 comidas al día.'
      }
      return null

    case 'objetivo':
      if (!respuestas.objetivo_principal) return 'Selecciona un objetivo principal.'
      if ((respuestas.objetivo_detalle ?? '').length > 280) return 'El detalle del objetivo no puede superar los 280 caracteres.'
      return null

    default:
      return null
  }
}

/**
 * Contenedor del wizard guiado de solicitud de borrador (spec 016).
 *
 * Mantiene todas las respuestas del cuestionario en un único objeto que
 * persiste mientras el usuario navega entre pasos, y delega el contenido de
 * cada paso al componente registrado en `PASOS`. Cada paso recibe
 * `respuestas` y `actualizarRespuestas` para leer/escribir su parte del
 * estado compartido, sin que este contenedor conozca sus campos concretos.
 *
 * `onCompletar` se invoca al confirmar el último paso (resumen) con el
 * objeto `respuestas` completo; el llamador decide qué hacer con él (por
 * ejemplo, enviarlo a `POST /asistente/borrador`). Si no se recibe
 * `onCompletar`, el botón final se limita a un console.log.
 */
export default function WizardBorrador({ onCompletar }) {
  const [pasoActual, setPasoActual] = useState(0)
  const [respuestas, setRespuestas] = useState(RESPUESTAS_INICIALES)

  const actualizarRespuestas = useCallback((cambios) => {
    setRespuestas((prev) => ({ ...prev, ...cambios }))
  }, [])

  function irSiguiente() {
    if (validarPaso(PASOS[pasoActual].id, respuestas)) return
    setPasoActual((paso) => Math.min(paso + 1, TOTAL_PASOS - 1))
  }

  function irAtras() {
    setPasoActual((paso) => Math.max(paso - 1, 0))
  }

  function handleFinalizar() {
    if (onCompletar) {
      onCompletar(respuestas)
    } else {
      console.log('Wizard completo (envío real a /asistente/borrador llega en T16):', respuestas)
    }
  }

  const paso = PASOS[pasoActual]
  const PasoActual = paso.componente
  const esUltimoPaso = pasoActual === TOTAL_PASOS - 1
  const errorPaso = esUltimoPaso ? null : validarPaso(paso.id, respuestas)

  return (
    <div className="flex flex-col gap-4">
      <div>
        <div className="flex justify-between text-xs text-on-surface-variant mb-1">
          <span>
            Paso {pasoActual + 1} de {TOTAL_PASOS}
          </span>
          <span>{paso.titulo}</span>
        </div>
        <div className="h-2 rounded-full bg-surface-container-high overflow-hidden">
          <div
            className="h-full bg-primary-fixed transition-all"
            style={{ width: `${((pasoActual + 1) / TOTAL_PASOS) * 100}%` }}
          />
        </div>
      </div>

      <PasoActual titulo={paso.titulo} respuestas={respuestas} actualizarRespuestas={actualizarRespuestas} />

      {errorPaso && <p className="text-error text-sm">{errorPaso}</p>}

      <div className="flex justify-between gap-2 mt-2">
        <button
          type="button"
          onClick={irAtras}
          disabled={pasoActual === 0}
          className="px-4 py-2 rounded-lg border border-outline-variant text-on-surface font-bold disabled:opacity-40"
        >
          Atrás
        </button>

        {esUltimoPaso ? (
          <button
            type="button"
            onClick={handleFinalizar}
            disabled={!onCompletar}
            className="px-4 py-2 rounded-lg bg-primary-fixed text-on-primary-fixed font-bold disabled:opacity-60"
          >
            Solicitar borrador
          </button>
        ) : (
          <button
            type="button"
            onClick={irSiguiente}
            disabled={!!errorPaso}
            className="px-4 py-2 rounded-lg bg-primary-fixed text-on-primary-fixed font-bold disabled:opacity-60"
          >
            Siguiente
          </button>
        )}
      </div>
    </div>
  )
}
