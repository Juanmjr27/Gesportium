# Plan 017 — Panel de administración

## Fase 0 — Pantallas principales
Login, Dashboard, Sedes, Socios, Membresías, Clases, Entrenadores, 
Pagos/Remesas, Leads, Informes, Configuración

## Fase 1 — Consumo de API
Cada pantalla consume los endpoints ya definidos en sus specs 
respectivas (001-014) — sin duplicar aquí

## Fase 2 — Seguridad
- Rutas protegidas según rol (admin/gestor_sede/entrenador)
- Menú lateral se adapta dinámicamente según permisos del usuario

## Fase 3 — Estructura de carpetas (frontend)

\`\`\`
frontend/
└── src/
    └── panel-admin/
        ├── pages/       # Dashboard, Sedes, Socios, Clases, etc.
        ├── components/  # Tablas, formularios reutilizables
        ├── hooks/
        └── services/
\`\`\`

## Fase 4 — Dependencias externas
- Mismas que portal-socio (React Router, cliente HTTP, gestor de 
  estado) + librería de tablas/gráficos (ej. Recharts para KPIs)