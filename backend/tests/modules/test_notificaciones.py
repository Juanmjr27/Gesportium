import uuid
from datetime import date, datetime, timedelta

from app.modules.accesos import service as accesos_service
from app.modules.clases import service as clases_service
from app.modules.clases.models import Clase, Reserva
from app.modules.entrenadores.models import Entrenador
from app.modules.identidad import service as identidad_service
from app.modules.membresias import service as membresias_service
from app.modules.membresias.models import HistorialEstadosMembresia, Membresia, PlanMembresia
from app.modules.notificaciones import service as notificaciones_service
from app.modules.notificaciones.models import Notificacion, PreferenciaNotificacion
from app.modules.pagos import service as pagos_service
from app.modules.socios import service as socios_service
from app.modules.socios.models import Socio
from app.modules.socios.schemas import SocioCreate


def _token_admin(db_session):
    admin = identidad_service.crear_usuario(db_session, "admin-notif@test.com", "password123", "admin", None)
    return identidad_service.create_access_token(admin)


def _token_gestor(db_session, sede_id, email="gestor-notif@test.com"):
    gestor = identidad_service.crear_usuario(db_session, email, "password123", "gestor_sede", sede_id)
    return identidad_service.create_access_token(gestor)


def _crear_socio_completo(db_session, sede_id, email="socio-notif@test.com"):
    usuario = identidad_service.crear_usuario(db_session, email, "password123", "socio", sede_id)
    socio = Socio(
        usuario_id=usuario.id,
        sede_id=sede_id,
        fecha_nacimiento=date(1990, 1, 1),
        telefono="600111222",
        direccion="Calle Falsa 1",
        contacto_emergencia_nombre="Familiar",
        contacto_emergencia_telefono="600333444",
    )
    db_session.add(socio)
    db_session.commit()
    db_session.refresh(socio)
    return usuario, socio


def _crear_plan(db_session, **overrides) -> PlanMembresia:
    datos = {
        "nombre": "Plan Test", "precio": "29.99", "duracion": "mensual", "alcance": "toda_cadena",
        "sede_id": None, "preaviso_cancelacion_dias": 0, "activo": True,
    }
    datos.update(overrides)
    plan = PlanMembresia(**datos)
    db_session.add(plan)
    db_session.commit()
    db_session.refresh(plan)
    return plan


def _crear_membresia(db_session, socio, plan, autor_id, **overrides) -> Membresia:
    return membresias_service.crear_membresia(
        db_session,
        socio_id=socio.id,
        plan=plan,
        fecha_inicio=overrides.get("fecha_inicio", date.today()),
        renovacion_automatica=overrides.get("renovacion_automatica", True),
        autor_id=autor_id,
    )


def _crear_entrenador(db_session, sede_id, email="entrenador-notif@test.com"):
    usuario = identidad_service.crear_usuario(db_session, email, "password123", "entrenador", sede_id)
    entrenador = Entrenador(usuario_id=usuario.id, sede_id=sede_id, activo=True)
    db_session.add(entrenador)
    db_session.commit()
    db_session.refresh(entrenador)
    return entrenador


def _crear_clase(db_session, sede_id, entrenador_id, **overrides) -> Clase:
    datos = {
        "sede_id": sede_id, "entrenador_id": entrenador_id, "nombre": "Yoga", "tipo": "yoga",
        "fecha_hora": datetime.utcnow() + timedelta(days=1), "duracion_minutos": 60,
        "aforo_maximo": 1, "recurrente": False, "regla_recurrencia": None, "estado": "activa",
    }
    datos.update(overrides)
    clase = Clase(**datos)
    db_session.add(clase)
    db_session.commit()
    db_session.refresh(clase)
    return clase


# --- Servicio: encolar / preferencias / worker ---------------------------

def test_encolar_notificacion_renderiza_plantilla_y_queda_pendiente(db_session, sede_id):
    usuario, _ = _crear_socio_completo(db_session, sede_id)

    notificacion = notificaciones_service.encolar_notificacion(
        db_session, usuario.id, "bienvenida",
    )

    assert notificacion.estado == "pendiente"
    assert notificacion.intentos == 0
    assert "Bienvenido" in notificacion.asunto


