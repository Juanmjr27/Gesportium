# Spec 016 — Asistente IA conversacional
 
## Resumen
Chat con IA local (Ollama) accesible desde el portal de socio, para 
dudas generales y generación de borradores de plan nutricional/rutina 
que requieren aprobación del entrenador.
 
## Relación con módulos existentes
- Requiere `Socio` (003) autenticado con `Membresía` (004) activa
- Los borradores generados se integran con `Rutinas`/`Planes 
  nutricionales` (007), pendientes de aprobación del `Entrenador` (006)
## Requisitos funcionales
1. Chat conversacional para dudas generales (horarios, qué incluye 
   su plan, cómo reservar) — respuesta directa, sin aprobación
2. Solicitud de borrador de plan nutricional o rutina personalizada 
   mediante un **cuestionario guiado paso a paso** (wizard), no un 
   formulario libre: el asistente combina los datos del perfil del 
   socio (edad, objetivo, membresía) con los datos recogidos en el 
   cuestionario (peso, altura, preferencias, disponibilidad, etc.) 
   para generar una propuesta. Detalle completo del cuestionario en 
   la sección "Cuestionario guiado de solicitud de borrador"
3. Todo borrador generado por IA queda en estado "pendiente de 
   revisión" — NO se activa como plan real hasta que el entrenador 
   asignado lo apruebe o edite
4. Entrenador ve, para cada borrador pendiente de sus socios, **tanto 
   los datos estructurados enviados por el socio como el borrador 
   generado por el asistente**, lado a lado, y puede aprobar tal cual, 
   editar y aprobar, o rechazar pidiendo más datos. Detalle en la 
   sección "Vista del entrenador"
5. Historial de conversación por socio
6. Aviso visible al socio: "Esto es un borrador generado por IA, 
   pendiente de revisión profesional" mientras no esté aprobado
## Cuestionario guiado de solicitud de borrador
 
Sustituye a un formulario libre. Se presenta como asistente paso a 
paso, un bloque de preguntas por pantalla, con barra de progreso y 
opción de volver atrás sin perder lo ya introducido.
 
### Paso 0 — Tipo de borrador
 
| Campo | Tipo | Validación |
|---|---|---|
| `tipo_borrador` | selección única: `rutina` \| `plan_nutricional` | obligatorio |
 
El valor elegido determina qué preguntas de los pasos 2 y 3 se muestran.
 
### Paso 1 — Datos del perfil (autocompletados, no editables aquí)
 
**Corrección (2026-08-24):** la versión anterior de este paso incluía 
`nombre` y `sexo` como si vinieran del perfil del socio, pero `Socio` 
(003) nunca ha tenido ninguno de los dos. Se resuelven de forma 
distinta según si el dato importa para el borrador o no:
- `nombre`: no influye en el contenido del borrador (ni rutina ni 
  plan nutricional cambian por el nombre) — se retira sin más.
- `sexo`: sí influye en un borrador de nutrición/rutina bien hecho, 
  así que no se retira — se mueve al Paso 2 como una pregunta más del 
  cuestionario (como peso/altura), en vez de tratarlo como un dato ya 
  guardado en un perfil que no lo tiene. Ver Paso 2 más abajo.
Se muestran como confirmación, no como campos vacíos, para no volver a 
preguntar lo que el club ya sabe:
 
| Campo | Origen | Comportamiento |
|---|---|---|
| `edad` | perfil del socio (`Socio.fecha_nacimiento`) | solo lectura |
| `tipo_membresia` | membresía activa del socio | solo lectura |
 
**Caso borde:** si al socio le falta `fecha_nacimiento` en el perfil 
(p. ej. socio antiguo sin ese dato registrado), el paso 1 pasa a 
pedirlo como campo editable obligatorio en ese momento, en lugar de 
bloquear el flujo. El dato introducido se guarda también en el perfil 
del socio (vía el endpoint de actualización ya existente de 003) para 
no volver a pedirlo.
 
### Paso 2 — Datos físicos
 
| Campo | Tipo | Validación | Aplica a |
|---|---|---|---|
| `sexo` | selección única: `masculino` \| `femenino` \| `prefiero_no_decirlo` | obligatorio | rutina y plan nutricional |
| `peso_kg` | numérico | obligatorio, 20–300 | rutina y plan nutricional |
| `altura_cm` | numérico | obligatorio, 100–250 | rutina y plan nutricional |
| `nivel_actividad_actual` | selección única: `sedentario` \| `activo` \| `muy_activo` | obligatorio | solo rutina |
| `restricciones_medicas` | texto corto / chips predefinidos (alergias, intolerancias, otro) | opcional | solo plan nutricional |
 
