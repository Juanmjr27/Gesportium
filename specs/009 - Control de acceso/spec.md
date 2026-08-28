# Spec 009 — Control de acceso

## Resumen
Registro de entrada/salida física de socios en la sede, y su relación 
con la asistencia a clases reservadas.

## Relación con módulos existentes
- Valida `Membresía` (004) activa antes de permitir acceso
- Si el socio tenía `Reserva` (005), marca su `Asistencia`

## Requisitos funcionales
1. Check-in mediante código QR o número de socio en tótem/tablet de 
   la sede
2. Valida membresía activa antes de permitir el acceso
3. Si coincide con una clase reservada en ese momento, marca 
   asistencia automáticamente
4. Registro de aforo en tiempo real por sede
5. gestor_sede ve ocupación actual de su sede
6. Historial de accesos por socio (fecha, hora, sede)

## Criterios de aceptación
- Membresía congelada o cancelada bloquea el check-in
- Si se supera el aforo máximo de la sede, se avisa a gestor_sede 
  (no bloquea automáticamente, decisión manual)

## Fuera de alcance en esta feature
- Hardware físico real (lector QR, torno) — solo API que lo soportaría