# Spec 017 — Panel de administración

## Resumen
Frontend de gestión usado por admin, gestor_sede y entrenador — la 
interfaz para operar el negocio, distinta del portal de socio (015).

## Relación con módulos existentes
Consume: 001 (login), 002 (sedes), 003 (socios), 004 (membresías), 
005 (clases), 006 (entrenadores), 007 (planes), 008 (pagos), 
009 (accesos), 010 (leads), 012 (dashboard), 013 (informes), 
014 (configuración)

## Requisitos funcionales
1. Login (comparte lógica con 001, distinta interfaz que el portal)
2. Dashboard inicial con KPIs (módulo 012)
3. Gestión CRUD visual de: sedes, socios (con ficha de detalle, ver 
   FR8), membresías, clases, entrenadores, pagos/remesas, leads
4. Vistas filtradas por rol: gestor_sede solo ve su sede, entrenador 
   solo sus clases/socios asignados
5. Acceso a informes exportables y resumen IA (módulo 013)
6. Pantalla de configuración general (módulo 014, solo admin)
7. Diseño desktop-first (uso principalmente en oficina/recepción), 
   pero funcional en tablet
8. Ficha de socio: vista de detalle de un socio individual, accesible 
   desde la pantalla de Socios (FR3). Admin/gestor_sede pueden abrir 
   la ficha de cualquier socio (de su alcance según FR4); entrenador 
   solo la de sus socios asignados. Todos los roles ven en modo 
   consulta: datos personales, sede, estado, membresía y entrenador 
   asignado del socio, además de sus rutinas y planes nutricionales 
   (módulo 007). Las notas internas del socio (003, notas internas — 
   solo admin/gestor_sede) no se muestran en esta ficha a ningún rol 
   que no las viera ya. Además del modo consulta común, el entrenador 
   puede crear y editar rutinas y planes nutricionales del socio 
   abierto (reutilizando los endpoints de creación/edición de 007), 
   únicamente si el socio está en su lista de asignados (006). Ningún 
   rol puede dar de baja al socio ni cambiarlo de sede desde esta 
   pantalla (eso sigue perteneciendo a las acciones ya definidas en 
   003 FR4/FR5, restringidas a admin/gestor_sede). Fuera de alcance 
   por ahora: historial de pagos y de reservas de clases dentro de la 
   ficha.

## Criterios de aceptación
- Todas las vistas respetan permisos ya definidos en cada módulo 
  backend
- Un gestor_sede nunca ve datos de otra sede en ninguna pantalla
- La ficha de socio nunca muestra notas internas a un rol que no las 
  tuviera ya visibles en otra pantalla
- Un entrenador no puede abrir la ficha de un socio que no tiene 
  asignado, ni crear/editar rutinas o planes desde ninguna ficha 
  salvo la de sus socios asignados
- Ningún rol puede dar de baja ni transferir de sede a un socio desde 
  la ficha

## Fuera de alcance en esta feature
- Versión móvil nativa
- Historial de pagos dentro de la ficha de socio
- Historial de reservas de clases dentro de la ficha de socio