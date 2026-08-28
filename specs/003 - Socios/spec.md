# Spec 003 — Socios

## Resumen
Gestión de los socios de la cadena de gimnasios: sus datos personales, 
historial y documentación asociada a su condición de socio (más allá 
del acceso al sistema, que ya cubre el módulo 001).

## Relación con módulos existentes
- Todo socio tiene un `Usuario` (módulo 001) con rol `socio`
- Todo socio pertenece a una `Sede` (módulo 002)
- La membresía en sí (plan, precio, estado) se define en el módulo 004, 
  no aquí — este módulo cubre el perfil del socio, no su suscripción
- La visibilidad de socios por parte de un entrenador (asignación 
  personal e inscripción a clases) se resuelve con las tablas 
  `socios_asignados` (módulo 006) y `reservas` (módulo 005)

## Requisitos funcionales
1. Alta de socio — completa datos adicionales al `Usuario` ya creado 
   en el módulo 001: fecha de nacimiento, teléfono, dirección, 
   contacto de emergencia
2. Documentación: subida de consentimiento informado y certificado de 
   aptitud médica (PDF/imagen), con fecha de caducidad si aplica
3. Historial del socio: fechas de alta/baja, sede(s) por las que ha 
   pasado, notas internas (visibles solo para admin/gestor_sede)
4. Transferencia de socio entre sedes — admin y gestor_sede origen 
   pueden iniciarla; conserva el historial
5. Baja de socio: baja lógica, no se elimina el registro (se conserva 
   histórico de pagos/asistencias)
6. gestor_sede y entrenador solo ven socios de su propia sede; 
   entrenador solo ve los socios que tiene asignados en 
   entrenamiento personal (tabla `socios_asignados`, módulo 006) o 
   que están inscritos en alguna de sus clases (módulo 005)
7. El propio socio puede ver y editar sus datos de contacto (no las 
   notas internas ni su historial administrativo)

## Criterios de aceptación
- No se puede completar el alta de socio sin certificado de aptitud 
  médica si la sede lo exige (parametrizable por sede)
- Un socio dado de baja no puede reservar clases ni acceder al portal, 
  pero su historial sigue siendo consultable por admin
- Las notas internas nunca son visibles para el propio socio

## Fuera de alcance en esta feature
- Gestión de la membresía/plan de pago (módulo 004)
- Check-in físico en sede (módulo 009)