const OPCIONES_EQUIPAMIENTO = [
  { valor: 'gimnasio_completo', etiqueta: 'Gimnasio completo' },
  { valor: 'casa_basico', etiqueta: 'Casa (material básico)' },
  { valor: 'sin_material', etiqueta: 'Sin material' },
]

const OPCIONES_PREFERENCIA_ALIMENTARIA = [
  { valor: 'omnivoro', etiqueta: 'Omnívoro' },
  { valor: 'vegetariano', etiqueta: 'Vegetariano' },
  { valor: 'vegano', etiqueta: 'Vegano' },
  { valor: 'otro', etiqueta: 'Otro' },
]

function SelectorUnico({ opciones, valorActual, onSeleccionar }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
      {opciones.map((opcion) => {
        const seleccionada = valorActual === opcion.valor
        return (
          <button
            key={opcion.valor}
            type="button"
            onClick={() => onSeleccionar(opcion.valor)}
            aria-pressed={seleccionada}
            className={`rounded-lg border-2 px-4 py-3 text-sm font-bold transition-colors ${
              seleccionada
                ? 'border-primary-fixed bg-primary-fixed/10 text-primary-fixed'
                : 'border-outline-variant text-on-surface-variant hover:border-primary-fixed/50'
            }`}
          >
            {opcion.etiqueta}
          </button>
        )
      })}
    </div>
  )
}

export default function PasoPreferencias({ titulo, respuestas, actualizarRespuestas }) {
  const esRutina = respuestas.tipo_borrador === 'rutina'

  return (
    <div className="py-6 flex flex-col gap-4">
      <h3 className="font-display text-xl text-on-surface">{titulo}</h3>

      {esRutina ? (
        <>
          <label className="flex flex-col gap-1">
            <span className="text-xs uppercase tracking-widest text-on-surface-variant">Días disponibles a la semana</span>
            <input
              type="number"
              min={1}
              max={7}
              value={respuestas.dias_disponibles_semana}
              onChange={(e) => actualizarRespuestas({ dias_disponibles_semana: e.target.value })}
              className="bg-surface-container border-0 border-b-2 border-white/10 text-tertiary px-4 py-3 focus:ring-0 focus:outline-none input-energetic transition-colors rounded-t-lg"
            />
          </label>

          <div className="flex flex-col gap-2">
            <p className="text-xs uppercase tracking-widest text-on-surface-variant">Equipamiento disponible</p>
            <SelectorUnico
              opciones={OPCIONES_EQUIPAMIENTO}
              valorActual={respuestas.equipamiento}
              onSeleccionar={(valor) => actualizarRespuestas({ equipamiento: valor })}
            />
          </div>

          <label className="flex flex-col gap-1">
            <span className="text-xs uppercase tracking-widest text-on-surface-variant">
              Lesiones o zonas a evitar — opcional
            </span>
            <input
              type="text"
              value={respuestas.lesiones_zonas_evitar}
              onChange={(e) => actualizarRespuestas({ lesiones_zonas_evitar: e.target.value })}
              className="bg-surface-container border-0 border-b-2 border-white/10 text-tertiary px-4 py-3 focus:ring-0 focus:outline-none input-energetic transition-colors rounded-t-lg"
            />
          </label>
        </>
      ) : (
        <>
          <div className="flex flex-col gap-2">
            <p className="text-xs uppercase tracking-widest text-on-surface-variant">Preferencia alimentaria</p>
            <SelectorUnico
              opciones={OPCIONES_PREFERENCIA_ALIMENTARIA}
              valorActual={respuestas.preferencia_alimentaria}
              onSeleccionar={(valor) => actualizarRespuestas({ preferencia_alimentaria: valor })}
            />
          </div>

          <label className="flex flex-col gap-1">
            <span className="text-xs uppercase tracking-widest text-on-surface-variant">Comidas al día</span>
            <input
              type="number"
              min={2}
              max={6}
              value={respuestas.comidas_al_dia}
              onChange={(e) => actualizarRespuestas({ comidas_al_dia: e.target.value })}
              className="bg-surface-container border-0 border-b-2 border-white/10 text-tertiary px-4 py-3 focus:ring-0 focus:outline-none input-energetic transition-colors rounded-t-lg"
            />
          </label>

          <label className="flex flex-col gap-1">
            <span className="text-xs uppercase tracking-widest text-on-surface-variant">Alimentos a excluir — opcional</span>
            <input
              type="text"
              value={respuestas.alimentos_excluir}
              onChange={(e) => actualizarRespuestas({ alimentos_excluir: e.target.value })}
              className="bg-surface-container border-0 border-b-2 border-white/10 text-tertiary px-4 py-3 focus:ring-0 focus:outline-none input-energetic transition-colors rounded-t-lg"
            />
          </label>
        </>
      )}
    </div>
  )
}
