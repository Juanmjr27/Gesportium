# Spec 012 — Dashboard principal

## Resumen
Vista resumen con las métricas clave del negocio, distinta de los 
informes detallados (módulo 013).

## Relación con módulos existentes
Agrega datos de: 003 (socios), 004 (membresías), 005 (clases), 
008 (pagos), 010 (leads)

## Requisitos funcionales
1. KPIs mostrados: socios activos, altas/bajas del mes, ingresos del 
   mes, ocupación media de clases, tasa de conversión de leads
2. Filtro por sede (gestor_sede solo ve la suya) o global (admin)
3. Comparativa con periodo anterior (mes/mes, variación %)
4. Actualización de datos casi en tiempo real (no histórico complejo, 
   eso es el módulo 013)

## Criterios de aceptación
- gestor_sede nunca ve datos agregados de otras sedes
- Los KPIs se calculan sobre datos reales, no cacheados más de 15 min

## Fuera de alcance en esta feature
- Informes exportables/detallados (módulo 013)