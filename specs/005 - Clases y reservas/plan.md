# Plan 005 — Clases y reservas

## Fase 0 — Modelo de datos

**Tabla `clases`**
- id (UUID, PK)
- sede_id (FK a sedes)
- entrenador_id (FK a entrenadores.id, módulo 006 — no a usuarios directamente)
- nombre (string)
- tipo (string)
- fecha_hora (datetime)
- duracion_minutos (integer)
- aforo_maximo (integer)
- recurrente (boolean)
- regla_recurrencia (string, nullable — ej. "weekly:monday")

**Tabla `reservas`**
- id (UUID, PK)
- clase_id (FK a clases)
- socio_id (FK a socios)
- estado (enum: confirmada, lista_espera, cancelada)
- fecha_reserva (datetime)
- fecha_cancelacion (datetime, nullable)

**Tabla `asistencias`**
- id (UUID, PK)
- reserva_id (FK a reservas)
- fecha_checkin (datetime, nullable)

## Fase 1 — Contratos de API

| Método | Ruta | Rol requerido | Descripción |
|---|---|---|---|
| POST | /clases | gestor_sede, admin | Crear clase |
| GET | /clases | público (autenticado) | Listado con filtro por sede/fecha |
| GET | /clases/{id} | público (autenticado) | Detalle + aforo disponible |
| PUT | /clases/{id} | gestor_sede, admin | Editar clase |
| POST | /clases/{id}/reservar | socio | Reservar plaza |
| DELETE | /reservas/{id} | socio (propia), gestor_sede | Cancelar reserva |
| GET | /clases/{id}/ocupacion | gestor_sede, entrenador (si es suya) | Ver ocupación |

## Fase 2 — Seguridad y validaciones
- Reutiliza `dependencies.py` del módulo 001
- Validación de membresía activa antes de reservar (llamada al 
  módulo 004)
- Validación de aforo: si está lleno, inserta en `reservas` con 
  estado `lista_espera` en vez de rechazar
- Al asignar `entrenador_id` en POST/PUT `/clases`, validar que el 
  entrenador (módulo 006) tiene `activo = true`; si no, rechazar con 
  error de validación
- Endpoint interno `POST /clases/reasignar-por-baja-entrenador` 
  (rol: sistema/gestor_sede), invocado por el módulo 006 al dar de 
  baja un entrenador: recibe `entrenador_id` y devuelve/cancela las 
  clases futuras de ese entrenador según decisión del gestor_sede 
  (reasignar a otro entrenador o cancelar, con notificación — 
  módulo 011)

## Fase 3 — Estructura de carpetas (backend)

\`\`\`
backend/
└── app/
    └── modules/
        └── clases/
            ├── models.py       # Clase, Reserva, Asistencia
            ├── schemas.py      # Pydantic schemas
            ├── router.py       # Endpoints FastAPI
            └── service.py      # Lógica de negocio (aforo, lista de espera)
\`\`\`

## Fase 4 — Dependencias externas
Ninguna nueva