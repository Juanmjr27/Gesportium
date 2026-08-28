import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export default function ProtectedRoute({ roles }) {
  const { autenticado, usuario } = useAuth()

  if (!autenticado) {
    return <Navigate to="/admin/login" replace />
  }

  if (roles && !roles.includes(usuario.rol)) {
    return <Navigate to="/admin" replace />
  }

  return <Outlet />
}
