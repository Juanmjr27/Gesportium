# Plan 004 — Membresías

## Fase 0 — Modelo de datos

**Tabla `planes_membresia`**
- id (UUID, PK)
- nombre (string)
- precio (decimal)
- duracion (enum: mensual, trimestral, anual)
- alcance (enum: sede_unica, toda_cadena)
- sede_id (FK a sedes, nullable si alcance=toda_cadena)
- preaviso_cancelacion_dias (integer)
- activo (boolean, default true)

**Tabla `membresias`**
- id (UUID, PK)
- socio_id (FK a socios)
- plan_id (FK a planes_membresia)
- fecha_inicio (date)
- fecha_proxima_renovacion (date)
- renovacion_automatica (boolean, default true)
- estado (enum: activa, congelada, cancelada, vencida)
- fecha_cancelacion (date, nullable)

**Tabla `congelaciones_membresia`**
- id (UUID, PK)
- membresia_id (FK a membresias)
- fecha_inicio (date)
- fecha_fin (date, nullable)
- motivo (string, opcional)
- origen (enum: manual, impago — default manual)

**Tabla `historial_estados_membresia`** (auditoría)
- id (UUID, PK)
- membresia_id (FK a membresias)
- estado_anterior (enum)
- estado_nuevo (enum)
- autor_id (FK a usuarios)
- fecha (datetime)

## Fase 1 — Contratos de API

| Método | Ruta | Rol requerido | Descripción |
|---|---|---|---|
| POST | /planes-membresia | admin | Crear plan |
| GET | /planes-membresia | público | Listado de planes disponibles |
| POST | /membresias | admin, gestor_sede | Alta de membresía a un socio |
| GET | /membresias/{id} | admin, gestor_sede, propio socio | Detalle |
| POST | /membresias/{id}/congelar | admin, gestor_sede, propio socio, sistema (interno, origen=impago) | Congelar |
| POST | /membresias/{id}/reactivar | admin, gestor_sede, propio socio | Reactivar (bloqueada si `congelaciones_membresia.origen = impago` y el módulo 008 reporta pago pendiente) |
| POST | /membresias/{id}/cancelar | admin, gestor_sede, propio socio | Cancelar |

## Fase 2 — Seguridad y validaciones
- Reutiliza `dependencies.py` del módulo 001
- Validación cruzada con módulo 008 (pagos pendientes) antes de 
  permitir cancelación o reactivación de una congelación por impago
- Todo cambio de estado inserta fila en `historial_estados_membresia`, 
  incluidos los disparados por el módulo 008 (autor_id = usuario 
  técnico "sistema", para no romper la trazabilidad exigida por la 
  Constitution)
- Contrato interno con módulo 008: el job de cobro (008) llama a 
  `POST /membresias/{id}/congelar` con `origen=impago` tras agotar 
  reintentos; este endpoint es la única vía autorizada para que 008 
  modifique el estado de una membresía (nunca escritura directa a BD)
- Job diario de renovación: recorre membresías `activa` con 
  `renovacion_automatica=true`, omite las que estén `congelada`, y 
  marca como "próxima a vencer" (evento a módulo 011) las que estén 
  a ≤3 días de `fecha_proxima_renovacion`
- Job diario de vencimiento (`ejecutar_job_vencimiento`, disparado por 
  scheduler externo, igual que el job de renovación): recorre 
  membresías `activa` con `renovacion_automatica=false` cuya 
  `fecha_proxima_renovacion` ya pasó, las marca `estado=vencida` 
  (con su fila en `historial_estados_membresia`) y emite el evento 
  "membresía vencida" al módulo 011. Las membresías con 
  `renovacion_automatica=true` no pasan por este job: su transición a 
  `vencida`/`congelada` depende de que el módulo 008 agote los 
  reintentos de cobro automático y llame a 
  `/membresias/{id}/congelar` (ver Fase 4)

## Fase 3 — Estructura de carpetas (backend)

\`\`\`
backend/
└── app/
    └── modules/
        └── membresias/
            ├── models.py       # PlanMembresia, Membresia, CongelacionMembresia, HistorialEstadosMembresia
            ├── schemas.py      # Pydantic schemas
            ├── router.py       # Endpoints FastAPI
            └── service.py      # Lógica de negocio (cambios de estado, validaciones)
\`\`\`

## Fase 4 — Dependencias externas
- Módulo 008 (Pagos y facturación): llama a `/membresias/{id}/congelar` 
  tras impago; se consulta antes de permitir reactivación/cancelación; 
  para membresías con `renovacion_automatica=true`, es también la vía 
  por la que llegan a `vencida`/`congelada` (el job de vencimiento de 
  004 no las gestiona directamente)
- Módulo 011 (Notificaciones): consumidor de los eventos "próxima a 
  vencer" y "membresía vencida"