`sexo` es obligatorio para ambos tipos porque afecta directamente a la 
calidad del borrador (necesidades calóricas, composición corporal), 
pero incluye `prefiero_no_decirlo` para que nadie se vea forzado a 
elegir entre solo dos opciones.
 
### Paso 3 — Preferencias
 
**Si `tipo_borrador = rutina`:**
 
| Campo | Tipo | Validación |
|---|---|---|
| `dias_disponibles_semana` | numérico | obligatorio, 1–7 |
| `equipamiento` | selección única: `gimnasio_completo` \| `casa_basico` \| `sin_material` | obligatorio |
| `lesiones_zonas_evitar` | texto corto | opcional |
 
**Si `tipo_borrador = plan_nutricional`:**
 
| Campo | Tipo | Validación |
|---|---|---|
| `preferencia_alimentaria` | selección única: `omnivoro` \| `vegetariano` \| `vegano` \| `otro` | obligatorio |
| `comidas_al_dia` | numérico | obligatorio, 2–6 |
| `alimentos_excluir` | texto corto | opcional |
 
### Paso 4 — Objetivo
 
| Campo | Tipo | Validación |
|---|---|---|
| `objetivo_principal` | chips de selección única: `perder_peso` \| `ganar_masa_muscular` \| `mantenimiento` \| `rendimiento_deportivo` \| `salud_general` | obligatorio |
| `objetivo_detalle` | texto libre opcional (p. ej. "preparar una carrera en 3 meses") | opcional, máx. 280 caracteres |
 
Se conserva un campo de texto libre, pero acotado y opcional — no es 
la única fuente de información del objetivo.
 
### Paso 5 — Resumen y envío
 
Se muestra un resumen de todos los datos introducidos (pasos 1 a 4) 
antes de enviar. El socio puede volver a cualquier paso para corregir 
algo. Al confirmar, se genera el borrador (rutina o plan) mediante el 
asistente y se envía a revisión del entrenador junto con todos los 
datos estructurados.
 
Estado resultante: `borrador_pendiente_revision`.
 
## Vista del entrenador
 
Cuando el entrenador abre una solicitud pendiente, ve **ambas cosas a 
la vez**, no solo el borrador redactado:
 
**Panel izquierdo — Datos estructurados del socio** (los mismos 
campos de los pasos 1–4, en formato lectura): edad, membresía, peso, 
altura, nivel de actividad o restricciones médicas, días disponibles 
o preferencia alimentaria, objetivo y detalle. Nota de implementación: 
`edad` y `tipo_membresia` NO forman parte de `datos_cuestionario` (ese 
JSON solo guarda las respuestas del wizard, pasos 2-4) — hay que 
obtenerlos del perfil del socio por separado al construir esta 
pantalla, igual que hace el backend al generar el borrador.
 
**Panel derecho — Borrador generado por el asistente**: la rutina o 
el plan nutricional propuesto, editable directamente por el 
entrenador (no solo aprobar/rechazar en bloque).
 
**Acciones disponibles para el entrenador:**
 
| Acción | Efecto |
|---|---|
| Aprobar tal cual | El borrador pasa a activo, se notifica al socio |
| Editar y aprobar | El entrenador modifica el borrador en el panel derecho; al guardar, pasa a activo |
| Rechazar / pedir más datos | Vuelve al socio con un motivo, sin activar nada |
 
Mostrar los datos en crudo junto al borrador le da al entrenador el 
contexto necesario para juzgar si el borrador generado por el 
asistente tiene sentido para ese socio en concreto, en vez de 
aprobarlo a ciegas basándose solo en el texto ya redactado.
 
## Flujo de datos (resumen)
 
1. Socio pulsa "Solicitar un borrador" → completa el wizard de 5 pasos.
2. Al confirmar, el asistente genera el borrador y lo guarda junto con 
   los datos estructurados → estado `borrador_pendiente_revision`.
3. El entrenador recibe notificación, abre la solicitud → ve datos + 
   borrador lado a lado.
4. El entrenador aprueba, edita y aprueba, o rechaza.
5. Si se aprueba → estado `activo`, se notifica al socio. Si se 
   rechaza → estado `rechazado`, se notifica al socio con el motivo y 
   puede volver a solicitar.
## Criterios de aceptación
- Ningún borrador de plan nutricional/rutina llega al socio como 
  definitivo sin aprobación humana
- El asistente no accede a datos de otros socios, solo los propios
- Si Ollama no responde, el chat informa el fallo sin bloquear el 
  resto de la app
- El cuestionario guiado no permite avanzar de paso con campos 
  obligatorios vacíos o fuera de rango
- El entrenador siempre ve los datos estructurados del socio junto al 
  borrador generado, no solo el texto del borrador
## Fuera de alcance en esta feature
- Diagnóstico médico o consejo de salud fuera de nutrición/ejercicio 
  general
- Voz/audio (solo texto)
 