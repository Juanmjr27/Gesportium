import uuid
from datetime import date, datetime, time, timedelta

import pytest

from app.modules.identidad import service as identidad_service
from app.modules.membresias import service as membresias_service
from app.modules.membresias.models import CongelacionMembresia, Membresia, PlanMembresia
from app.modules.pagos import service as pagos_service
from app.modules.pagos.models import Factura, HistorialAccionPago, Pago
from app.modules.sedes.models import Sede
from app.modules.socios.models import Socio


def _token_admin(db_session):
    admin = identidad_service.crear_usuario(db_session, "admin-pagos@test.com", "password123", "admin", None)
    return identidad_service.create_access_token(admin)


def _token_gestor(db_session, sede_id, email="gestor-pagos@test.com"):
    gestor = identidad_service.crear_usuario(db_session, email, "password123", "gestor_sede", sede_id)
    return identidad_service.create_access_token(gestor)


def _crear_socio_completo(db_session, sede_id, email="socio-pagos@test.com"):
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


def test_cobro_exitoso_genera_factura(db_session, sede_id):
    usuario, socio = _crear_socio_completo(db_session, sede_id)
    plan = _crear_plan(db_session)
    membresia = _crear_membresia(db_session, socio, plan, autor_id=usuario.id)

    pago = pagos_service.generar_cobro_pendiente(db_session, membresia, plan)
    pago = pagos_service.intentar_cobro(db_session, pago, exitoso=True)

    assert pago.estado == "exitoso"
    factura = db_session.query(Factura).filter(Factura.pago_id == pago.id).first()
    assert factura is not None
    assert factura.numero.startswith("F-")


def test_no_se_puede_facturar_dos_veces_el_mismo_periodo(db_session, sede_id):
    usuario, socio = _crear_socio_completo(db_session, sede_id)
    plan = _crear_plan(db_session)
    membresia = _crear_membresia(db_session, socio, plan, autor_id=usuario.id)

    pagos_service.generar_cobro_pendiente(db_session, membresia, plan)
    with pytest.raises(ValueError):
        pagos_service.generar_cobro_pendiente(db_session, membresia, plan)


def test_reintentos_agotados_congela_membresia_por_impago(db_session, sede_id):
    usuario, socio = _crear_socio_completo(db_session, sede_id)
    plan = _crear_plan(db_session)
    membresia = _crear_membresia(db_session, socio, plan, autor_id=usuario.id)

    pago = pagos_service.generar_cobro_pendiente(db_session, membresia, plan)
    for _ in range(pagos_service.MAX_REINTENTOS - 1):
        pago = pagos_service.intentar_cobro(db_session, pago, exitoso=False)
        assert pago.estado == "pendiente"
        assert membresia.estado == "activa"

    pago = pagos_service.intentar_cobro(db_session, pago, exitoso=False)

    assert pago.estado == "fallido"
    db_session.refresh(membresia)
    assert membresia.estado == "congelada"

    congelacion = (
        db_session.query(CongelacionMembresia)
        .filter(CongelacionMembresia.membresia_id == membresia.id)
        .order_by(CongelacionMembresia.fecha_inicio.desc())
        .first()
    )
    assert congelacion.origen == "impago"


def test_intentar_cobro_sobre_pago_no_pendiente_lanza_error(db_session, sede_id):
    usuario, socio = _crear_socio_completo(db_session, sede_id)
    plan = _crear_plan(db_session)
    membresia = _crear_membresia(db_session, socio, plan, autor_id=usuario.id)

    pago = pagos_service.generar_cobro_pendiente(db_session, membresia, plan)
    pago = pagos_service.intentar_cobro(db_session, pago, exitoso=True)

    with pytest.raises(ValueError):
        pagos_service.intentar_cobro(db_session, pago, exitoso=True)


def test_hay_pagos_pendientes_bloquea_cancelacion_de_membresia(db_session, sede_id):
    usuario, socio = _crear_socio_completo(db_session, sede_id)
    plan = _crear_plan(db_session)
    membresia = _crear_membresia(db_session, socio, plan, autor_id=usuario.id)

    pagos_service.generar_cobro_pendiente(db_session, membresia, plan)

    assert membresias_service.hay_pagos_pendientes(db_session, membresia.id) is True
    with pytest.raises(ValueError):
        membresias_service.cancelar_membresia(db_session, membresia, plan, autor_id=usuario.id)


