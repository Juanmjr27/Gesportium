# Plan 006 — Entrenadores

## Fase 0 — Modelo de datos

**Tabla `entrenadores`**
- id (UUID, PK)
- usuario_id (FK a usuarios, único)
- sede_id (FK a sedes)
- especialidades (array de string)
- horario_disponible (JSON, franjas horarias)
- activo (boolean, default true)

**Tabla `socios_asignados`**
- id (UUID, PK)
- entrenador_id (FK a entrenadores)
- socio_id (FK a socios)
- fecha_inicio (date)
- fecha_fin (date, nullable)

## Fase 1 — Contratos de API

| Método | Ruta | Rol requerido | Descripción |
|---|---|---|---|
| POST | /entrenadores | admin, gestor_sede | Alta de entrenador |
| GET | /entrenadores | admin, gestor_sede | Listado (filtrado por sede) |
| GET | /entrenadores/{id} | admin, gestor_sede, propio entrenador | Detalle |
| PUT | /entrenadores/{id} | admin, gestor_sede | Editar |
| DELETE | /entrenadores/{id} | admin, gestor_sede | Baja lógica |
| POST | /entrenadores/{id}/socios | gestor_sede | Asignar socio |
| DELETE | /entrenadores/{id}/socios/{socio_id} | gestor_sede | Desasignar socio |
| GET | /entrenadores/{id}/socios | propio entrenador, gestor_sede | Ver socios asignados |

## Fase 2 — Seguridad y validaciones
- Reutiliza `dependencies.py` del módulo 001
- Al dar de baja entrenador: consultar clases futuras asignadas 
  (módulo 005) y, si existen, requerir confirmación explícita del 
  gestor_sede antes de completar la baja. Al confirmar, llamar a 
  `POST /clases/reasignar-por-baja-entrenador` (módulo 005) con el 
  `entrenador_id`, que reasigna o cancela esas clases y notifica a 
  los socios con reserva confirmada (módulo 011)

## Fase 3 — Estructura de carpetas (backend)

\`\`\`
backend/
└── app/
    └── modules/
        └── entrenadores/
            ├── models.py       # Entrenador, SocioAsignado
            ├── schemas.py      # Pydantic schemas
            ├── router.py       # Endpoints FastAPI
            └── service.py      # Lógica de negocio (asignación, baja)
\`\`\`

## Fase 4 — Dependencias externas
Ninguna nueva