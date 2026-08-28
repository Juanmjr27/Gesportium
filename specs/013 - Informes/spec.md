# Spec 013 — Informes con Ollama

## Resumen
Informes detallados y exportables, con un asistente de IA local 
(Ollama) que genera resúmenes en lenguaje natural.

## Relación con módulos existentes
Agrega datos de: 003, 004, 005, 008, 010 (igual que Dashboard, pero 
en detalle y exportable)

## Requisitos funcionales
1. Informes predefinidos: socios (altas/bajas/histórico), financiero 
   (ingresos/impagos), ocupación de clases, rendimiento comercial (leads)
2. Filtros por rango de fechas y sede
3. Exportación a PDF/Excel
4. Botón "Generar resumen IA": envía los datos del informe a Ollama 
   (local, sin salir del servidor) y devuelve un resumen en texto 
   natural con conclusiones destacadas
5. Solo admin y gestor_sede acceden a informes

## Criterios de aceptación
- El resumen IA nunca inventa cifras no presentes en los datos 
  originales (se valida con prompt estructurado)
- Si Ollama no está disponible, el informe se genera igual, sin resumen

## Fuera de alcance en esta feature
- IA en la nube (siempre local, según Constitution)