# Spec 007 — Planes de entrenamiento y nutrición

## Resumen
Entrenadores diseñan rutinas de ejercicio y planes nutricionales 
para sus socios asignados (módulo 006).

## Relación con módulos existentes
- Solo un `Entrenador` (006) puede crear planes
- Solo para `Socios` (003) que tenga asignados (tabla socios_asignados)
- El `Asistente IA conversacional` (016) puede generar borradores de 
  rutina/plan nutricional; al ser aprobados por el entrenador, se 
  materializan como registros de este módulo (ver FR6)

## Requisitos funcionales
1. Entrenador crea rutina: nombre, ejercicios (nombre, series, reps, 
   descanso), días de la semana
2. Entrenador crea plan nutricional: comidas por día, notas 
   (sin cálculo automático de macros en v1)
3. Socio ve sus rutinas y planes asignados, marca ejercicios como 
   completados
4. Entrenador ve progreso de cumplimiento de su socio
5. Historial de planes anteriores (no se borran, se archivan)
6. Un plan/rutina puede originarse de un borrador generado por el 
   Asistente IA (módulo 016) y aprobado por el entrenador; en ese 
   caso el entrenador sigue siendo su autor y responsable final, 
   pero el registro conserva la trazabilidad de su origen (manual o 
   IA) y, si aplica, referencia al borrador original

## Criterios de aceptación
- Un socio solo ve planes de su propio entrenador asignado
- Un plan archivado no se puede editar, solo consultar
- Un plan con origen IA (016) no se activa como definitivo hasta que 
  el entrenador lo aprueba explícitamente (ver módulo 016)

## Fuera de alcance en esta feature
- Cálculo automático de calorías/macros
- Integración con wearables