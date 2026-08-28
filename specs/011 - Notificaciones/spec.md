# Spec 011 — Notificaciones

## Resumen
Envío de avisos automáticos por email/push, disparados por eventos 
de otros módulos (clase liberada, pago fallido, membresía por vencer).

## Relación con módulos existentes
Resuelve eventos pendientes de: 005 (lista de espera, reasignación o 
cancelación de clase por baja de entrenador), 008 (pago fallido), 
004 (membresía próxima a vencer — umbral definido en 004; membresía 
vencida)

## Requisitos funcionales
1. Plantillas de notificación por tipo de evento
2. Canales: email (v1), push (preparado pero no implementado)
3. Eventos disparadores: plaza liberada, pago fallido, membresía 
   próxima a vencer, membresía vencida (expiración efectiva), 
   bienvenida al alta
4. Cola de envío con reintentos si falla
5. Socio puede desactivar notificaciones no esenciales (marketing), 
   no las transaccionales (pago, acceso)
6. Historial de notificaciones enviadas por socio

## Criterios de aceptación
- Un fallo de envío no bloquea la acción que lo disparó (ej. el pago 
  falla igual aunque el email de aviso no se envíe)
- Notificaciones transaccionales no se pueden desactivar

## Fuera de alcance en esta feature
- Push real (solo estructura preparada)
- Campañas de marketing masivo