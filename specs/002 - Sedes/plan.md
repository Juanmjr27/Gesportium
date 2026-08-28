# Plan 002 — Sedes

## Fase 0 — Modelo de datos (SQLAlchemy)

**Tabla `sedes`**
- id (UUID, PK)
- nombre (string)
- direccion (string)
- ciudad (string)
- telefono (string)
- horario_apertura (time)
- horario_cierre (time)
- aforo_maximo (integer)
- activa (boolean, default true)
- fecha_creacion (datetime)

**Relación con `usuarios`** (módulo 001): 
`usuarios.sede_id` → FK a `sedes.id` (ya definida en 001, se activa 
su relación real aquí)

## Fase 1 — Endpoints de la API

| Método | Ruta | Rol requerido | Descripción |
|---|---|---|---|
| GET | /sedes | público | Listado básico (nombre, dirección, horario) |
| GET | /sedes/{id} | admin, gestor_sede (solo la suya) | Detalle completo |
| POST | /sedes | admin | Crear sede |
| PUT | /sedes/{id} | admin, gestor_sede (solo la suya) | Editar sede |
| DELETE | /sedes/{id} | admin | Baja lógica (activa=false) |

## Fase 2 — Seguridad
- Reutiliza el `dependencies.py` de Identidad (módulo 001) para 
  validar rol
- Nueva validación específica: gestor_sede solo puede operar sobre 
  su propio `sede_id` (comparando `usuario.sede_id` con el `id` de 
  la sede solicitada)

## Fase 3 — Estructura de carpetas (backend)

\`\`\`
backend/
└── app/
   └── modules/
      └── sedes/
      ├── models.py # Sede
      ├── schemas.py # Pydantic schemas
      ├── router.py # Endpoints FastAPI
      └── service.py # Lógica de negocio
\`\`\`

## Fase 4 — Dependencias externas
Ninguna nueva — reutiliza lo ya instalado en el módulo 001