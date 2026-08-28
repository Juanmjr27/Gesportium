# Plan 013 — Informes con Ollama

## Fase 0 — Modelo de datos
No requiere tablas nuevas (consulta agregada, igual que Dashboard)

## Fase 1 — Contratos de API

| Método | Ruta | Rol | Descripción |
|---|---|---|---|
| GET | /informes/{tipo} | admin, gestor_sede | Datos del informe |
| GET | /informes/{tipo}/exportar | admin, gestor_sede | PDF/Excel |
| POST | /informes/{tipo}/resumen-ia | admin, gestor_sede | Resumen vía Ollama |

## Fase 2 — Seguridad
- Reutiliza dependencies.py del 001
- Comunicación con Ollama solo desde backend (localhost:11434), 
  nunca expuesta al frontend directamente

## Fase 3 — Estructura de carpetas

\`\`\`
backend/
└── app/
    └── modules/
        └── informes/
            ├── schemas.py
            ├── router.py
            ├── service.py       # queries de cada informe
            └── ollama_client.py # llamada al modelo local
\`\`\`

## Fase 4 — Dependencias externas
- Ollama corriendo en el servidor (localhost:11434)
- `reportlab`/`openpyxl` (ya contemplado en 008 para PDF)