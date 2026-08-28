import { useEffect, useRef, useState } from 'react'
import * as asistenteService from '../services/asistenteService'
import WizardBorrador from '../components/WizardBorrador/WizardBorrador'

function mensajeErrorApi(error, mensajePorDefecto, mensaje503 = 'El asistente no está disponible en este momento. Inténtalo de nuevo más tarde.') {
  if (error.response?.status === 503) {
    return mensaje503
  }
  return mensajePorDefecto
}

export default function AsistentePage() {
  const [mensajes, setMensajes] = useState([])
  const [cargandoHistorial, setCargandoHistorial] = useState(true)
  const [texto, setTexto] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [errorChat, setErrorChat] = useState(null)

  const [enviandoBorrador, setEnviandoBorrador] = useState(false)
  const [errorBorrador, setErrorBorrador] = useState(null)
  const [borradorCreado, setBorradorCreado] = useState(null)

  const finRef = useRef(null)

  useEffect(() => {
    asistenteService
      .obtenerHistorial()
      .then(setMensajes)
      .catch(() => setErrorChat('No se pudo cargar el historial del chat.'))
      .finally(() => setCargandoHistorial(false))
  }, [])

  useEffect(() => {
    finRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [mensajes])

  async function handleEnviarMensaje(event) {
    event.preventDefault()
    const contenido = texto.trim()
    if (!contenido || enviando) return
    setTexto('')
    setErrorChat(null)
    setEnviando(true)
    setMensajes((prev) => [...prev, { id: `local-${Date.now()}`, rol: 'socio', contenido, fecha: new Date().toISOString() }])
    try {
      const respuesta = await asistenteService.enviarMensaje(contenido)
      setMensajes((prev) => [...prev, respuesta])
    } catch (error) {
      setErrorChat(mensajeErrorApi(error, 'No se pudo enviar el mensaje.'))
    } finally {
      setEnviando(false)
    }
  }

  async function handleCompletarWizard(respuestas) {
    setEnviandoBorrador(true)
    setErrorBorrador(null)
    try {
      const borrador = await asistenteService.solicitarBorrador(respuestas)
      setBorradorCreado(borrador)
    } catch (error) {
      setErrorBorrador(
        mensajeErrorApi(
          error,
          'No se pudo generar el borrador. Inténtalo de nuevo.',
          'El asistente de IA no está disponible en este momento para generar tu borrador. Tus respuestas no se han perdido: puedes volver a intentarlo en unos minutos.',
        ),
      )
    } finally {
      setEnviandoBorrador(false)
    }
  }

  return (
    <div className="py-8 md:py-16 flex flex-col gap-10">
      <section className="flex flex-col gap-2">
        <p className="text-primary-fixed uppercase tracking-widest text-xs font-bold">IA</p>
        <h1 className="font-display text-4xl md:text-6xl text-on-surface uppercase tracking-tighter">Asistente</h1>
        <p className="text-on-surface-variant mt-1">
          Pregunta dudas sobre tu membresía o clases, o pide un borrador de rutina/plan nutricional para que tu entrenador lo revise.
        </p>
      </section>

      <section className="glass-card rounded-xl p-4 md:p-6 flex flex-col gap-4">
        <h2 className="font-display text-2xl text-on-surface flex items-center gap-2">
          <span className="material-symbols-outlined text-primary-fixed">smart_toy</span>
          Chat
        </h2>

        <div className="flex flex-col gap-3 max-h-[28rem] overflow-y-auto pr-1">
          {cargandoHistorial && <p className="text-on-surface-variant">Cargando historial…</p>}
          {!cargandoHistorial && mensajes.length === 0 && (
            <p className="text-on-surface-variant">Todavía no has hablado con el asistente. Escribe tu primera pregunta abajo.</p>
          )}
          {mensajes.map((m) => (
            <div key={m.id} className={`flex ${m.rol === 'socio' ? 'justify-end' : 'justify-start'}`}>
              <div
                className={`max-w-[80%] rounded-xl px-4 py-2 text-sm ${
                  m.rol === 'socio' ? 'bg-primary-fixed text-on-primary-fixed' : 'bg-surface-container-high text-on-surface'
                }`}
              >
                {m.contenido}
              </div>
            </div>
          ))}
          <div ref={finRef} />
        </div>

        {errorChat && <p className="text-error text-sm">{errorChat}</p>}

        <form onSubmit={handleEnviarMensaje} className="flex gap-2">
          <input
            type="text"
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            placeholder="Escribe tu mensaje…"
            disabled={enviando}
            className="flex-1 rounded-lg border border-outline-variant bg-surface px-4 py-2 text-on-surface outline-none focus:border-primary-fixed disabled:opacity-60"
          />
          <button
            type="submit"
            disabled={enviando || !texto.trim()}
            className="px-4 py-2 rounded-lg bg-primary-fixed text-on-primary-fixed font-bold disabled:opacity-60"
          >
            {enviando ? 'Enviando…' : 'Enviar'}
          </button>
        </form>
      </section>

      <section className="glass-card rounded-xl p-4 md:p-6 flex flex-col gap-4">
        <h2 className="font-display text-2xl text-on-surface flex items-center gap-2">
          <span className="material-symbols-outlined text-primary-fixed">draft</span>
          Solicitar un borrador
        </h2>
        <p className="text-sm text-on-surface-variant">
          El asistente genera un borrador de rutina o plan nutricional según tu edad, tu objetivo y tu membresía. Tu entrenador debe
          revisarlo y aprobarlo antes de que se active.
        </p>

        {borradorCreado ? (
          <div className="rounded-lg border border-primary-fixed bg-primary-fixed/10 px-4 py-4 flex flex-col gap-2">
            <p className="text-on-surface font-bold">Borrador solicitado correctamente.</p>
            <p className="text-sm text-on-surface-variant">
              Esto es un borrador generado por IA, pendiente de revisión profesional. Tu entrenador lo revisará antes de activarlo.
            </p>
          </div>
        ) : (
          <>
            {errorBorrador && <p className="text-error text-sm">{errorBorrador}</p>}
            <WizardBorrador onCompletar={enviandoBorrador ? undefined : handleCompletarWizard} />
          </>
        )}
      </section>
    </div>
  )
}
