# Plan 020 — Mejoras de ingeniería (revisión externa)

## Criterio de priorización
Gesportium es un proyecto personal de portfolio para búsqueda de empleo, no
un sistema que vaya a escalar a producción real ni a recibir tráfico
concurrente de verdad. Eso condiciona el orden de las 4 fases: se prioriza
lo que un revisor técnico (o un entrevistador) va a notar rápido leyendo el
código o el repo — duplicación, ausencia de CI, ausencia de Dockerfile —
por encima de infraestructura que solo importaría con escala real
(RabbitMQ, Docker Compose con healthchecks) o de features de producto que
no aportan a "esto está bien construido" (permisos configurables por
pantalla). El orden de fases es explícitamente coste/señal: primero lo
barato con mucha señal, al final lo que no es urgente para este objetivo.

## Fase 1 — Barato, mucha señal
1. **T1 — Autorización centralizada**: 5 funciones duplicadas
   (`_verificar_acceso_gestion` ×2, `_verificar_acceso_socio`,
   `_verificar_acceso_membresia`, `_verificar_acceso_sede`,
   `_verificar_acceso_lead`) que ya hacen literalmente lo mismo (admin
   pasa, gestor_sede pasa si coincide sede, a veces el propio dueño pasa)
   → una función en `identidad/dependencies.py`. Se hace primero porque es
   el cambio de menor riesgo (comportamiento idéntico, solo se mueve dónde
   vive la regla) y el que más deuda evidente elimina de golpe.
2. **T2 — CI/CD con GitHub Actions**: correr `pytest` automáticamente en
   cada push/PR. Depende de que T1 no haya roto nada — tiene sentido tener
   ya la suite verde y estable antes de automatizarla, no al revés.
3. **T3 — Dockerfile básico**: una forma de levantar el backend sin el
   entorno virtual local. Va al final de esta fase porque es el más
   mecánico de los tres y no depende de ningún cambio de código previo,
   solo de que el proyecto ya esté en un estado limpio.

## Fase 2 — Calidad del código
4. **T4 — Separar tests unitarios de integración**: reorganizar
   `backend/tests/` en unit/integration (o markers de pytest), como base
   necesaria antes de que el pipeline de CI (T2) pueda distinguir qué
   ejecutar en qué momento.
5. **T5 — Tests de frontend**: `frontend/` no tiene ninguna suite hoy. Se
   aborda después de T4 para poder replicar el mismo criterio de
   separación unit/integration ya establecido en el backend.
6. **T6 — Transacciones + patrón Repository**: separar persistencia de
   lógica de negocio en los `service.py`, eliminando los `commit()` sueltos
   repartidos por cada flujo. Va al final de esta fase porque es el cambio
   de mayor superficie de código tocado (todos los módulos con
   `service.py`) y conviene hacerlo con la red de seguridad de tests ya
   reorganizada (T4) para detectar cualquier regresión de comportamiento
   transaccional.

## Fase 3 — Estructura y documentación
7. **T7 — Reorganización por dominio**: evolucionar la organización de
   backend/frontend para que el agrupamiento por dominio de negocio sea
   aún más explícito que por capa técnica. Se hace después de T6 porque
   tocar estructura de ficheros a la vez que se introduce Repository
   duplicaría el riesgo de conflictos; mejor con la capa de persistencia
   ya estable.
8. **T8 — `AGENTS.md` + separación config Speckit / código de producto**:
   documentar el proyecto ya reorganizado (T7) es más útil que documentar
   una estructura que va a cambiar poco después.
9. **T9 — Logging/reporte de errores**: última de la fase porque es
   ortogonal a la reorganización (T7) y a la documentación (T8) — no
   depende de ninguna, se hace al final de esta fase porque cierra el
   bloque de "hacer el proyecto entendible y observable" iniciado con T7/T8.

## Fase 4 — Aparcado, sin prisa
Ninguno de estos puntos es urgente para un proyecto de portfolio; se
documentan como tareas de referencia (sin marcar en tasks.md) para no
perder la observación del revisor, pero no se implementan salvo que el
usuario lo pida explícitamente más adelante:

10. **T10 — Sistema de permisos configurable por rol/usuario**: el revisor
    fue explícito (matiz de WhatsApp) en que esto es una feature de
    producto aparte, no parte de "centralizar autorización" (T1) — requiere
    su propio spec si se aborda.
11. **T11 — Explorar si algún MCP tiene sentido**: sin caso de uso concreto
    todavía en este proyecto.
12. **T12 — Docker Compose completo (backend+Postgres+Ollama con
    healthchecks) y notificaciones asíncronas con RabbitMQ**: ambos son
    infraestructura que solo se justifica con escala o despliegue real, que
    no es el objetivo de este proyecto de portfolio.
13. **Docker Compose (backend + PostgreSQL + Ollama)**, evolución sobre el
    Dockerfile de T3 — orquestar los tres servicios juntos, healthchecks,
    variables de entorno centralizadas.

## Forma de trabajo
Cada tarea (T1-T12) se cierra de forma independiente y bajo demanda
explícita del usuario, siguiendo el mismo ciclo ya usado en el resto del
proyecto: explicación del problema → diseño de la solución →
implementación → verificación. No se implementa ninguna tarea por
adelantado ni se combinan varias en un mismo cambio sin que el usuario lo
pida.
