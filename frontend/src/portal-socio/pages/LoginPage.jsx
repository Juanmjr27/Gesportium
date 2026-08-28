import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export default function LoginPage() {
  const { autenticado, iniciarSesion, cargando } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [mostrarPassword, setMostrarPassword] = useState(false)
  const [error, setError] = useState(null)

  if (autenticado) {
    return <Navigate to={location.state?.from ?? '/'} replace />
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError(null)
    try {
      await iniciarSesion(email, password)
      navigate('/', { replace: true })
    } catch (err) {
      if (err.response?.status === 429) {
        setError('Demasiados intentos. Inténtalo de nuevo más tarde.')
      } else {
        setError('Correo o contraseña incorrectos.')
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
          <p className="text-on-surface-variant">Alto rendimiento, unificado.</p>
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
                  name="email"
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
              <label className="sr-only" htmlFor="password">
                Contraseña
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-on-surface-variant">
                  <span className="material-symbols-outlined text-[20px]">lock</span>
                </div>
                <input
                  id="password"
                  name="password"
                  type={mostrarPassword ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Contraseña"
                  className="block w-full pl-10 pr-10 bg-[#1A1A1A] border-0 border-b-2 border-surface-variant text-on-surface focus:ring-0 input-energetic transition-colors py-3"
                />
                <button
                  type="button"
                  onClick={() => setMostrarPassword((v) => !v)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center cursor-pointer text-on-surface-variant hover:text-primary-fixed transition-colors"
                  aria-label={mostrarPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                >
                  <span className="material-symbols-outlined text-[20px]">
                    {mostrarPassword ? 'visibility' : 'visibility_off'}
                  </span>
                </button>
              </div>
            </div>

            {error && <p className="text-error text-sm">{error}</p>}

            <div>
              <button
                type="submit"
                disabled={cargando}
                className="w-full flex justify-center py-3 px-4 rounded text-on-primary-fixed bg-primary-fixed font-display font-bold uppercase tracking-wider hover:shadow-[0_0_20px_rgba(195,244,0,0.3)] hover:scale-[1.02] transition-all duration-200 disabled:opacity-60"
              >
                {cargando ? 'Entrando…' : 'Entrar'}
              </button>
            </div>
          </form>

          <div className="mt-8 text-center">
            <p className="text-on-surface-variant">
              ¿No tienes una cuenta?{' '}
              <Link
                to="/registro"
                className="font-bold text-primary-fixed hover:text-white transition-colors uppercase ml-1 border-b border-transparent hover:border-white"
              >
                Crear cuenta
              </Link>
            </p>
          </div>
        </div>
      </main>
    </div>
  )
}
