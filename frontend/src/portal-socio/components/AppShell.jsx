import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

const NAV_ITEMS = [
  { to: '/', label: 'Home', icon: 'home', end: true },
  { to: '/clases', label: 'Clases', icon: 'calendar_today' },
  { to: '/entrenamiento', label: 'Entrenamiento', icon: 'fitness_center' },
  { to: '/asistente', label: 'Asistente', icon: 'smart_toy' },
  { to: '/pagos', label: 'Pagos', icon: 'payments' },
  { to: '/perfil', label: 'Perfil', icon: 'person' },
]

export default function AppShell() {
  const { cerrarSesion } = useAuth()

  return (
    <div className="min-h-screen pb-24 md:pb-0">
      <header className="fixed top-0 w-full z-50 bg-surface/60 backdrop-blur-md border-b border-white/10">
        <div className="flex justify-between items-center px-4 md:px-16 h-16 w-full max-w-[1280px] mx-auto">
          <span className="material-symbols-outlined text-primary-fixed" style={{ fontVariationSettings: "'FILL' 1" }}>
            fitness_center
          </span>
          <div className="font-display text-xl md:text-2xl italic uppercase tracking-tighter text-primary-fixed">
            Gesportium
          </div>
          <nav className="hidden md:flex items-center gap-6">
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `font-bold text-sm transition-colors ${isActive ? 'text-primary-fixed' : 'text-on-surface-variant hover:text-primary-fixed'}`
                }
              >
                {item.label}
              </NavLink>
            ))}
            <button
              onClick={cerrarSesion}
              className="text-on-surface-variant hover:text-primary-fixed transition-colors text-sm font-bold uppercase"
            >
              Salir
            </button>
          </nav>
          <button
            onClick={cerrarSesion}
            className="md:hidden text-on-surface-variant hover:text-primary-fixed transition-colors"
            aria-label="Cerrar sesión"
          >
            <span className="material-symbols-outlined">logout</span>
          </button>
        </div>
      </header>

      <main className="pt-16 w-full max-w-[1280px] mx-auto px-4 md:px-16 relative z-10">
        <Outlet />
      </main>

      <nav className="md:hidden fixed bottom-0 w-full z-50 rounded-t-full bg-surface/80 backdrop-blur-xl border-t border-white/5 shadow-[0_-4px_20px_rgba(0,0,0,0.5)]">
        <div className="flex justify-around items-center h-20 px-2">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `flex flex-col items-center justify-center transition-colors active:scale-90 duration-200 ${isActive ? 'text-primary-fixed font-bold' : 'text-on-surface-variant hover:text-primary-fixed'}`
              }
            >
              <span className="material-symbols-outlined">{item.icon}</span>
              <span className="text-[12px] mt-1">{item.label}</span>
            </NavLink>
          ))}
        </div>
      </nav>
    </div>
  )
}
