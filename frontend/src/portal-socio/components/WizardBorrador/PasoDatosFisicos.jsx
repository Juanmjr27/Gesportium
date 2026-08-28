const OPCIONES_SEXO = [
  { valor: 'masculino', etiqueta: 'Masculino' },
  { valor: 'femenino', etiqueta: 'Femenino' },
  { valor: 'prefiero_no_decirlo', etiqueta: 'Prefiero no decirlo' },
]

const OPCIONES_ACTIVIDAD = [
  { valor: 'sedentario', etiqueta: 'Sedentario' },
  { valor: 'activo', etiqueta: 'Activo' },
  { valor: 'muy_activo', etiqueta: 'Muy activo' },
]

export default function PasoDatosFisicos({ titulo, respuestas, actualizarRespuestas }) {
  const esRutina = respuestas.tipo_borrador === 'rutina'

  return (
    <div className="py-6 flex flex-col gap-4">
      <h3 className="font-display text-xl text-on-surface">{titulo}</h3>

      <div className="flex flex-col gap-2">
        <p className="text-xs uppercase tracking-widest text-on-surface-variant">Sexo</p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {OPCIONES_SEXO.map((opcion) => {
            const seleccionada = respuestas.sexo === opcion.valor
            return (
              <button
                key={opcion.valor}
                type="button"
                onClick={() => actualizarRespuestas({ sexo: opcion.valor })}
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

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <label className="flex flex-col gap-1">
          <span className="text-xs uppercase tracking-widest text-on-surface-variant">Peso (kg)</span>
          <input
            type="number"
            min={20}
            max={300}
            value={respuestas.peso_kg}
            onChange={(e) => actualizarRespuestas({ peso_kg: e.target.value })}
            className="bg-surface-container border-0 border-b-2 border-white/10 text-tertiary px-4 py-3 focus:ring-0 focus:outline-none input-energetic transition-colors rounded-t-lg"
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-xs uppercase tracking-widest text-on-surface-variant">Altura (cm)</span>
          <input
            type="number"
            min={100}
            max={250}
            value={respuestas.altura_cm}
            onChange={(e) => actualizarRespuestas({ altura_cm: e.target.value })}
            className="bg-surface-container border-0 border-b-2 border-white/10 text-tertiary px-4 py-3 focus:ring-0 focus:outline-none input-energetic transition-colors rounded-t-lg"
          />
        </label>
      </div>

      {esRutina ? (
        <div className="flex flex-col gap-2">
          <p className="text-xs uppercase tracking-widest text-on-surface-variant">Nivel de actividad actual</p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {OPCIONES_ACTIVIDAD.map((opcion) => {
              const seleccionada = respuestas.nivel_actividad_actual === opcion.valor
              return (
                <button
                  key={opcion.valor}
                  type="button"
                  onClick={() => actualizarRespuestas({ nivel_actividad_actual: opcion.valor })}
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
      ) : (
        <label className="flex flex-col gap-1">
          <span className="text-xs uppercase tracking-widest text-on-surface-variant">
            Restricciones médicas (alergias, intolerancias, otro) — opcional
          </span>
          <input
            type="text"
            value={respuestas.restricciones_medicas}
            onChange={(e) => actualizarRespuestas({ restricciones_medicas: e.target.value })}
            className="bg-surface-container border-0 border-b-2 border-white/10 text-tertiary px-4 py-3 focus:ring-0 focus:outline-none input-energetic transition-colors rounded-t-lg"
          />
        </label>
      )}
    </div>
  )
}
