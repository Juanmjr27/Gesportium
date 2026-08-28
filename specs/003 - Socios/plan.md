# Plan 003 — Socios

## Fase 0 — Modelo de datos

**Tabla `socios`**
- id (UUID, PK)
- usuario_id (FK a usuarios, único)
- sede_id (FK a sedes)
- fecha_nacimiento (date)
- telefono (string)
- direccion (string)
- contacto_emergencia_nombre (string)
- contacto_emergencia_telefono (string)
- fecha_alta (date)
- fecha_baja (date, nullable)
- activo (boolean, default true)

**Tabla `documentos_socio`**
- id (UUID, PK)
- socio_id (FK a socios)
- tipo (enum: consentimiento, aptitud_medica)
- archivo_url (string)
- fecha_subida (datetime)
- fecha_caducidad (date, nullable)

**Tabla `notas_socio`** (internas)
- id (UUID, PK)
- socio_id (FK a socios)
- autor_id (FK a usuarios)
- contenido (text)
- fecha (datetime)

**Tabla `historial_sedes_socio`**
- id (UUID, PK)
- socio_id (FK a socios)
- sede_id (FK a sedes)
- fecha_inicio (date)
- fecha_fin (date, nullable)

## Fase 1 — Contratos de API

| Método | Ruta | Rol requerido | Descripción |
|---|---|---|---|
| POST | /socios | admin, gestor_sede | Alta de socio |
| GET | /socios | admin, gestor_sede, entrenador (filtrado por `socios_asignados` + `reservas`, ver Fase 2) | Listado según permisos |
| GET | /socios/{id} | admin, gestor_sede, entrenador (si asignado en `socios_asignados` o inscrito en su clase), propio socio | Detalle |
| PUT | /socios/{id} | admin, gestor_sede, propio socio (solo contacto) | Editar |
| DELETE | /socios/{id} | admin, gestor_sede | Baja lógica |
| POST | /socios/{id}/documentos | admin, gestor_sede | Subir documento |
| POST | /socios/{id}/transferir | admin, gestor_sede origen | Transferir de sede |
| POST | /socios/{id}/notas | admin, gestor_sede | Añadir nota interna |

## Fase 2 — Seguridad y validaciones
- Reutiliza `dependencies.py` de Identidad (001) para rol y sede
- Nueva validación: entrenador solo accede a socios presentes en 
  `socios_asignados` (módulo 006, filtrado por `entrenador_id`) o en 
  `reservas` de una clase que imparte (módulo 005, filtrado por 
  `clases.entrenador_id`)
- Notas internas excluidas explícitamente del schema de respuesta 
  cuando el solicitante es el propio socio

## Fase 3 — Estructura de carpetas (backend)

\`\`\`
backend/
└── app/
    └── modules/
        └── socios/
            ├── models.py       # Socio, DocumentoSocio, NotaSocio, HistorialSedesSocio
            ├── schemas.py      # Pydantic schemas
            ├── router.py       # Endpoints FastAPI
            └── service.py      # Lógica de negocio (alta, transferencia, baja)
\`\`\`

## Fase 4 — Dependencias externas
- Almacenamiento de archivos (ej. S3 o equivalente local en desarrollo) 
  para documentos del socio