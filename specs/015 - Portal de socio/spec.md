# Spec 015 — Portal de socio

## Resumen
No es un módulo de backend nuevo — es la especificación del 
**frontend orientado al socio**, que consume los endpoints ya 
definidos en los módulos 001-014.

## Relación con módulos existentes
Consume: 001 (login), 003 (perfil), 004 (membresía), 005 (reservas), 
007 (rutinas/nutrición), 008 (pagos/facturas), 009 (historial accesos)

## Requisitos funcionales
1. Login/registro público
2. Ver y editar datos de contacto propios
3. Ver estado de membresía, congelar/cancelar (solicitud)
4. Reservar/cancelar clases, ver lista de espera
5. Ver rutinas y planes nutricionales asignados, marcar cumplimiento
6. Ver historial de pagos y descargar facturas
7. Ver historial de accesos propio
8. Diseño responsive (móvil primero, según Constitution)

## Criterios de aceptación
- Todas las acciones respetan los permisos ya definidos en cada 
  módulo backend (el frontend no reimplementa seguridad, solo la 
  respeta)
- Funciona correctamente en móvil (viewport reducido)

## Fuera de alcance en esta feature
- App nativa (solo web responsive, según Constitution)