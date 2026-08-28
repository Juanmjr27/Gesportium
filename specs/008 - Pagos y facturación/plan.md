# Plan 008 — Pagos y facturación

## Fase 0 — Modelo de datos

**Tabla `pagos`**
- id (UUID, PK), socio_id (FK), membresia_id (FK, nullable), 
  concepto (string), importe (decimal), estado (enum: exitoso, 
  fallido, pendiente), fecha (datetime)

**Tabla `facturas`**
- id (UUID, PK), pago_id (FK), numero (string, único), 
  pdf_url (string), fecha_emision (datetime), anulada (boolean)

**Tabla `remesas`**
- id (UUID, PK), sede_id (FK), fecha (date), total (decimal)

**Tabla `remesa_pagos`** (relación N:M)
- remesa_id (FK), pago_id (FK)

**Tabla `historial_acciones_pago`** (auditoría, mismo patrón que 
`historial_estados_membresia` de 004 y `historial_acciones_socio` de 003)
- id (UUID, PK), entidad_tipo (enum: pago, factura, remesa), 
  entidad_id (UUID), accion (string), autor_id (FK a usuarios), 
  fecha (datetime)

## Fase 1 — Contratos de API

| Método | Ruta | Rol | Descripción |
|---|---|---|---|
| POST | /pagos/procesar | sistema (interno) | Cobro automático por renovación (excluye membresías en estado `congelada`, consultado vía módulo 004) |
| GET | /pagos/{socio_id} | propio socio, gestor_sede, admin | Historial |
| GET | /facturas/{id} | propio socio, gestor_sede, admin | Descargar PDF |
| POST | /remesas | admin, gestor_sede | Generar remesa |
| GET | /remesas | admin, gestor_sede (su sede) | Listado |

## Fase 2 — Seguridad
- Reutiliza dependencies.py del 001
- Endpoint de cobro automático no expuesto públicamente (job interno)
- El job de cobro filtra `membresias.estado != congelada` (módulo 
  004) antes de generar el pago
- Tras N reintentos fallidos (parametrizable), el servicio llama a 
  `POST /membresias/{id}/congelar` (módulo 004) con `origen=impago` 
  como único mecanismo de cambio de estado — no se escribe 
  directamente en las tablas de 004, para preservar 
  `historial_estados_membresia`
- Emite evento "pago fallido" hacia el módulo 011 (Notificaciones)

## Fase 3 — Estructura de carpetas

\`\`\`
backend/
└── app/
    └── modules/
        └── pagos/
            ├── models.py
            ├── schemas.py
            ├── router.py
            └── service.py
\`\`\`

## Fase 4 — Dependencias externas
- Generación de PDF (ej. `reportlab` o `weasyprint`)