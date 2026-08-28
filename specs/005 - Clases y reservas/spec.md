# Spec 005 — Clases y reservas

## Resumen
Gestión del catálogo de clases (horarios, aforo) y el sistema de 
reservas de los socios para asistir a ellas.

## Relación con módulos existentes
- Cada clase pertenece a una `Sede` (módulo 002)
- Cada clase la imparte un `Entrenador` (módulo 006 — dependencia 
  cruzada a resolver cuando lo especifiquemos)
- Solo puede reservar un `Socio` (módulo 003) con `Membresía` (módulo 
  004) activa; si el plan no incluye clases, se marca como "de pago 
  aparte" (relación con módulo 008)

## Requisitos funcionales
1. gestor_sede crea/edita clases: nombre, tipo (ej. yoga, spinning), 
   horario, duración, aforo máximo, sede, entrenador asignado
2. Clases pueden ser puntuales o recurrentes (ej. todos los lunes 9h)
3. Socio con membresía activa puede reservar plaza en una clase, 
   siempre que haya aforo disponible
4. Lista de espera automática cuando la clase está completa; si se 
   libera una plaza, se notifica al primero de la lista 
   (relación con módulo 011, Notificaciones)
5. Cancelación de reserva por el socio, con límite de tiempo antes de 
   la clase (parametrizable) para no penalizar
6. Registro de asistencia real (check-in en la clase), distinto de la 
   reserva — relación con módulo 009 (Control de acceso)
7. gestor_sede ve ocupación de cada clase; entrenador ve solo las 
   clases que imparte
8. Al darse de baja un entrenador (módulo 006), sus clases futuras 
   deben reasignarse a otro entrenador o cancelarse; los socios con 
   reserva confirmada reciben notificación (módulo 011)
9. No se puede asignar un entrenador dado de baja (`activo = false` 
   en módulo 006) a una clase nueva o existente

## Criterios de aceptación
- No se puede reservar una clase si la membresía está congelada o 
  cancelada
- No se puede reservar por encima del aforo máximo (la lista de 
  espera absorbe el exceso)
- Cancelar fuera de plazo queda registrado (para políticas futuras de 
  penalización, no implementadas en v1)

## Fuera de alcance en esta feature
- Cobro de clases sueltas fuera de plan (módulo 008)
- Check-in físico real (módulo 009)
- Envío efectivo de notificaciones (módulo 011, aquí solo se genera 
  el evento)