# Plan 012 — Dashboard

## Fase 0 — Modelo de datos
No requiere tablas nuevas — consulta agregada sobre tablas existentes 
(socios, membresias, pagos, clases, leads)

## Fase 1 — Contratos de API

| Método | Ruta | Rol | Descripción |
|---|---|---|---|
| GET | /dashboard/kpis | admin, gestor_sede | KPIs según rol/sede |

## Fase 2 — Seguridad
- Reutiliza dependencies.py del 001
- Filtro de sede aplicado automáticamente si rol=gestor_sede

## Fase 3 — Estructura de carpetas

\`\`\`
backend/
└── app/
    └── modules/
        └── dashboard/
            ├── schemas.py
            ├── router.py
            └── service.py   # queries agregadas
\`\`\`

## Fase 4 — Dependencias externas
Ninguna nueva