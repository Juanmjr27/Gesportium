# Spec 020 — Mejoras de ingeniería (revisión externa)

## Resumen
Un amigo de Juan, ingeniero de software, revisó el repositorio público de
Gesportium tras su publicación (specs/019) y mandó dos cosas: un documento
con 12 puntos de mejora de ingeniería, y después un mensaje de WhatsApp
matizando y acotando algunos de esos puntos (qué es urgente, qué es una
feature aparte, qué no tiene caso de uso todavía). Este módulo formaliza
esa revisión externa como trabajo de ingeniería sobre el proyecto ya
existente: no añade funcionalidad de producto nueva, mejora la base de
código de los 17 módulos de producto ya construidos (identidad, socios,
membresías, entrenadores, pagos, sedes, crm, etc.) en autorización,
pruebas, estructura y documentación.

## Relación con módulos existentes
- No añade funcionalidad de producto: es trabajo transversal de ingeniería
  sobre el código ya construido en specs/001-017 (mismo tipo de módulo que
  specs/018 y specs/019, que tampoco añadieron feature de producto)
- El punto más concreto (T1, autorización centralizada) toca directamente
  el código de socios (003), membresías (004), entrenadores (006), pagos
  (008), sedes (002) y crm (010) — sin cambiar su comportamiento observable
  desde fuera, solo cómo está implementado internamente

## Problema observado
El documento del revisor identifica patrones que se repiten en un proyecto
que ha crecido módulo a módulo siguiendo un flujo spec-driven estricto,
pero sin una pasada de refactor transversal entre módulos:

1. **Autorización duplicada**: 5 `router.py` distintos (`entrenadores`,
   `socios`, `pagos`, `membresias`, `sedes`, `crm` — 6 en realidad)
   reimplementan, cada uno con su propio nombre de función
   (`_verificar_acceso_gestion`, `_verificar_acceso_socio`,
   `_verificar_acceso_membresia`, `_verificar_acceso_sede`,
   `_verificar_acceso_lead`), la misma regla de negocio: admin ve todo,
   gestor_sede ve su sede, y en algunos casos el propio dueño del recurso
   ve lo suyo. Cambiar esa regla (por ejemplo, añadir un nuevo rol con
   acceso parcial) requeriría tocar 5-6 sitios a la vez, con riesgo de que
   alguno quede desincronizado.
2. **Sin CI/CD**: no hay ningún workflow de GitHub Actions — los tests
   (`pytest`, 100%+ en verde según CHANGELOG.md) solo se ejecutan
   manualmente, nunca automáticamente contra cada cambio.
3. **Sin Dockerfile**: no hay forma de levantar el backend en un contenedor;
   el único camino documentado en el README es el entorno virtual local.
4. **Tests no separados por tipo**: la suite de `pytest` mezcla tests que
   solo ejercitan lógica de un módulo con tests que hacen peticiones HTTP
   completas contra la base de datos, sin distinción de carpeta ni marker.
5. **Sin tests de frontend**: `frontend/` no tiene ninguna suite de tests
   (ni unitarios de componentes ni end-to-end), pese a tener dos
   aplicaciones completas (portal-socio, panel-admin).
6. **Persistencia mezclada con lógica de negocio**: los `service.py` de los
   módulos llaman a `db.commit()` directamente y en varios puntos distintos
   de cada flujo, sin una capa de repositorio ni límites de transacción
   explícitos — dificulta razonar sobre qué queda persistido si un paso
   intermedio falla.
7. **Organización por capa técnica**: dentro de cada módulo de
   `backend/app/modules/` ya se organiza por dominio, pero el propio
   revisor apunta a evolucionar esa organización (y la del frontend) para
   que sea aún más evidente por dominio de negocio en vez de por capa
   técnica (routers/, services/, models/ como agrupación transversal).
8. **Sin `AGENTS.md`**: no hay un punto de entrada único en la raíz del
   repo que explique a otro desarrollador (humano o agente) cómo está
   organizado el proyecto y cómo trabajar en él.
