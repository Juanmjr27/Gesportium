import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

const NAV_ITEMS = [
  { to: '/admin', label: 'Dashboard', icon: 'dashboard', end: true, roles: ['admin', 'gestor_sede', 'entrenador'] },
  { to: '/admin/sedes', label: 'Sedes', icon: 'location_on', roles: ['admin'] },
  { to: '/admin/socios', label: 'Socios', icon: 'group', roles: ['admin', 'gestor_sede', 'entrenador'] },
  { to: '/admin/membresias', label: 'Membresías', icon: 'card_membership', roles: ['admin', 'gestor_sede'] },
  { to: '/admin/clases', label: 'Clases', icon: 'event_repeat', roles: ['admin', 'gestor_sede', 'entrenador'] },
  { to: '/admin/entrenadores', label: 'Entrenadores', icon: 'fitness_center', roles: ['admin', 'gestor_sede'] },
  { to: '/admin/borradores-ia', label: 'Borradores IA', icon: 'smart_toy', roles: ['entrenador'] },
  { to: '/admin/pagos', label: 'Pagos', icon: 'payments', roles: ['admin', 'gestor_sede'] },
  { to: '/admin/leads', label: 'Leads', icon: 'leaderboard', roles: ['admin', 'gestor_sede'] },
  { to: '/admin/informes', label: 'Informes', icon: 'assessment', roles: ['admin', 'gestor_sede'] },
]

const ROL_LABEL = {
  admin: 'Administrador',
  gestor_sede: 'Gestor de sede',
  entrenador: 'Entrenador',
}

export default function AdminShell() {
  const { usuario, cerrarSesion } = useAuth()
  const items = NAV_ITEMS.filter((item) => item.roles.includes(usuario.rol))

  return (
    <div className="panel-admin flex min-h-screen">
      <nav className="hidden md:flex fixed left-0 top-0 h-full w-sidebar-width bg-inverse-surface flex-col py-gp-lg px-gp-md z-50">
        <div className="flex items-center gap-3 mb-gp-xl px-gp-sm">
          <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center text-on-primary font-bold">
            G
          </div>
          <div>
            <h1 className="text-headline-lg text-on-primary-fixed">Gesportium</h1>
            <p className="text-label-sm text-on-surface-variant uppercase">Facility Manager</p>
          </div>
        </div>
        <ul className="flex flex-col gap-1 flex-1">
          {items.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded transition-colors ${
                    isActive
                      ? 'border-l-4 border-primary bg-secondary-container/20 text-on-primary-fixed font-bold'
                      : 'border-l-4 border-transparent text-on-surface-variant hover:text-on-surface hover:bg-surface-container-highest'
                  }`
                }
              >
                <span className="material-symbols-outlined">{item.icon}</span>
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
        {usuario.rol === 'admin' && (
          <div className="mt-auto">
            <NavLink
              to="/admin/configuracion"
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded transition-colors ${
                  isActive
                    ? 'border-l-4 border-primary bg-secondary-container/20 text-on-primary-fixed font-bold'
                    : 'border-l-4 border-transparent text-on-surface-variant hover:text-on-surface hover:bg-surface-container-highest'
                }`
              }
            >
              <span className="material-symbols-outlined">settings</span>
              Configuración
            </NavLink>
          </div>
        )}
      </nav>

      <div className="flex-1 md:ml-sidebar-width flex flex-col min-h-screen">
        <header className="flex justify-between items-center h-16 px-gp-lg w-full bg-surface border-b border-outline-variant sticky top-0 z-40">
          <div className="flex items-center gap-gp-md">
            <span className="text-label-sm text-on-surface-variant">
              {ROL_LABEL[usuario.rol]}
              {usuario.rol === 'gestor_sede' ? ' · Sede propia' : ''}
            </span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-body-md text-on-surface-variant hidden sm:inline">{usuario.email}</span>
            <button
              onClick={cerrarSesion}
              className="w-8 h-8 flex items-center justify-center rounded-full text-on-surface-variant hover:bg-surface-container-low transition-all"
              aria-label="Cerrar sesión"
            >
              <span className="material-symbols-outlined">logout</span>
            </button>
          </div>
        </header>

        <main className="p-gp-lg flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
