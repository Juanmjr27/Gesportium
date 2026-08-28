const OPCIONES = [
  { valor: 'rutina', etiqueta: 'Rutina de entrenamiento', icono: 'fitness_center' },
  { valor: 'plan_nutricional', etiqueta: 'Plan nutricional', icono: 'restaurant' },
]

export default function PasoTipo({ titulo, respuestas, actualizarRespuestas }) {
  return (
    <div className="py-6 flex flex-col gap-4">
      <h3 className="font-display text-xl text-on-surface">{titulo}</h3>
      <p className="text-sm text-on-surface-variant">
        Elige qué quieres que te prepare el asistente. Esto determina las preguntas de los siguientes pasos.
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {OPCIONES.map((opcion) => {
          const seleccionada = respuestas.tipo_borrador === opcion.valor
          return (
            <button
              key={opcion.valor}
              type="button"
              onClick={() => actualizarRespuestas({ tipo_borrador: opcion.valor })}
              aria-pressed={seleccionada}
              className={`flex flex-col items-center gap-2 rounded-xl border-2 px-4 py-6 transition-colors ${
                seleccionada
                  ? 'border-primary-fixed bg-primary-fixed/10 text-primary-fixed'
                  : 'border-outline-variant text-on-surface-variant hover:border-primary-fixed/50'
              }`}
            >
              <span className="material-symbols-outlined text-3xl">{opcion.icono}</span>
              <span className="font-bold text-sm uppercase tracking-wide">{opcion.etiqueta}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
