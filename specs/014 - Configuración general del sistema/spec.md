# Spec 014 — Configuración general del sistema

## Resumen
Parámetros globales y por sede que personalizan el comportamiento del 
sistema sin tocar código.

## Relación con módulos existentes
Afecta a: 002 (aforo/horarios ya editables ahí), 003 (exigencia de 
aptitud médica), 004 (preaviso de cancelación), 005 (límite de 
cancelación de reserva), 008 (reintentos de impago), 011 (plantillas)

## Requisitos funcionales
1. admin configura parámetros globales: moneda, zona horaria, 
   textos legales (política de privacidad, condiciones)
2. Parámetros configurables por sede (ya cubiertos en sus módulos 
   respectivos, aquí solo se centraliza la vista)
3. Panel único de configuración con las secciones agrupadas
4. Historial de cambios de configuración (quién, qué, cuándo)

## Criterios de aceptación
- Solo admin accede a configuración global
- gestor_sede solo edita parámetros de su propia sede (ya definidos 
  en cada módulo, no duplicados aquí)

## Fuera de alcance en esta feature
- Multi-idioma / internacionalización real