def test_alta_de_socio_encola_notificacion_de_bienvenida(db_session, sede_id):
    autor = identidad_service.crear_usuario(db_session, "autor-alta-notif@test.com", "password123", "admin", None)
    usuario_socio = identidad_service.crear_usuario(db_session, "nuevo-socio-notif@test.com", "password123", "socio", sede_id)

    socios_service.crear_socio(
        db_session,
        SocioCreate(
            usuario_id=usuario_socio.id,
            sede_id=sede_id,
            fecha_nacimiento=date(1990, 1, 1),
            telefono="600111222",
            direccion="Calle Falsa 1",
            contacto_emergencia_nombre="Familiar",
            contacto_emergencia_telefono="600333444",
        ),
        autor_id=autor.id,
    )

    notificacion = (
        db_session.query(Notificacion)
        .filter(Notificacion.usuario_id == usuario_socio.id, Notificacion.tipo == "bienvenida")
        .first()
    )
    assert notificacion is not None


def test_membresia_vencida_sin_renovacion_automatica_transiciona_y_notifica(db_session, sede_id):
    usuario, socio = _crear_socio_completo(db_session, sede_id)
    plan = _crear_plan(db_session)
    membresia = _crear_membresia(db_session, socio, plan, autor_id=usuario.id, renovacion_automatica=False)
    membresia.fecha_proxima_renovacion = date.today() - timedelta(days=1)
    db_session.commit()

    vencidas = membresias_service.ejecutar_job_vencimiento(db_session)

    assert len(vencidas) == 1
    db_session.refresh(membresia)
    assert membresia.estado == "vencida"

    historial = (
        db_session.query(HistorialEstadosMembresia)
        .filter(HistorialEstadosMembresia.membresia_id == membresia.id, HistorialEstadosMembresia.estado_nuevo == "vencida")
        .first()
    )
    assert historial is not None
    assert historial.estado_anterior == "activa"

    notificacion = (
        db_session.query(Notificacion)
        .filter(Notificacion.usuario_id == usuario.id, Notificacion.tipo == "membresia_vencida")
        .first()
    )
    assert notificacion is not None


def test_membresia_vencida_no_afecta_a_renovacion_automatica(db_session, sede_id):
    usuario, socio = _crear_socio_completo(db_session, sede_id)
    plan = _crear_plan(db_session)
    membresia = _crear_membresia(db_session, socio, plan, autor_id=usuario.id, renovacion_automatica=True)
    membresia.fecha_proxima_renovacion = date.today() - timedelta(days=1)
    db_session.commit()

    vencidas = membresias_service.ejecutar_job_vencimiento(db_session)

    assert vencidas == []
    db_session.refresh(membresia)
    assert membresia.estado == "activa"


def test_marketing_desactivado_no_encola(db_session, sede_id):
    usuario, _ = _crear_socio_completo(db_session, sede_id)
    notificaciones_service.actualizar_preferencia(db_session, usuario.id, marketing_activo=False)

    resultado = notificaciones_service.encolar_notificacion(
        db_session, usuario.id, "marketing", mensaje="Oferta especial",
    )

    assert resultado is None
    assert db_session.query(Notificacion).filter(Notificacion.usuario_id == usuario.id).count() == 0


def test_notificacion_transaccional_se_encola_aunque_marketing_este_desactivado(db_session, sede_id):
    usuario, _ = _crear_socio_completo(db_session, sede_id)
    notificaciones_service.actualizar_preferencia(db_session, usuario.id, marketing_activo=False)

    notificacion = notificaciones_service.encolar_notificacion(db_session, usuario.id, "bienvenida")

    assert notificacion is not None
    assert notificacion.estado == "pendiente"


def test_procesar_cola_marca_enviada_si_exitoso(db_session, sede_id):
    usuario, _ = _crear_socio_completo(db_session, sede_id)
    notificacion = notificaciones_service.encolar_notificacion(db_session, usuario.id, "bienvenida")

    procesadas = notificaciones_service.procesar_cola_notificaciones(
        db_session, resultados_envio={notificacion.id: True}
    )

    assert len(procesadas) == 1
    db_session.refresh(notificacion)
    assert notificacion.estado == "enviada"
    assert notificacion.fecha_envio is not None


