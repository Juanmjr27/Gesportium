# Spec 004 — Membresías

## Resumen
Gestión de los planes de suscripción de los socios: qué tipos de 
membresía existen, su ciclo de vida (alta, renovación, congelación, 
cancelación) y su relación con el acceso al gimnasio.

## Relación con módulos existentes
- Cada membresía pertenece a un `Socio` (módulo 003)
- Cada plan de membresía puede estar limitado a una `Sede` (módulo 002) 
  o ser válido en toda la cadena
- El pago asociado a la membresía se gestiona en el módulo 008 
  (Pagos y facturación) — aquí solo se define el plan y su estado. 
  El módulo 008 puede congelar automáticamente una membresía por 
  impago (ver FR4) mediante el contrato interno definido en el plan
- Emite eventos consumidos por `Notificaciones` (módulo 011): 
  membresía próxima a vencer, bienvenida al alta

## Requisitos funcionales
1. admin puede crear/editar planes de membresía: nombre, precio, 
   duración (mensual/trimestral/anual), acceso (una sede / toda la 
   cadena), clases incluidas o de pago aparte
2. Alta de membresía a un socio: se le asigna un plan concreto con 
   fecha de inicio
3. Renovación automática configurable por socio (activada/desactivada). 
   El cobro de renovación (módulo 008) se omite mientras la 
   membresía esté en estado `congelada`
4. Congelación temporal: pausa la membresía sin perder antigüedad, 
   con fecha de inicio y fin de la pausa. El origen de la 
   congelación puede ser manual (socio/gestor_sede, ej. lesión o 
   viaje) o automático por impago (módulo 008, tras N reintentos 
   fallidos); una congelación por impago solo puede reactivarse 
   cuando el pago pendiente se resuelve (módulo 008)
5. Cancelación: el socio o gestor_sede puede solicitar baja de la 
   membresía, con periodo de preaviso configurable por plan
6. Estado de la membresía siempre visible: activa, congelada, 
   cancelada, vencida
7. El socio ve su propia membresía (plan, próxima renovación, estado); 
   no puede editarla directamente, solo solicitar cambios
8. Aviso de renovación próxima: se considera "próxima a vencer" una 
   membresía cuya `fecha_proxima_renovacion` está a 3 días o menos 
   (parametrizable por plan); el job diario de renovación calcula 
   este umbral y dispara el evento consumido por Notificaciones 
   (módulo 011)

## Criterios de aceptación
- Una membresía congelada no permite reservar clases hasta reactivarse
- No se puede cancelar una membresía con pagos pendientes sin resolver 
  (dependencia con módulo 008)
- El cambio de estado de una membresía queda registrado con fecha y 
  quién lo hizo (trazabilidad, ya definida en la Constitution)
- Una membresía congelada por impago no puede reactivarse mediante 
  `POST /membresias/{id}/reactivar` hasta que el módulo 008 confirme 
  que no hay pagos pendientes

## Fuera de alcance en esta feature
- Procesamiento real del cobro (módulo 008)
- Descuentos por referidos (módulo CRM, 010)