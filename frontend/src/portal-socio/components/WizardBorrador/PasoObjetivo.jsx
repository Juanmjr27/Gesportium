const OPCIONES_OBJETIVO = [
  { valor: 'perder_peso', etiqueta: 'Perder peso' },
  { valor: 'ganar_masa_muscular', etiqueta: 'Ganar masa muscular' },
  { valor: 'mantenimiento', etiqueta: 'Mantenimiento' },
  { valor: 'rendimiento_deportivo', etiqueta: 'Rendimiento deportivo' },
  { valor: 'salud_general', etiqueta: 'Salud general' },
]

export default function PasoObjetivo({ titulo, respuestas, actualizarRespuestas }) {
  return (
    <div className="py-6 flex flex-col gap-4">
      <h3 className="font-display text-xl text-on-surface">{titulo}</h3>

      <div className="flex flex-col gap-2">
        <p className="text-xs uppercase tracking-widest text-on-surface-variant">Objetivo principal</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {OPCIONES_OBJETIVO.map((opcion) => {
            const seleccionada = respuestas.objetivo_principal === opcion.valor
            return (
              <button
                key={opcion.valor}
                type="button"
                onClick={() => actualizarRespuestas({ objetivo_principal: opcion.valor })}
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
      </div>

      <label className="flex flex-col gap-1">
        <span className="text-xs uppercase tracking-widest text-on-surface-variant">
          Detalle del objetivo (p. ej. "preparar una carrera en 3 meses") — opcional
        </span>
        <textarea
          maxLength={280}
          rows={3}
          value={respuestas.objetivo_detalle}
          onChange={(e) => actualizarRespuestas({ objetivo_detalle: e.target.value })}
          className="bg-surface-container border-0 border-b-2 border-white/10 text-tertiary px-4 py-3 focus:ring-0 focus:outline-none input-energetic transition-colors rounded-t-lg resize-none"
        />
      </label>
    </div>
  )
}
