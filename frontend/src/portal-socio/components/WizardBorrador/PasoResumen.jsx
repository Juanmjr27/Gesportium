import { useEffect, useState } from 'react'
import { useAuth } from '../../hooks/useAuth'
import * as membresiasService from '../../services/membresiasService'
import * as planesService from '../../services/planesService'

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

const ETIQUETAS_SEXO = {
  masculino: 'Masculino',
  femenino: 'Femenino',
  prefiero_no_decirlo: 'Prefiero no decirlo',
}

const ETIQUETAS_ACTIVIDAD = {
  sedentario: 'Sedentario',
  activo: 'Activo',
  muy_activo: 'Muy activo',
}

const ETIQUETAS_EQUIPAMIENTO = {
  gimnasio_completo: 'Gimnasio completo',
  casa_basico: 'Casa (material básico)',
  sin_material: 'Sin material',
}

const ETIQUETAS_PREFERENCIA_ALIMENTARIA = {
  omnivoro: 'Omnívoro',
  vegetariano: 'Vegetariano',
  vegano: 'Vegano',
  otro: 'Otro',
}

const ETIQUETAS_OBJETIVO = {
  perder_peso: 'Perder peso',
  ganar_masa_muscular: 'Ganar masa muscular',
  mantenimiento: 'Mantenimiento',
  rendimiento_deportivo: 'Rendimiento deportivo',
  salud_general: 'Salud general',
}

function Dato({ etiqueta, valor }) {
  return (
    <div className="rounded-lg border border-outline-variant px-4 py-3">
      <p className="text-xs uppercase tracking-widest text-on-surface-variant mb-1">{etiqueta}</p>
      <p className="text-on-surface font-bold">{valor || '—'}</p>
    </div>
  )
}

export default function PasoResumen({ titulo, respuestas }) {
  const { socio } = useAuth()
  const [tipoMembresia, setTipoMembresia] = useState(null)
  const [cargandoMembresia, setCargandoMembresia] = useState(true)

  useEffect(() => {
    if (!socio) return
    Promise.all([membresiasService.listarMisMembresias(), planesService.listarPlanesPublico().catch(() => [])])
      .then(([membresias, planes]) => {
        const activa = membresias.find((m) => m.estado === 'activa') ?? null
        const plan = activa ? (planes.find((p) => p.id === activa.plan_id) ?? null) : null
        setTipoMembresia(plan?.nombre ?? 'Sin membresía activa')
      })
      .catch(() => setTipoMembresia('Sin membresía activa'))
      .finally(() => setCargandoMembresia(false))
  }, [socio])

  const esRutina = respuestas.tipo_borrador === 'rutina'
  const edad = socio?.fecha_nacimiento ? `${calcularEdad(socio.fecha_nacimiento)} años` : 'Sin registrar'

  return (
    <div className="py-6 flex flex-col gap-4">
      <h3 className="font-display text-xl text-on-surface">{titulo}</h3>
      <p className="text-sm text-on-surface-variant">
        Revisa tus respuestas antes de enviar. Usa "Atrás" para volver a cualquier paso anterior y corregir algo sin perder el resto.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Dato etiqueta="Tipo de borrador" valor={esRutina ? 'Rutina de entrenamiento' : 'Plan nutricional'} />
        <Dato etiqueta="Edad" valor={edad} />
        <Dato etiqueta="Membresía" valor={cargandoMembresia ? 'Cargando…' : tipoMembresia} />
        <Dato etiqueta="Sexo" valor={ETIQUETAS_SEXO[respuestas.sexo]} />
        <Dato etiqueta="Peso" valor={respuestas.peso_kg ? `${respuestas.peso_kg} kg` : ''} />
        <Dato etiqueta="Altura" valor={respuestas.altura_cm ? `${respuestas.altura_cm} cm` : ''} />

        {esRutina ? (
          <>
            <Dato etiqueta="Nivel de actividad actual" valor={ETIQUETAS_ACTIVIDAD[respuestas.nivel_actividad_actual]} />
            <Dato etiqueta="Días disponibles a la semana" valor={respuestas.dias_disponibles_semana} />
            <Dato etiqueta="Equipamiento" valor={ETIQUETAS_EQUIPAMIENTO[respuestas.equipamiento]} />
            <Dato etiqueta="Lesiones o zonas a evitar" valor={respuestas.lesiones_zonas_evitar} />
          </>
        ) : (
          <>
            <Dato etiqueta="Restricciones médicas" valor={respuestas.restricciones_medicas} />
            <Dato etiqueta="Preferencia alimentaria" valor={ETIQUETAS_PREFERENCIA_ALIMENTARIA[respuestas.preferencia_alimentaria]} />
            <Dato etiqueta="Comidas al día" valor={respuestas.comidas_al_dia} />
            <Dato etiqueta="Alimentos a excluir" valor={respuestas.alimentos_excluir} />
          </>
        )}

        <Dato etiqueta="Objetivo principal" valor={ETIQUETAS_OBJETIVO[respuestas.objetivo_principal]} />
        <Dato etiqueta="Detalle del objetivo" valor={respuestas.objetivo_detalle} />
      </div>
    </div>
  )
}