def test_procesar_cola_reintenta_y_falla_tras_agotar_intentos(db_session, sede_id):
    usuario, _ = _crear_socio_completo(db_session, sede_id)
    notificacion = notificaciones_service.encolar_notificacion(db_session, usuario.id, "bienvenida")

    for _ in range(notificaciones_service.MAX_REINTENTOS - 1):
        notificaciones_service.procesar_cola_notificaciones(
            db_session, resultados_envio={notificacion.id: False}
        )
        db_session.refresh(notificacion)
        assert notificacion.estado == "pendiente"

    notificaciones_service.procesar_cola_notificaciones(
        db_session, resultados_envio={notificacion.id: False}
    )
    db_session.refresh(notificacion)
    assert notificacion.estado == "fallida"
    assert notificacion.intentos == notificaciones_service.MAX_REINTENTOS


def test_historial_y_preferencias_via_api(client, db_session, sede_id):
    usuario, _ = _crear_socio_completo(db_session, sede_id)
    notificaciones_service.encolar_notificacion(db_session, usuario.id, "bienvenida")
    token = identidad_service.create_access_token(usuario)

    historial = client.get("/notificaciones", headers={"Authorization": f"Bearer {token}"})
    assert historial.status_code == 200
    assert len(historial.json()) == 1

    prefs = client.put(
        "/notificaciones/preferencias",
        headers={"Authorization": f"Bearer {token}"},
        json={"marketing_activo": False},
    )
    assert prefs.status_code == 200
    assert prefs.json()["marketing_activo"] is False

    preferencia = db_session.get(PreferenciaNotificacion, usuario.id)
    assert preferencia.marketing_activo is False


def test_usuario_no_ve_notificaciones_ajenas(client, db_session, sede_id):
    usuario_a, _ = _crear_socio_completo(db_session, sede_id, "socio-a-notif@test.com")
    usuario_b, _ = _crear_socio_completo(db_session, sede_id, "socio-b-notif@test.com")
    notificaciones_service.encolar_notificacion(db_session, usuario_a.id, "bienvenida")

    token_b = identidad_service.create_access_token(usuario_b)
    response = client.get("/notificaciones", headers={"Authorization": f"Bearer {token_b}"})
    assert response.status_code == 200
    assert response.json() == []


# --- Ganchos conectados desde otros módulos -------------------------------

def test_pago_fallido_encola_notificacion_al_socio(db_session, sede_id):
    usuario, socio = _crear_socio_completo(db_session, sede_id)
    plan = _crear_plan(db_session)
    membresia = _crear_membresia(db_session, socio, plan, autor_id=usuario.id)
    pago = pagos_service.generar_cobro_pendiente(db_session, membresia, plan)

    for _ in range(pagos_service.MAX_REINTENTOS):
        pago = pagos_service.intentar_cobro(db_session, pago, exitoso=False)

    assert pago.estado == "fallido"
    notificacion = (
        db_session.query(Notificacion)
        .filter(Notificacion.usuario_id == usuario.id, Notificacion.tipo == "pago_fallido")
        .first()
    )
    assert notificacion is not None
    assert pago.concepto in notificacion.cuerpo


def test_membresia_proxima_a_vencer_encola_notificacion(db_session, sede_id):
    usuario, socio = _crear_socio_completo(db_session, sede_id)
    plan = _crear_plan(db_session)
    membresia = _crear_membresia(db_session, socio, plan, autor_id=usuario.id)
    membresia.fecha_proxima_renovacion = date.today() + timedelta(days=2)
    db_session.commit()

    membresias_service.ejecutar_job_renovacion(db_session)

    notificacion = (
        db_session.query(Notificacion)
        .filter(Notificacion.usuario_id == usuario.id, Notificacion.tipo == "membresia_proxima_vencer")
        .first()
    )
    assert notificacion is not None