def test_procesar_cobros_automaticos_excluye_membresia_congelada(db_session, sede_id):
    usuario, socio = _crear_socio_completo(db_session, sede_id)
    plan = _crear_plan(db_session)
    membresia = _crear_membresia(db_session, socio, plan, autor_id=usuario.id)
    membresia.fecha_proxima_renovacion = date.today() + timedelta(days=1)
    membresias_service.congelar_membresia(db_session, membresia, origen="manual", autor_id=usuario.id)

    pagos = pagos_service.procesar_cobros_automaticos(db_session)
    ids = {p.membresia_id for p in pagos}
    assert membresia.id not in ids


def test_procesar_cobros_automaticos_genera_y_cobra_membresia_proxima_a_vencer(db_session, sede_id):
    usuario, socio = _crear_socio_completo(db_session, sede_id)
    plan = _crear_plan(db_session)
    membresia = _crear_membresia(db_session, socio, plan, autor_id=usuario.id)
    membresia.fecha_proxima_renovacion = date.today() + timedelta(days=1)
    db_session.commit()

    pagos = pagos_service.procesar_cobros_automaticos(db_session)
    assert len(pagos) == 1
    assert pagos[0].membresia_id == membresia.id
    assert pagos[0].estado == "exitoso"


def test_socio_ve_su_propio_historial_de_pagos(client, db_session, sede_id):
    usuario, socio = _crear_socio_completo(db_session, sede_id)
    plan = _crear_plan(db_session)
    membresia = _crear_membresia(db_session, socio, plan, autor_id=usuario.id)
    pago = pagos_service.generar_cobro_pendiente(db_session, membresia, plan)
    pagos_service.intentar_cobro(db_session, pago, exitoso=True)

    token = identidad_service.create_access_token(usuario)
    response = client.get(f"/pagos/{socio.id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_socio_no_ve_historial_de_pagos_ajeno(client, db_session, sede_id):
    usuario_a, socio_a = _crear_socio_completo(db_session, sede_id, "socio-a-pagos@test.com")
    usuario_b, socio_b = _crear_socio_completo(db_session, sede_id, "socio-b-pagos@test.com")

    token_b = identidad_service.create_access_token(usuario_b)
    response = client.get(f"/pagos/{socio_a.id}", headers={"Authorization": f"Bearer {token_b}"})
    assert response.status_code == 403


def test_historial_pagos_incluye_factura_id_vigente(client, db_session, sede_id):
    usuario, socio = _crear_socio_completo(db_session, sede_id)
    plan = _crear_plan(db_session)
    membresia = _crear_membresia(db_session, socio, plan, autor_id=usuario.id)
    pago = pagos_service.generar_cobro_pendiente(db_session, membresia, plan)
    pago = pagos_service.intentar_cobro(db_session, pago, exitoso=True)
    factura = db_session.query(Factura).filter(Factura.pago_id == pago.id).first()

    token = identidad_service.create_access_token(usuario)
    response = client.get(f"/pagos/{socio.id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()[0]["factura_id"] == str(factura.id)


def test_historial_pagos_factura_id_nulo_para_pago_sin_factura(client, db_session, sede_id):
    usuario, socio = _crear_socio_completo(db_session, sede_id)
    plan = _crear_plan(db_session)
    membresia = _crear_membresia(db_session, socio, plan, autor_id=usuario.id)
    pagos_service.generar_cobro_pendiente(db_session, membresia, plan)

    token = identidad_service.create_access_token(usuario)
    response = client.get(f"/pagos/{socio.id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()[0]["factura_id"] is None


def test_socio_descarga_su_propia_factura(client, db_session, sede_id):
    usuario, socio = _crear_socio_completo(db_session, sede_id)
    plan = _crear_plan(db_session)
    membresia = _crear_membresia(db_session, socio, plan, autor_id=usuario.id)
    pago = pagos_service.generar_cobro_pendiente(db_session, membresia, plan)
    pago = pagos_service.intentar_cobro(db_session, pago, exitoso=True)
    factura = db_session.query(Factura).filter(Factura.pago_id == pago.id).first()

    token = identidad_service.create_access_token(usuario)
    response = client.get(f"/facturas/{factura.id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


def test_socio_no_descarga_factura_ajena(client, db_session, sede_id):
    usuario_a, socio_a = _crear_socio_completo(db_session, sede_id, "socio-a2-pagos@test.com")
    usuario_b, socio_b = _crear_socio_completo(db_session, sede_id, "socio-b2-pagos@test.com")
    plan = _crear_plan(db_session)
    membresia = _crear_membresia(db_session, socio_a, plan, autor_id=usuario_a.id)
    pago = pagos_service.generar_cobro_pendiente(db_session, membresia, plan)
    pago = pagos_service.intentar_cobro(db_session, pago, exitoso=True)
    factura = db_session.query(Factura).filter(Factura.pago_id == pago.id).first()

    token_b = identidad_service.create_access_token(usuario_b)
    response = client.get(f"/facturas/{factura.id}", headers={"Authorization": f"Bearer {token_b}"})
    assert response.status_code == 403


def test_admin_genera_remesa_agrupando_pagos_exitosos_del_dia(client, db_session, sede_id):
    usuario, socio = _crear_socio_completo(db_session, sede_id)
    plan = _crear_plan(db_session)
    membresia = _crear_membresia(db_session, socio, plan, autor_id=usuario.id)
    pago = pagos_service.generar_cobro_pendiente(db_session, membresia, plan)
    pagos_service.intentar_cobro(db_session, pago, exitoso=True)

    token = _token_admin(db_session)
    response = client.post(
        "/remesas",
        headers={"Authorization": f"Bearer {token}"},
        json={"sede_id": str(sede_id), "fecha": str(date.today())},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["pagos_incluidos"] == 1
    assert float(body["total"]) == 29.99


def test_gestor_sede_no_puede_generar_remesa_de_otra_sede(client, db_session, sede_id):
    otra_sede = Sede(
        nombre="Otra sede pagos", direccion="Otra calle", ciudad="Valencia", telefono="600999888",
        horario_apertura=time(7, 0), horario_cierre=time(22, 0), aforo_maximo=50,
    )
    db_session.add(otra_sede)
    db_session.commit()
    db_session.refresh(otra_sede)

    token = _token_gestor(db_session, sede_id)
    response = client.post(
        "/remesas",
        headers={"Authorization": f"Bearer {token}"},
        json={"sede_id": str(otra_sede.id), "fecha": str(date.today())},
    )
    assert response.status_code == 403


def test_generar_remesa_audita_quien_la_genero(client, db_session, sede_id):
    usuario, socio = _crear_socio_completo(db_session, sede_id)
    plan = _crear_plan(db_session)
    membresia = _crear_membresia(db_session, socio, plan, autor_id=usuario.id)
    pago = pagos_service.generar_cobro_pendiente(db_session, membresia, plan)
    pagos_service.intentar_cobro(db_session, pago, exitoso=True)

    token = _token_admin(db_session)
    response = client.post(
        "/remesas",
        headers={"Authorization": f"Bearer {token}"},
        json={"sede_id": str(sede_id), "fecha": str(date.today())},
    )
    assert response.status_code == 201
    remesa_id = uuid.UUID(response.json()["id"])

    auditoria = (
        db_session.query(HistorialAccionPago)
        .filter(HistorialAccionPago.entidad_tipo == "remesa", HistorialAccionPago.entidad_id == remesa_id)
        .first()
    )
    assert auditoria is not None
    assert auditoria.accion == "generada"
    assert auditoria.autor_id is not None


def test_cobro_exitoso_audita_pago_y_factura(db_session, sede_id):
    usuario, socio = _crear_socio_completo(db_session, sede_id)
    plan = _crear_plan(db_session)
    membresia = _crear_membresia(db_session, socio, plan, autor_id=usuario.id)

    pago = pagos_service.generar_cobro_pendiente(db_session, membresia, plan)
    pago = pagos_service.intentar_cobro(db_session, pago, exitoso=True)
    factura = db_session.query(Factura).filter(Factura.pago_id == pago.id).first()

    acciones_pago = {
        h.accion for h in db_session.query(HistorialAccionPago).filter(
            HistorialAccionPago.entidad_tipo == "pago", HistorialAccionPago.entidad_id == pago.id
        )
    }
    assert {"generado", "cobro_exitoso"} <= acciones_pago

    accion_factura = (
        db_session.query(HistorialAccionPago)
        .filter(HistorialAccionPago.entidad_tipo == "factura", HistorialAccionPago.entidad_id == factura.id)
        .first()
    )
    assert accion_factura is not None
    assert accion_factura.accion == "emitida"


def test_anular_factura_y_reemitir(client, db_session, sede_id):
    usuario, socio = _crear_socio_completo(db_session, sede_id)
    plan = _crear_plan(db_session)
    membresia = _crear_membresia(db_session, socio, plan, autor_id=usuario.id)
    pago = pagos_service.generar_cobro_pendiente(db_session, membresia, plan)
    pago = pagos_service.intentar_cobro(db_session, pago, exitoso=True)
    factura = db_session.query(Factura).filter(Factura.pago_id == pago.id).first()

    token = _token_admin(db_session)
    response = client.post(
        f"/facturas/{factura.id}/anular",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["anulada"] is True

    response_doble = client.post(
        f"/facturas/{factura.id}/anular",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response_doble.status_code == 409

    response_reemitir = client.post(
        f"/facturas/{factura.id}/reemitir",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response_reemitir.status_code == 201
    nueva_factura = response_reemitir.json()
    assert nueva_factura["id"] != str(factura.id)
    assert nueva_factura["anulada"] is False
    assert nueva_factura["pago_id"] == str(pago.id)

    facturas_del_pago = db_session.query(Factura).filter(Factura.pago_id == pago.id).count()
    assert facturas_del_pago == 2


def test_reemitir_factura_no_anulada_es_rechazado(client, db_session, sede_id):
    usuario, socio = _crear_socio_completo(db_session, sede_id)
    plan = _crear_plan(db_session)
    membresia = _crear_membresia(db_session, socio, plan, autor_id=usuario.id)
    pago = pagos_service.generar_cobro_pendiente(db_session, membresia, plan)
    pago = pagos_service.intentar_cobro(db_session, pago, exitoso=True)
    factura = db_session.query(Factura).filter(Factura.pago_id == pago.id).first()

    token = _token_admin(db_session)
    response = client.post(
        f"/facturas/{factura.id}/reemitir",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 409


def test_gestor_sede_no_puede_anular_factura_de_otra_sede(client, db_session, sede_id):
    otra_sede = Sede(
        nombre="Otra sede pagos 3", direccion="Otra calle 3", ciudad="Sevilla", telefono="600999890",
        horario_apertura=time(7, 0), horario_cierre=time(22, 0), aforo_maximo=50,
    )
    db_session.add(otra_sede)
    db_session.commit()
    db_session.refresh(otra_sede)

    usuario, socio = _crear_socio_completo(db_session, otra_sede.id, "socio-otra-sede-pagos@test.com")
    plan = _crear_plan(db_session)
    membresia = _crear_membresia(db_session, socio, plan, autor_id=usuario.id)
    pago = pagos_service.generar_cobro_pendiente(db_session, membresia, plan)
    pago = pagos_service.intentar_cobro(db_session, pago, exitoso=True)
    factura = db_session.query(Factura).filter(Factura.pago_id == pago.id).first()

    token = _token_gestor(db_session, sede_id)
    response = client.post(
        f"/facturas/{factura.id}/anular",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_gestor_sede_lista_solo_remesas_de_su_sede(client, db_session, sede_id):
    otra_sede = Sede(
        nombre="Otra sede pagos 2", direccion="Otra calle 2", ciudad="Bilbao", telefono="600999889",
        horario_apertura=time(7, 0), horario_cierre=time(22, 0), aforo_maximo=50,
    )
    db_session.add(otra_sede)
    db_session.commit()
    db_session.refresh(otra_sede)

    pagos_service.generar_remesa(db_session, sede_id, date.today())
    pagos_service.generar_remesa(db_session, otra_sede.id, date.today())

    token = _token_gestor(db_session, sede_id)
    response = client.get("/remesas", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    ids_sede = {r["sede_id"] for r in response.json()}
    assert ids_sede == {str(sede_id)}
