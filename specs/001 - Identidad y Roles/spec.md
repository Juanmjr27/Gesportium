# Spec 001 — Identidad y Roles

## Resumen
Sistema de autenticación y autorización de Gesportium. Gestiona quién 
puede entrar al sistema, con qué rol, y qué puede ver/hacer cada rol.

## Roles del sistema
- **admin**: control total, ve y gestiona todas las sedes
- **gestor_sede**: administra una sede concreta (socios, clases, pagos)
- **entrenador**: gestiona sus clases y ve sus socios asignados
- **socio**: accede a su perfil, reserva clases, ve su membresía y pagos
- **comercial**: gestiona leads y su seguimiento comercial (módulo 010); no accede a datos operativos de socios (clases, rutinas, pagos)

## Requisitos funcionales
1. Registro de usuarios:
   - admin y gestor_sede pueden crear cuentas de entrenador, socio y comercial
   - Los socios también pueden registrarse públicamente desde el portal
2. Login con email + contraseña → devuelve token de sesión (JWT)
3. Recuperación de contraseña vía email
4. Cierre de sesión (invalidación de token)
5. Cada socio y entrenador pertenece a una sede concreta; admin ve todas
6. Cada endpoint de la API valida el rol del usuario antes de responder
7. Auditoría: se registra cada intento de login (éxito/fallo) con 
   fecha, hora e IP

## Criterios de aceptación
- Un socio no puede acceder a datos de otra sede
- Un entrenador no puede ver socios que no le estén asignados
- Un token expirado no permite ninguna acción
- Tras 5 intentos fallidos de login, se bloquea temporalmente la cuenta

## Fuera de alcance en esta feature
- Login social (Google/Facebook)
- Autenticación de dos factores (2FA)