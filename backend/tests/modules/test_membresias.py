import uuid
from datetime import date, timedelta

from app.modules.identidad import service as identidad_service
from app.modules.membresias import service as membresias_service
from app.modules.membresias.models import Membresia, PlanMembresia
from app.modules.socios.models import Socio


def _token_admin(db_session):
    admin = identidad_service.crear_usuario(db_session, "admin-membresias@test.com", "password123", "admin", None)
    return identidad_service.create_access_token(admin)


def _token_gestor(db_session, sede_id):
    gestor = identidad_service.crear_usuario(db_session, "gestor-membresias@test.com", "password123", "gestor_sede", sede_id)
    return identidad_service.create_access_token(gestor)


def _crear_socio_completo(db_session, sede_id, email="socio-membresias@test.com"):
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
        "nombre": "Plan Mensual",
        "precio": "29.99",
        "duracion": "mensual",
        "alcance": "toda_cadena",
        "sede_id": None,
        "preaviso_cancelacion_dias": 0,
        "activo": True,
    }
    datos.update(overrides)
    plan = PlanMembresia(**datos)
    db_session.add(plan)
    db_session.commit()
    db_session.refresh(plan)
    return plan


def _crear_membresia(db_session, socio, plan, autor_id, **overrides) -> Membresia:
    membresia = membresias_service.crear_membresia(
        db_session,
        socio_id=socio.id,
        plan=plan,
        fecha_inicio=overrides.get("fecha_inicio", date.today()),
        renovacion_automatica=overrides.get("renovacion_automatica", True),
        autor_id=autor_id,
    )
    return membresia


def test_admin_puede_crear_plan(client, db_session):
    token = _token_admin(db_session)
    response = client.post(
        "/planes-membresia",
        headers={"Authorization": f"Bearer {token}"},
        json={"nombre": "Plan Anual", "precio": "299.99", "duracion": "anual", "alcance": "toda_cadena"},
    )
    assert response.status_code == 201
    assert response.json()["activo"] is True


def test_plan_sede_unica_requiere_sede_id(client, db_session):
    token = _token_admin(db_session)
    response = client.post(
        "/planes-membresia",
        headers={"Authorization": f"Bearer {token}"},
        json={"nombre": "Plan Local", "precio": "19.99", "duracion": "mensual", "alcance": "sede_unica"},
    )
    assert response.status_code == 422


def test_listado_planes_publico_solo_muestra_activos(client, db_session):
    _crear_plan(db_session, nombre="Activo")
    _crear_plan(db_session, nombre="Inactivo", activo=False)

    response = client.get("/planes-membresia")
    assert response.status_code == 200
    nombres = [p["nombre"] for p in response.json()]
    assert "Activo" in nombres
    assert "Inactivo" not in nombres


def test_admin_puede_editar_plan(client, db_session):
    plan = _crear_plan(db_session)
    token = _token_admin(db_session)

    response = client.put(
        f"/planes-membresia/{plan.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"precio": "39.99"},
    )
    assert response.status_code == 200
    assert response.json()["precio"] == "39.99"


