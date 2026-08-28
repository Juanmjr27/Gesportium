# Spec 008 — Pagos y facturación

## Resumen
Cobro de membresías, generación de facturas y gestión de impagos.

## Relación con módulos existentes
- Cobra `Membresías` (004) según su ciclo de renovación, omitiendo 
  las que estén en estado `congelada`
- Resuelve dependencias pendientes: validación de pagos antes de 
  cancelar membresía (004), cobro de clases sueltas (005)
- Al agotar los reintentos de un impago, congela la membresía (004) 
  llamando a su endpoint `POST /membresias/{id}/congelar` con 
  `origen=impago` (nunca por escritura directa)
- Emite el evento "pago fallido" consumido por `Notificaciones` 
  (módulo 011)

## Requisitos funcionales
1. Generación automática de cobro en cada renovación de membresía
2. Pasarela de pago simulada (no real, según Constitution)
3. Factura generada por cada cobro exitoso (PDF descargable)
4. Gestión de impagos: reintentos, marcado de membresía en riesgo
5. Remesas: agrupación de cobros por sede/fecha para conciliación
6. Socio ve su historial de pagos y descarga facturas
7. gestor_sede ve pagos/impagos de su sede; admin ve todo

## Criterios de aceptación
- Un impago tras N reintentos congela automáticamente la membresía 
  (registrando `origen=impago` en el módulo 004, distinguible de una 
  congelación manual)
- No se puede facturar dos veces el mismo periodo
- No se genera cobro de renovación para una membresía en estado 
  `congelada`
- Las facturas no se editan una vez emitidas (solo se anulan y 
  reemiten)

## Fuera de alcance en esta feature
- Integración con pasarela de pago real (Stripe, Redsys...)