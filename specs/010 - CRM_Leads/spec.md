# Spec 010 — CRM / Leads

## Resumen
Gestión de clientes potenciales (leads) desde su captación hasta su 
conversión en socio o descarte.

## Relación con módulos existentes
- Un lead convertido genera un `Socio` (003) con `Usuario` (001)
- Vinculado a una `Sede` (002) de interés

## Requisitos funcionales
1. Alta de lead: nombre, contacto, sede de interés, origen 
   (web, referido, redes)
2. gestor_sede/admin asigna lead a un comercial para seguimiento
3. Registro de interacciones: llamadas, emails, visitas, con notas
4. Estados del lead: nuevo, contactado, en negociación, convertido, 
   descartado
5. Conversión a socio: crea Usuario + Socio automáticamente con los 
   datos del lead
6. Panel de seguimiento: leads por estado, por comercial, tasa de 
   conversión

## Criterios de aceptación
- Un lead descartado puede reabrirse manualmente
- La conversión no duplica datos si el email ya existe como usuario

## Fuera de alcance en esta feature
- Automatización de marketing (emails masivos) — módulo 011 cubre 
  notificaciones puntuales, no campañas