9. **`.claude/`/`.specify/` sin distinguir de código de producto**: specs/019
   ya decidió fichero por fichero qué trackear de estos directorios, pero
   el repo no documenta en ningún sitio visible qué es config del flujo
   Speckit y qué es código del producto en sí.
10. **Sin logging ni reporte de errores estructurado**: no hay un logger
    configurado ni una estrategia de captura de errores más allá de las
    excepciones HTTP de FastAPI — un fallo en producción no dejaría rastro
    más allá de lo que imprima uvicorn.
11. **Sin sistema de permisos configurable por pantalla**: los roles
    (admin, gestor_sede, entrenador, socio, comercial) están fijados en
    código; no hay ninguna pantalla para definir permisos granulares por
    usuario o rol en tiempo de ejecución. El revisor fue explícito en el
    matiz de WhatsApp: esto es una **feature de producto nueva**, no forma
    parte de "centralizar autorización" (T1) — se aparca sin urgencia.
12. **Sin exploración de MCP, Docker Compose completo ni mensajería
    asíncrona**: ninguno de los tres tiene un caso de uso concreto todavía
    en este proyecto — quedan como ideas a evaluar más adelante, no como
    trabajo pendiente con motivación actual.

## Requisitos funcionales
1. Los 5 puntos de acceso duplicados por sede/propietario en los routers de
   socios, entrenadores, pagos, membresías, sedes y crm deben consolidarse
   en una única función compartida en `identidad/dependencies.py`, sin
   cambiar el comportamiento observable de ningún endpoint existente (T1)
2. El proyecto debe poder verificarse automáticamente en cada cambio
   (CI) y poder levantarse en un contenedor (Dockerfile básico), sin que
   ninguna de las dos cosas cambie el comportamiento de la aplicación (T2, T3)
3. La suite de tests del backend debe distinguir tests unitarios de tests
   de integración, y el frontend debe pasar a tener cobertura de tests
   donde hoy no tiene ninguna (T4, T5)
4. La capa de persistencia debe separarse de la lógica de negocio mediante
   transacciones explícitas y un patrón Repository, reduciendo los
   `commit()` sueltos repartidos por los `service.py` (T6)
5. La estructura del código y su documentación deben facilitar que alguien
   nuevo (humano o agente) entienda el proyecto rápido: organización por
   dominio, un `AGENTS.md` de referencia en la raíz, separación clara entre
   config de Speckit y código de producto, y logging/reporte de errores
   básico (T7, T8, T9)
6. Los puntos aparcados (permisos configurables por pantalla, exploración
   de MCP, Docker Compose completo con healthchecks, notificaciones
   asíncronas con RabbitMQ) quedan documentados como tareas de referencia
   sin implementar en este módulo, para no perder la observación del
   revisor aunque no haya urgencia (T10, T11, T12)

## Criterios de aceptación
- Cada tarea (T1-T12) se cierra siguiendo el mismo ciclo spec-driven ya
  usado en el resto del proyecto: explicación del problema → diseño →
  implementación → verificación, documentado en este módulo
- Ninguna tarea de las Fases 1-3 cambia el comportamiento observable de la
  API ni del frontend desde el punto de vista de un cliente externo —son
  mejoras de calidad interna, no de producto
- La suite completa de `pytest` sigue en verde después de cada tarea que
  toque código de backend
- Las tareas de la Fase 4 (aparcadas) quedan registradas en `tasks.md` sin
  marcar, como referencia explícita de que se evaluaron y se decidió no
  abordarlas todavía — no se implementa ninguna sin que el usuario la pida
  explícitamente en un prompt separado

## Fuera de alcance en esta feature
- Implementar el sistema de permisos configurable por pantalla — es una
  feature de producto nueva, con su propio spec futuro si se decide
  abordar (ver Fase 4, T10)
- Explorar o integrar MCP, Docker Compose completo, o RabbitMQ — sin caso
  de uso concreto todavía (ver Fase 4, T11, T12)
- Cualquier tarea de la Fase 2, 3 o 4 más allá de T1: se documentan como
  referencia en `tasks.md` pero no se implementan hasta que el usuario las
  encargue explícitamente, una por una
