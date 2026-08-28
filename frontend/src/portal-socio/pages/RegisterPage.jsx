import { useEffect, useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import * as sedesService from '../services/sedesService'

export default function RegisterPage() {
  const { autenticado, registrar, cargando } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmacion, setConfirmacion] = useState('')
  const [sedeId, setSedeId] = useState('')
  const [sedes, setSedes] = useState([])
  const [error, setError] = useState(null)

  useEffect(() => {
    sedesService
      .listarSedesPublico()
      .then(setSedes)
      .catch(() => setError('No se pudieron cargar las sedes disponibles.'))
  }, [])

  if (autenticado) {
    return <Navigate to="/" replace />
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError(null)

    if (password.length < 8) {
      setError('La contraseña debe tener al menos 8 caracteres.')
      return
    }
    if (password !== confirmacion) {
      setError('Las contraseñas no coinciden.')
      return
    }
    if (!sedeId) {
      setError('Selecciona tu sede.')
      return
    }

    try {
      await registrar(email, password, sedeId)
      navigate('/', { replace: true })
    } catch (err) {
      if (err.response?.status === 409) {
        setError('Ya existe una cuenta con ese correo.')
      } else {
        setError('No se pudo crear la cuenta. Inténtalo de nuevo.')
      }
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden">
      <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-0 w-full h-1/2 bg-surface-container-lowest skew-bg -mt-10" />
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-primary-fixed/5 rounded-full blur-[100px]" />
      </div>

      <main className="w-full max-w-md px-4 md:px-0 z-10 relative">
        <div className="text-center mb-10">
          <h1 className="font-display text-4xl md:text-6xl italic uppercase tracking-tighter text-primary-fixed mb-2">
            Gesportium
          </h1>
          <p className="text-on-surface-variant">Crea tu cuenta de socio.</p>
        </div>

        <div className="glass-card rounded-xl p-6 w-full">
          <form className="space-y-6" onSubmit={handleSubmit}>
            <div>
              <label className="sr-only" htmlFor="email">
                Correo electrónico
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-on-surface-variant">
                  <span className="material-symbols-outlined text-[20px]">mail</span>
                </div>
                <input
                  id="email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Correo electrónico"
                  className="block w-full pl-10 bg-[#1A1A1A] border-0 border-b-2 border-surface-variant text-on-surface focus:ring-0 input-energetic transition-colors py-3"
                />
              </div>
            </div>

            <div>
              <label className="sr-only" htmlFor="sede">
                Sede
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-on-surface-variant">
                  <span className="material-symbols-outlined text-[20px]">location_on</span>
                </div>
                <select
                  id="sede"
                  required
                  value={sedeId}
                  onChange={(e) => setSedeId(e.target.value)}
                  className="block w-full pl-10 bg-[#1A1A1A] border-0 border-b-2 border-surface-variant text-on-surface focus:ring-0 input-energetic transition-colors py-3 appearance-none"
                >
                  <option value="" disabled>
                    Selecciona tu sede
                  </option>
                  {sedes.map((sede) => (
                    <option key={sede.id} value={sede.id}>
                      {sede.nombre} · {sede.ciudad}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="sr-only" htmlFor="password">
                Contraseña
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-on-surface-variant">
                  <span className="material-symbols-outlined text-[20px]">lock</span>
                </div>
                <input
                  id="password"
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Contraseña (mínimo 8 caracteres)"
                  className="block w-full pl-10 bg-[#1A1A1A] border-0 border-b-2 border-surface-variant text-on-surface focus:ring-0 input-energetic transition-colors py-3"
                />
              </div>
            </div>

            <div>
              <label className="sr-only" htmlFor="confirmacion">
                Confirmar contraseña
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-on-surface-variant">
                  <span className="material-symbols-outlined text-[20px]">lock</span>
                </div>
                <input
                  id="confirmacion"
                  type="password"
                  required
                  value={confirmacion}
                  onChange={(e) => setConfirmacion(e.target.value)}
                  placeholder="Confirmar contraseña"
                  className="block w-full pl-10 bg-[#1A1A1A] border-0 border-b-2 border-surface-variant text-on-surface focus:ring-0 input-energetic transition-colors py-3"
                />
              </div>
            </div>

            {error && <p className="text-error text-sm">{error}</p>}

            <div>
              <button
                type="submit"
                disabled={cargando}
                className="w-full flex justify-center py-3 px-4 rounded text-on-primary-fixed bg-primary-fixed font-display font-bold uppercase tracking-wider hover:shadow-[0_0_20px_rgba(195,244,0,0.3)] hover:scale-[1.02] transition-all duration-200 disabled:opacity-60"
              >
                {cargando ? 'Creando cuenta…' : 'Crear cuenta'}
              </button>
            </div>
          </form>

          <div className="mt-8 text-center">
            <p className="text-on-surface-variant">
              ¿Ya tienes una cuenta?{' '}
              <Link
                to="/login"
                className="font-bold text-primary-fixed hover:text-white transition-colors uppercase ml-1 border-b border-transparent hover:border-white"
              >
                Entrar
              </Link>
            </p>
          </div>
        </div>
      </main>
    </div>
  )
}
