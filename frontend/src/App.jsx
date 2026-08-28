import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './portal-socio/hooks/useAuth'
import ProtectedRoute from './portal-socio/components/ProtectedRoute'
import AppShell from './portal-socio/components/AppShell'
import LoginPage from './portal-socio/pages/LoginPage'
import RegisterPage from './portal-socio/pages/RegisterPage'
import HomePage from './portal-socio/pages/HomePage'
import ClasesPage from './portal-socio/pages/ClasesPage'
import EntrenamientoPage from './portal-socio/pages/EntrenamientoPage'
import AsistentePage from './portal-socio/pages/AsistentePage'
import PagosPage from './portal-socio/pages/PagosPage'
import PerfilPage from './portal-socio/pages/PerfilPage'

import { AuthProvider as AdminAuthProvider } from './panel-admin/hooks/useAuth'
import AdminProtectedRoute from './panel-admin/components/ProtectedRoute'
import AdminShell from './panel-admin/components/AdminShell'
import AdminLoginPage from './panel-admin/pages/LoginPage'
import AdminDashboardPage from './panel-admin/pages/DashboardPage'
import AdminSedesPage from './panel-admin/pages/SedesPage'
import AdminSociosPage from './panel-admin/pages/SociosPage'
import AdminFichaSocioPage from './panel-admin/pages/FichaSocioPage'
import AdminMembresiasPage from './panel-admin/pages/MembresiasPage'
import AdminClasesPage from './panel-admin/pages/ClasesPage'
import AdminEntrenadoresPage from './panel-admin/pages/EntrenadoresPage'
import AdminBorradoresPendientesPage from './panel-admin/pages/BorradoresPendientesPage'
import AdminPagosPage from './panel-admin/pages/PagosPage'
import AdminLeadsPage from './panel-admin/pages/LeadsPage'
import AdminInformesPage from './panel-admin/pages/InformesPage'
import AdminConfiguracionPage from './panel-admin/pages/ConfiguracionPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/*"
          element={
            <AuthProvider>
              <Routes>
                <Route path="/login" element={<LoginPage />} />
                <Route path="/registro" element={<RegisterPage />} />
                <Route element={<ProtectedRoute />}>
                  <Route element={<AppShell />}>
                    <Route path="/" element={<HomePage />} />
                    <Route path="/clases" element={<ClasesPage />} />
                    <Route path="/entrenamiento" element={<EntrenamientoPage />} />
                    <Route path="/asistente" element={<AsistentePage />} />
                    <Route path="/pagos" element={<PagosPage />} />
                    <Route path="/perfil" element={<PerfilPage />} />
                  </Route>
                </Route>
              </Routes>
            </AuthProvider>
          }
        />

        <Route
          path="/admin/*"
          element={
            <AdminAuthProvider>
              <Routes>
                <Route path="login" element={<AdminLoginPage />} />
                <Route element={<AdminProtectedRoute />}>
                  <Route element={<AdminShell />}>
                    <Route index element={<AdminDashboardPage />} />
                    <Route element={<AdminProtectedRoute roles={['admin']} />}>
                      <Route path="sedes" element={<AdminSedesPage />} />
                      <Route path="configuracion" element={<AdminConfiguracionPage />} />
                    </Route>
                    <Route element={<AdminProtectedRoute roles={['admin', 'gestor_sede', 'entrenador']} />}>
                      <Route path="socios" element={<AdminSociosPage />} />
                      <Route path="socios/:socioId" element={<AdminFichaSocioPage />} />
                      <Route path="clases" element={<AdminClasesPage />} />
                    </Route>
                    <Route element={<AdminProtectedRoute roles={['admin', 'gestor_sede']} />}>
                      <Route path="membresias" element={<AdminMembresiasPage />} />
                      <Route path="entrenadores" element={<AdminEntrenadoresPage />} />
                      <Route path="pagos" element={<AdminPagosPage />} />
                      <Route path="leads" element={<AdminLeadsPage />} />
                      <Route path="informes" element={<AdminInformesPage />} />
                    </Route>
                    <Route element={<AdminProtectedRoute roles={['entrenador']} />}>
                      <Route path="borradores-ia" element={<AdminBorradoresPendientesPage />} />
                    </Route>
                  </Route>
                </Route>
              </Routes>
            </AdminAuthProvider>
          }
        />
      </Routes>
    </BrowserRouter>
  )
}
