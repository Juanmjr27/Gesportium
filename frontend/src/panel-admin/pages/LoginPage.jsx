import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export default function LoginPage() {
  const { autenticado, iniciarSesion, cargando } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)

  if (autenticado) {
    return <Navigate to="/admin" replace />
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError(null)
    try {
      await iniciarSesion(email, password)
      navigate('/admin', { replace: true })
    } catch {
      setError('Credenciales incorrectas.')
    }
  }

  return (
    <div className="panel-admin min-h-screen flex items-center justify-center bg-background">
      <div className="w-full max-w-[24rem] bg-surface-container-lowest border border-outline-variant rounded-xl shadow-sm p-gp-lg">
        <div className="flex flex-col items-center mb-gp-lg">
          <div className="w-12 h-12 rounded-full bg-primary flex items-center justify-center text-on-primary font-bold text-headline-md mb-2">
            G
          </div>
          <h1 className="text-headline-lg text-on-surface">Gesportium</h1>
          <p className="text-body-md text-on-surface-variant">Panel de administración</p>
        </div>

        <form className="flex flex-col gap-gp-md" onSubmit={handleSubmit}>
          <div className="flex flex-col gap-1">
            <label className="text-label-sm text-on-surface-variant uppercase" htmlFor="email">
              Correo electrónico
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="rounded border border-outline-variant bg-surface px-gp-sm py-gp-sm text-body-md text-on-surface focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-label-sm text-on-surface-variant uppercase" htmlFor="password">
              Contraseña
            </label>
            <input
              id="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="rounded border border-outline-variant bg-surface px-gp-sm py-gp-sm text-body-md text-on-surface focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all"
            />
          </div>

          {error && <p className="text-error text-sm">{error}</p>}

          <button
            type="submit"
            disabled={cargando}
            className="mt-2 bg-primary text-on-primary font-button text-button py-2 rounded hover:bg-primary-container transition-colors disabled:opacity-60"
          >
            {cargando ? 'Entrando…' : 'Entrar'}
          </button>
        </form>
      </div>
    </div>
  )
}
