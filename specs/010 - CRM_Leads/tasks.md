# Tasks 010

- [X] T1 — Modelos SQLAlchemy (Lead, InteraccionLead)
      Archivo: backend/app/modules/crm/models.py
      Nota: plan.md y spec.md exigen un rol "comercial" (asignación de leads, "comercial asignado" como rol de API) que no existía en el proyecto (ROLES en identidad/models.py solo tenía admin/gestor_sede/entrenador/socio). Se añadió "comercial" a ROLES, al `Literal` `Rol` de identidad/schemas.py y a la lista de roles que admin/gestor_sede pueden dar de alta en `/auth/register` — extensión mínima y necesaria del módulo 001, no una decisión de diseño nueva.
- [X] T2 — Migración Alembic
      Archivo: backend/alembic/versions/8a2cdb12e0c1_crm_leads.py
- [X] T3 — Schemas Pydantic
      Archivo: backend/app/modules/crm/schemas.py
- [X] T4 — Endpoints CRUD de leads
      Archivos: backend/app/modules/crm/router.py, service.py
      Nota: POST /leads es público (sin dependencia de auth), tal y como indica plan.md ("público, admin, gestor_sede" — público ya cubre a cualquier rol). GET /leads filtra por rol: admin ve todos, gestor_sede los de su sede, comercial solo los que tiene asignados (comercial_id). PUT /leads/{id} permite editar `estado` (todos los roles con acceso al lead) y `comercial_id` (solo admin/gestor_sede) — el comercial asignado puede cambiar el estado pero no reasignar el lead a otro comercial.
- [X] T5 — Endpoint registro de interacciones
      Archivo: backend/app/modules/crm/router.py (POST /leads/{id}/interacciones)
      Nota: restringido al comercial asignado al lead (comercial_id == usuario.id), siguiendo literalmente la columna de rol de plan.md.
- [X] T6 — Endpoint conversión a socio (reutiliza service de 001/003)
      Archivo: backend/app/modules/crm/router.py, service.py (`convertir_a_socio`)
      Nota: el modelo `Socio` (003) exige campos NOT NULL que no existen en `Lead` (fecha_nacimiento, dirección, contacto de emergencia) — el lead solo capta nombre/email/teléfono/sede/origen. Como spec.md no puede exigir simultáneamente "datos automáticos del lead" y campos que el lead nunca captura, se resolvió pidiendo esos campos adicionales en el body de `POST /leads/{id}/convertir` (schema `LeadConvertir`), igual que otras ambigüedades de implementación resueltas sin bloquear (p. ej. la auth de tótem del módulo 009).
      Nota: la conversión reutiliza `identidad.service.crear_usuario` (001) y `socios.service.crear_socio` (003) — no duplica su lógica. Como el lead no aporta contraseña, se genera una temporal aleatoria (`secrets.token_urlsafe`); el socio la restablece vía `/auth/forgot-password` (001), ya existente.
      Nota: un lead ya convertido no puede volver a convertirse (409); intentar convertir con un email que ya tiene un `Socio` asociado también devuelve 409.
- [X] T7 — Validación de email duplicado en conversión
      Archivo: backend/app/modules/crm/service.py (`convertir_a_socio`)
      Nota: si ya existe un `Usuario` con ese email, se reutiliza (no se crea uno nuevo) — cumple el criterio de aceptación "la conversión no duplica datos si el email ya existe como usuario".
- [X] T8 — Tests de integración
      Archivo: backend/tests/modules/test_crm.py
