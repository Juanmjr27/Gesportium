# Spec 006 — Entrenadores

## Resumen
Gestión del perfil profesional de los entrenadores y la relación de 
qué socios tiene asignados cada uno, resolviendo las dependencias 
pendientes de los módulos 003 y 005.

## Relación con módulos existentes
- Todo entrenador tiene un `Usuario` (módulo 001) con rol `entrenador`
- Pertenece a una `Sede` (módulo 002)
- Resuelve la dependencia pendiente del módulo 003: aquí se define 
  la tabla `socios_asignados` que decide qué socios ve un entrenador
- Resuelve la dependencia pendiente del módulo 005: `clases.entrenador_id` 
  ya apuntaba aquí, ahora queda validado contra este modelo

## Requisitos funcionales
1. admin y gestor_sede dan de alta entrenadores: especialidades 
   (ej. yoga, crossfit, nutrición), horario disponible, sede
2. Asignación de socios a un entrenador para seguimiento personalizado 
   (entrenamiento personal), independiente de las clases grupales
3. Un entrenador puede impartir clases grupales (módulo 005) sin 
   necesidad de tener socios asignados en personal
4. gestor_sede asigna/desasigna socios a entrenadores
5. Entrenador ve: sus clases asignadas, sus socios de entrenamiento 
   personal, no ve socios de otros entrenadores ni de otras sedes
6. Baja de entrenador: baja lógica, sus clases futuras deben 
   reasignarse o cancelarse (aviso a gestor_sede)

## Criterios de aceptación
- Un entrenador dado de baja no puede ser asignado a nuevas clases 
  ni nuevos socios
- La asignación socio-entrenador registra fecha de inicio (y fin si 
  se desasigna), para histórico
- Un entrenador solo ve datos de socios que tiene asignados o que 
  están inscritos en sus clases (no el listado completo de socios)

## Fuera de alcance en esta feature
- Planes de entrenamiento/nutrición en sí (módulo 007)
- Pago a entrenadores (nóminas) — no contemplado en v1