def test_admin_puede_dar_alta_membresia_con_renovacion_calculada(client, db_session, sede_id):
    _, socio = _crear_socio_completo(db_session, sede_id)
    plan = _crear_plan(db_session)
    token = _token_admin(db_session)

    response = client.post(
        "/membresias",
        headers={"Authorization": f"Bearer {token}"},
        json={"socio_id": str(socio.id), "plan_id": str(plan.id), "fecha_inicio": "2026-01-15"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["estado"] == "activa"
    assert body["fecha_proxima_renovacion"] == "2026-02-15"


def test_gestor_sede_no_puede_dar_alta_para_socio_de_otra_sede(client, db_session, sede_id):
    from datetime import time

    from app.modules.sedes.models import Sede

    otra_sede = Sede(
        nombre="Otra sede", direccion="Otra calle", ciudad="Valencia", telefono="600999888",
        horario_apertura=time(7, 0), horario_cierre=time(22, 0), aforo_maximo=50,
    )
    db_session.add(otra_sede)
    db_session.commit()
    db_session.refresh(otra_sede)

    _, socio = _crear_socio_completo(db_session, otra_sede.id)
    plan = _crear_plan(db_session)
    token = _token_gestor(db_session, sede_id)

    response = client.post(
        "/membresias",
        headers={"Authorization": f"Bearer {token}"},
        json={"socio_id": str(socio.id), "plan_id": str(plan.id)},
    )
    assert response.status_code == 403


def test_alta_con_plan_inactivo_devuelve_409(client, db_session, sede_id):
    _, socio = _crear_socio_completo(db_session, sede_id)
    plan = _crear_plan(db_session, activo=False)
    token = _token_admin(db_session)

    response = client.post(
        "/membresias",
        headers={"Authorization": f"Bearer {token}"},
        json={"socio_id": str(socio.id), "plan_id": str(plan.id)},
    )
    assert response.status_code == 409


def test_socio_puede_ver_su_propia_membresia(client, db_session, sede_id):
    usuario, socio = _crear_socio_completo(db_session, sede_id)
    plan = _crear_plan(db_session)
    membresia = _crear_membresia(db_session, socio, plan, autor_id=usuario.id)
    token = identidad_service.create_access_token(usuario)

    response = client.get(f"/membresias/{membresia.id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


def test_socio_no_puede_ver_membresia_ajena(client, db_session, sede_id):
    usuario_a, socio_a = _crear_socio_completo(db_session, sede_id, "socio-a-membresias@test.com")
    usuario_b, socio_b = _crear_socio_completo(db_session, sede_id, "socio-b-membresias@test.com")
    plan = _crear_plan(db_session)
    membresia_b = _crear_membresia(db_session, socio_b, plan, autor_id=usuario_b.id)
    token_a = identidad_service.create_access_token(usuario_a)

    response = client.get(f"/membresias/{membresia_b.id}", headers={"Authorization": f"Bearer {token_a}"})
    assert response.status_code == 403


def test_socio_lista_su_propia_membresia_via_query_autoscoped(client, db_session, sede_id):
    usuario, socio = _crear_socio_completo(db_session, sede_id)
    otro_usuario, otro_socio = _crear_socio_completo(db_session, sede_id, "socio-otra-membresias@test.com")
    plan = _crear_plan(db_session)
    membresia = _crear_membresia(db_session, socio, plan, autor_id=usuario.id)
    _crear_membresia(db_session, otro_socio, plan, autor_id=otro_usuario.id)
    token = identidad_service.create_access_token(usuario)

    response = client.get("/membresias", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    ids = {m["id"] for m in response.json()}
    assert ids == {str(membresia.id)}


def test_admin_puede_filtrar_membresias_por_socio_id(client, db_session, sede_id):
    usuario, socio = _crear_socio_completo(db_session, sede_id)
    plan = _crear_plan(db_session)
    membresia = _crear_membresia(db_session, socio, plan, autor_id=usuario.id)
    token = _token_admin(db_session)

    response = client.get(f"/membresias?socio_id={socio.id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    ids = {m["id"] for m in response.json()}
    assert ids == {str(membresia.id)}


def test_congelar_membresia_manual_cambia_estado(client, db_session, sede_id):
    usuario, socio = _crear_socio_completo(db_session, sede_id)
    plan = _crear_plan(db_session)
    membresia = _crear_membresia(db_session, socio, plan, autor_id=usuario.id)
    token = _token_admin(db_session)

    response = client.post(
        f"/membresias/{membresia.id}/congelar",
        headers={"Authorization": f"Bearer {token}"},
        json={"motivo": "Lesión"},
    )
    assert response.status_code == 200
    assert response.json()["estado"] == "congelada"


def test_no_se_puede_congelar_membresia_ya_congelada(client, db_session, sede_id):
    usuario, socio = _crear_socio_completo(db_session, sede_id)
    plan = _crear_plan(db_session)
    membresia = _crear_membresia(db_session, socio, plan, autor_id=usuario.id)
    membresias_service.congelar_membresia(db_session, membresia, origen="manual", autor_id=usuario.id)
    token = _token_admin(db_session)

    response = client.post(
        f"/membresias/{membresia.id}/congelar",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )
    assert response.status_code == 409


def test_reactivar_membresia_congelada(client, db_session, sede_id):
    usuario, socio = _crear_socio_completo(db_session, sede_id)
    plan = _crear_plan(db_session)
    membresia = _crear_membresia(db_session, socio, plan, autor_id=usuario.id)
    membresias_service.congelar_membresia(db_session, membresia, origen="manual", autor_id=usuario.id)
    token = _token_admin(db_session)

    response = client.post(f"/membresias/{membresia.id}/reactivar", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["estado"] == "activa"


def test_congelacion_por_impago_registra_autor_sistema_y_permite_reactivar(client, db_session, sede_id):
    usuario, socio = _crear_socio_completo(db_session, sede_id)
    plan = _crear_plan(db_session)
    membresia = _crear_membresia(db_session, socio, plan, autor_id=usuario.id)

    membresias_service.congelar_por_impago(db_session, membresia)
    assert membresia.estado == "congelada"

    usuario_sistema = membresias_service.obtener_o_crear_usuario_sistema(db_session)
    assert usuario_sistema.email == membresias_service.USUARIO_SISTEMA_EMAIL

    token_admin = _token_admin(db_session)
    response = client.post(f"/membresias/{membresia.id}/reactivar", headers={"Authorization": f"Bearer {token_admin}"})
    assert response.status_code == 200
    assert response.json()["estado"] == "activa"


def test_cancelar_membresia_establece_fecha_con_preaviso(client, db_session, sede_id):
    usuario, socio = _crear_socio_completo(db_session, sede_id)
    plan = _crear_plan(db_session, preaviso_cancelacion_dias=15)
    membresia = _crear_membresia(db_session, socio, plan, autor_id=usuario.id)
    token = _token_admin(db_session)

    response = client.post(
        f"/membresias/{membresia.id}/cancelar",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["estado"] == "cancelada"
    assert body["fecha_cancelacion"] == str(date.today() + timedelta(days=15))


def test_no_se_puede_cancelar_membresia_ya_cancelada(client, db_session, sede_id):
    usuario, socio = _crear_socio_completo(db_session, sede_id)
    plan = _crear_plan(db_session)
    membresia = _crear_membresia(db_session, socio, plan, autor_id=usuario.id)
    token = _token_admin(db_session)

    client.post(f"/membresias/{membresia.id}/cancelar", headers={"Authorization": f"Bearer {token}"}, json={})
    response = client.post(f"/membresias/{membresia.id}/cancelar", headers={"Authorization": f"Bearer {token}"}, json={})
    assert response.status_code == 409


def test_membresia_inexistente_devuelve_404(client, db_session):
    token = _token_admin(db_session)
    response = client.get(f"/membresias/{uuid.uuid4()}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404


def test_job_renovacion_detecta_proximas_a_vencer_y_omite_congeladas(db_session, sede_id):
    usuario, socio = _crear_socio_completo(db_session, sede_id)
    plan = _crear_plan(db_session)

    proxima = _crear_membresia(db_session, socio, plan, autor_id=usuario.id)
    proxima.fecha_proxima_renovacion = date.today() + timedelta(days=2)
    db_session.commit()

    _, socio_lejos = _crear_socio_completo(db_session, sede_id, "socio-lejos@test.com")
    lejana = _crear_membresia(db_session, socio_lejos, plan, autor_id=usuario.id)
    lejana.fecha_proxima_renovacion = date.today() + timedelta(days=30)
    db_session.commit()

    _, socio_congelado = _crear_socio_completo(db_session, sede_id, "socio-congelado@test.com")
    congelada = _crear_membresia(db_session, socio_congelado, plan, autor_id=usuario.id)
    congelada.fecha_proxima_renovacion = date.today() + timedelta(days=1)
    membresias_service.congelar_membresia(db_session, congelada, origen="manual", autor_id=usuario.id)

    resultado = membresias_service.ejecutar_job_renovacion(db_session)
    ids_resultado = {m.id for m in resultado}

    assert proxima.id in ids_resultado
    assert lejana.id not in ids_resultado
    assert congelada.id not in ids_resultado
