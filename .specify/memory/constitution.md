# Constitution — Gesportium (ERP para cadena de gimnasios)

## Propósito
Sistema de gestión para una cadena de gimnasios: panel de administración 
(gestores de la cadena/sedes) y portal de socios (reserva de clases, 
gestión de membresía).

## Stack tecnológico (no negociable salvo revisión explícita)
- Backend/API: Python 3.12 + FastAPI
- ORM y migraciones: SQLAlchemy + Alembic
- Base de datos: PostgreSQL
- Frontend: React + JavaScript (JSX)
- Autenticación: JWT (roles: admin, gestor de sede, entrenador, socio, 
  comercial)
- IA local: Ollama 

## Principios de desarrollo
1. Spec-first: ninguna implementación empieza sin spec.md aprobado
2. Modularidad: cada dominio (socios, membresías, clases, sedes, 
   entrenadores, pagos, informes) es un módulo independiente
3. Tipado estricto: Pydantic en API (el backend mantiene tipado 
   estricto; el frontend usa JavaScript sin tipado estático)
4. Testing: cada endpoint requiere al menos un test de integración
5. API-first: frontend consume vía contrato OpenAPI, sin acceso 
   directo a BD
6. Seguridad: contraseñas hasheadas, JWT con expiración, control de 
   acceso por rol
7. Trazabilidad: acciones sensibles (altas/bajas de socios, pagos, 
   cambios de membresía) quedan registradas con usuario, fecha y 
   acción para auditoría

## Convenciones de código
- Backend: PEP8, endpoints en inglés, comentarios en español
- Frontend: componentes funcionales, hooks
- Commits: Conventional Commits

## Fuera de alcance en la v1
- Pasarela de pago real (se simula)
- App móvil nativa (solo web responsive)

## Visión y alcance del producto
Gesportium debe concebirse como un producto SaaS real, vendible a cadenas de gimnasios, con profundidad funcional comparable a ERPs comerciales del sector 
(ej. Mindbody, Glofox, Virtuagym).

Cada módulo debe implementarse con la funcionalidad completa esperada 
en un producto profesional (validaciones, casos borde, permisos 
granulares, notificaciones, historial/auditoría), no con la versión 
mínima que "simplemente funciona".

El desarrollo sigue siendo incremental (feature por feature vía SDD), 
pero cada feature debe planificarse pensando en el producto final, 
evitando decisiones que limiten la escalabilidad futura.

## Gobernanza
Versión: 1.2.0
Ratificada: 2026-07-28
Última modificación: 2026-08-14

Cualquier cambio a los principios de esta Constitution requiere 
justificación explícita y actualización de la versión.

### Historial de cambios
- 1.2.0 (2026-08-14): se corrige el stack de frontend de "React + 
  TypeScript" a "React + JavaScript (JSX)", y se ajusta el principio 
  de tipado estricto para aplicarse solo al backend (Pydantic). El 
  frontend se implementó en JavaScript desde los módulos 015 
  (Portal de socio) y 017 (Panel de administración) sin que se 
  detectara la discrepancia con la Constitution hasta el análisis 
  de coherencia de módulos 001-017 (`/speckit.analyze`). Esta 
  entrada documenta la realidad ya implementada en vez de forzar 
  una migración retroactiva a TypeScript.
- 1.1.0 (2026-08-10): se añade el rol "comercial" a los roles del 
  sistema (control de acceso por rol), introducido por el módulo 
  010 (CRM / Leads) para el seguimiento comercial de leads.
