# Plan 015 — Portal de socio

## Fase 0 — Pantallas principales
Login/Registro, Home (resumen membresía), Clases (catálogo+reserva), 
Mi entrenamiento (rutinas/nutrición), Pagos/Facturas, Mi perfil

## Fase 1 — Consumo de API
Cada pantalla consume los endpoints ya definidos — no se listan de 
nuevo aquí, referencia directa a specs 001, 003, 004, 005, 007, 008, 009

## Fase 2 — Seguridad
- Token JWT almacenado de forma segura (no localStorage plano, 
  usar httpOnly cookie o almacenamiento seguro equivalente)
- Rutas protegidas según rol=socio

## Fase 3 — Estructura de carpetas (frontend)

\`\`\`
frontend/
└── src/
    └── portal-socio/
        ├── pages/       # Login, Home, Clases, Entrenamiento, Pagos, Perfil
        ├── components/
        ├── hooks/       # useAuth, useApi
        └── services/    # llamadas a la API
\`\`\`

## Fase 4 — Dependencias externas
- React Router, cliente HTTP (ej. axios), gestor de estado ligero 
  (Context API o Zustand)