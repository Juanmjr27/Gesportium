# Spec 002 — Sedes

## Resumen
Gestión de las sedes físicas de la cadena de gimnasios. Es la base 
sobre la que se organizan socios, entrenadores, clases y pagos de 
cada ubicación.

## Relación con módulos existentes
Este módulo se apoya en el modelo `Usuario` del módulo 001 
(campo `sede_id`), que ya prevé que cada usuario (excepto admin) 
pertenezca a una sede concreta.

## Requisitos funcionales
1. Alta, edición y baja de sedes — solo rol **admin**
2. Cada sede tiene: nombre, dirección, ciudad, teléfono de contacto, 
   horario de apertura/cierre, aforo máximo simultáneo, estado 
   (activa/inactiva)
3. El rol **gestor_sede** puede ver y editar los datos de SU propia 
   sede (no crear ni eliminar sedes, no ver datos de otras)
4. El rol **admin** puede ver el listado completo de todas las sedes 
   y sus datos
5. Al desactivar una sede, no se elimina (baja lógica) — se conserva 
   el histórico de socios/clases asociados
6. Listado de sedes visible públicamente en el portal (para que un 
   futuro socio elija dónde inscribirse), mostrando solo datos básicos 
   (nombre, dirección, horario)

## Criterios de aceptación
- Un gestor_sede no puede editar ni ver datos de una sede que no sea 
  la suya
- No se puede eliminar físicamente una sede con socios activos 
  asociados — solo desactivar
- El listado público no expone datos sensibles (ej. aforo interno, 
  ingresos)

## Fuera de alcance en esta feature
- Transferencia de socios entre sedes (se define en el módulo Socios)
- Estadísticas/ocupación en tiempo real por sede (se define en Dashboard)