def test_aforo_superado_notifica_a_gestor_sede(db_session, sede_id):
    from app.modules.sedes.models import Sede

    sede = db_session.get(Sede, sede_id)
    sede.aforo_maximo = 1
    db_session.commit()

    gestor = identidad_service.crear_usuario(db_session, "gestor-aforo@test.com", "password123", "gestor_sede", sede_id)
    plan = _crear_plan(db_session)
    usuario_a, socio_a = _crear_socio_completo(db_session, sede_id, "socio-aforo-a@test.com")
    _crear_membresia(db_session, socio_a, plan, autor_id=usuario_a.id)
    usuario_b, socio_b = _crear_socio_completo(db_session, sede_id, "socio-aforo-b@test.com")
    _crear_membresia(db_session, socio_b, plan, autor_id=usuario_b.id)

    accesos_service.registrar_checkin(db_session, socio_a.id, sede_id)
    accesos_service.registrar_checkin(db_session, socio_b.id, sede_id)

    notificacion = (
        db_session.query(Notificacion)
        .filter(Notificacion.usuario_id == gestor.id, Notificacion.tipo == "aforo_superado")
        .first()
    )
    assert notificacion is not None


def test_promocion_lista_espera_notifica_plaza_liberada(db_session, sede_id):
    entrenador = _crear_entrenador(db_session, sede_id)
    clase = _crear_clase(db_session, sede_id, entrenador.id, aforo_maximo=1)

    usuario_a, socio_a = _crear_socio_completo(db_session, sede_id, "socio-a-lista@test.com")
    usuario_b, socio_b = _crear_socio_completo(db_session, sede_id, "socio-b-lista@test.com")

    reserva_a = clases_service.reservar_clase(db_session, clase, socio_a.id)
    reserva_b = clases_service.reservar_clase(db_session, clase, socio_b.id)
    assert reserva_b.estado == "lista_espera"

    clases_service.cancelar_reserva(db_session, reserva_a, clase)

    notificacion = (
        db_session.query(Notificacion)
        .filter(Notificacion.usuario_id == usuario_b.id, Notificacion.tipo == "plaza_liberada")
        .first()
    )
    assert notificacion is not None


def test_reasignar_por_baja_entrenador_notifica_a_socios_con_reserva(db_session, sede_id):
    entrenador_baja = _crear_entrenador(db_session, sede_id, "entrenador-baja-notif@test.com")
    nuevo_entrenador = _crear_entrenador(db_session, sede_id, "entrenador-nuevo-notif@test.com")
    clase = _crear_clase(
        db_session, sede_id, entrenador_baja.id, aforo_maximo=5,
        fecha_hora=datetime.utcnow() + timedelta(days=1),
    )
    usuario, socio = _crear_socio_completo(db_session, sede_id, "socio-reasignado@test.com")
    clases_service.reservar_clase(db_session, clase, socio.id)

    clases_service.reasignar_por_baja_entrenador(db_session, entrenador_baja.id, "reasignar", nuevo_entrenador.id)

    notificacion = (
        db_session.query(Notificacion)
        .filter(Notificacion.usuario_id == usuario.id, Notificacion.tipo == "clase_reasignada")
        .first()
    )
    assert notificacion is not None


def test_cancelar_clases_por_baja_entrenador_notifica_cancelacion(db_session, sede_id):
    entrenador_baja = _crear_entrenador(db_session, sede_id, "entrenador-baja-cancel@test.com")
    clase = _crear_clase(
        db_session, sede_id, entrenador_baja.id, aforo_maximo=5,
        fecha_hora=datetime.utcnow() + timedelta(days=1),
    )
    usuario, socio = _crear_socio_completo(db_session, sede_id, "socio-cancelado@test.com")
    clases_service.reservar_clase(db_session, clase, socio.id)

    clases_service.reasignar_por_baja_entrenador(db_session, entrenador_baja.id, "cancelar", None)

    notificacion = (
        db_session.query(Notificacion)
        .filter(Notificacion.usuario_id == usuario.id, Notificacion.tipo == "clase_cancelada")
        .first()
    )
    assert notificacion is not None
