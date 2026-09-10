import uuid
from datetime import date, datetime, timedelta

from app.modules.clases.models import Clase, Reserva
from app.modules.entrenadores.models import Entrenador
from app.modules.identidad import service as identidad_service
from app.modules.membresias.models import Membresia, PlanMembresia
from app.modules.socios.models import Socio


def _token_admin(db_session):
    admin = identidad_service.crear_usuario(db_session, "admin-clases@test.com", "password123", "admin", None)
    return identidad_service.create_access_token(admin)


def _token_gestor(db_session, sede_id, email="gestor-clases@test.com"):
    gestor = identidad_service.crear_usuario(db_session, email, "password123", "gestor_sede", sede_id)
    return identidad_service.create_access_token(gestor)


def _crear_entrenador(db_session, sede_id, email="entrenador-clases@test.com", activo=True) -> tuple:
    usuario = identidad_service.crear_usuario(db_session, email, "password123", "entrenador", sede_id)
    entrenador = Entrenador(usuario_id=usuario.id, sede_id=sede_id, activo=activo)
    db_session.add(entrenador)
    db_session.commit()
    db_session.refresh(entrenador)
    return usuario, entrenador


def _crear_socio_con_membresia(db_session, sede_id, email="socio-clases@test.com", membresia_activa=True):
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

    if membresia_activa:
        plan = PlanMembresia(
            nombre="Plan Test", precio="29.99", duracion="mensual", alcance="toda_cadena",
            sede_id=None, preaviso_cancelacion_dias=0, activo=True,
        )
        db_session.add(plan)
        db_session.commit()
        db_session.refresh(plan)

        membresia = Membresia(
            socio_id=socio.id, plan_id=plan.id, fecha_inicio=date.today(),
            fecha_proxima_renovacion=date.today() + timedelta(days=30),
            renovacion_automatica=True, estado="activa",
        )
        db_session.add(membresia)
        db_session.commit()

    return usuario, socio


def _crear_clase(db_session, sede_id, entrenador_id, **overrides) -> Clase:
    datos = {
        "sede_id": sede_id,
        "entrenador_id": entrenador_id,
        "nombre": "Yoga",
        "tipo": "yoga",
        "fecha_hora": datetime.utcnow() + timedelta(days=1),
        "duracion_minutos": 60,
        "aforo_maximo": 1,
        "recurrente": False,
        "regla_recurrencia": None,
        "estado": "activa",
    }
    datos.update(overrides)
    clase = Clase(**datos)
    db_session.add(clase)
    db_session.commit()
    db_session.refresh(clase)
    return clase


def test_gestor_sede_crea_clase_con_entrenador_activo(client, db_session, sede_id):
    _, entrenador = _crear_entrenador(db_session, sede_id)
    token = _token_gestor(db_session, sede_id)

    response = client.post(
        "/clases",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "sede_id": str(sede_id),
            "entrenador_id": str(entrenador.id),
            "nombre": "Spinning",
            "tipo": "spinning",
            "fecha_hora": "2026-09-01T09:00:00",
            "duracion_minutos": 45,
            "aforo_maximo": 20,
        },
    )
    assert response.status_code == 201
    assert response.json()["plazas_disponibles"] == 20


def test_crear_clase_con_entrenador_inactivo_devuelve_422(client, db_session, sede_id):
    _, entrenador = _crear_entrenador(db_session, sede_id, activo=False)
    token = _token_gestor(db_session, sede_id)

    response = client.post(
        "/clases",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "sede_id": str(sede_id),
            "entrenador_id": str(entrenador.id),
            "nombre": "Spinning",
            "tipo": "spinning",
            "fecha_hora": "2026-09-01T09:00:00",
            "duracion_minutos": 45,
            "aforo_maximo": 20,
        },
    )
    assert response.status_code == 422


def test_gestor_sede_no_puede_crear_clase_en_otra_sede(client, db_session, sede_id):
    from datetime import time as time_

    from app.modules.sedes.models import Sede

    otra_sede = Sede(
        nombre="Otra sede", direccion="Otra calle", ciudad="Valencia", telefono="600999888",
        horario_apertura=time_(7, 0), horario_cierre=time_(22, 0), aforo_maximo=50,
    )
    db_session.add(otra_sede)
    db_session.commit()
    db_session.refresh(otra_sede)

    _, entrenador = _crear_entrenador(db_session, otra_sede.id)
    token = _token_gestor(db_session, sede_id)

    response = client.post(
        "/clases",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "sede_id": str(otra_sede.id),
            "entrenador_id": str(entrenador.id),
            "nombre": "Spinning",
            "tipo": "spinning",
            "fecha_hora": "2026-09-01T09:00:00",
            "duracion_minutos": 45,
            "aforo_maximo": 20,
        },
    )
    assert response.status_code == 403


def test_socio_con_membresia_activa_reserva_plaza(client, db_session, sede_id):
    _, entrenador = _crear_entrenador(db_session, sede_id)
    clase = _crear_clase(db_session, sede_id, entrenador.id, aforo_maximo=5)
    usuario_socio, _ = _crear_socio_con_membresia(db_session, sede_id)
    token = identidad_service.create_access_token(usuario_socio)

    response = client.post(f"/clases/{clase.id}/reservar", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201
    assert response.json()["estado"] == "confirmada"


def test_socio_sin_membresia_activa_no_puede_reservar(client, db_session, sede_id):
    _, entrenador = _crear_entrenador(db_session, sede_id)
    clase = _crear_clase(db_session, sede_id, entrenador.id, aforo_maximo=5)
    usuario_socio, _ = _crear_socio_con_membresia(db_session, sede_id, membresia_activa=False)
    token = identidad_service.create_access_token(usuario_socio)

    response = client.post(f"/clases/{clase.id}/reservar", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_reserva_sobre_aforo_va_a_lista_espera(client, db_session, sede_id):
    _, entrenador = _crear_entrenador(db_session, sede_id)
    clase = _crear_clase(db_session, sede_id, entrenador.id, aforo_maximo=1)

    usuario_a, _ = _crear_socio_con_membresia(db_session, sede_id, "socio-a-clases@test.com")
    usuario_b, _ = _crear_socio_con_membresia(db_session, sede_id, "socio-b-clases@test.com")

    token_a = identidad_service.create_access_token(usuario_a)
    token_b = identidad_service.create_access_token(usuario_b)

    resp_a = client.post(f"/clases/{clase.id}/reservar", headers={"Authorization": f"Bearer {token_a}"})
    resp_b = client.post(f"/clases/{clase.id}/reservar", headers={"Authorization": f"Bearer {token_b}"})

    assert resp_a.json()["estado"] == "confirmada"
    assert resp_b.json()["estado"] == "lista_espera"


def test_reserva_duplicada_devuelve_409(client, db_session, sede_id):
    _, entrenador = _crear_entrenador(db_session, sede_id)
    clase = _crear_clase(db_session, sede_id, entrenador.id, aforo_maximo=5)
    usuario_socio, _ = _crear_socio_con_membresia(db_session, sede_id)
    token = identidad_service.create_access_token(usuario_socio)

    client.post(f"/clases/{clase.id}/reservar", headers={"Authorization": f"Bearer {token}"})
    response = client.post(f"/clases/{clase.id}/reservar", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 409


def test_socio_lista_solo_sus_propias_reservas_activas(client, db_session, sede_id):
    _, entrenador = _crear_entrenador(db_session, sede_id)
    clase = _crear_clase(db_session, sede_id, entrenador.id, aforo_maximo=5)

    usuario_a, _ = _crear_socio_con_membresia(db_session, sede_id, "socio-a3-clases@test.com")
    usuario_b, _ = _crear_socio_con_membresia(db_session, sede_id, "socio-b3-clases@test.com")
    token_a = identidad_service.create_access_token(usuario_a)
    token_b = identidad_service.create_access_token(usuario_b)

    reserva_a = client.post(f"/clases/{clase.id}/reservar", headers={"Authorization": f"Bearer {token_a}"}).json()
    client.post(f"/clases/{clase.id}/reservar", headers={"Authorization": f"Bearer {token_b}"})

    response = client.get("/reservas", headers={"Authorization": f"Bearer {token_a}"})
    assert response.status_code == 200
    ids = {r["id"] for r in response.json()}
    assert ids == {reserva_a["id"]}


def test_reservas_no_incluye_canceladas(client, db_session, sede_id):
    _, entrenador = _crear_entrenador(db_session, sede_id)
    clase = _crear_clase(db_session, sede_id, entrenador.id, aforo_maximo=5)
    usuario_socio, _ = _crear_socio_con_membresia(db_session, sede_id)
    token = identidad_service.create_access_token(usuario_socio)

    reserva = client.post(f"/clases/{clase.id}/reservar", headers={"Authorization": f"Bearer {token}"}).json()
    client.delete(f"/reservas/{reserva['id']}", headers={"Authorization": f"Bearer {token}"})

    response = client.get("/reservas", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == []


def test_cancelar_reserva_confirmada_promociona_lista_espera(client, db_session, sede_id):
    _, entrenador = _crear_entrenador(db_session, sede_id)
    clase = _crear_clase(db_session, sede_id, entrenador.id, aforo_maximo=1)

    usuario_a, _ = _crear_socio_con_membresia(db_session, sede_id, "socio-a2-clases@test.com")
    usuario_b, _ = _crear_socio_con_membresia(db_session, sede_id, "socio-b2-clases@test.com")
    token_a = identidad_service.create_access_token(usuario_a)
    token_b = identidad_service.create_access_token(usuario_b)

    reserva_a = client.post(f"/clases/{clase.id}/reservar", headers={"Authorization": f"Bearer {token_a}"}).json()
    reserva_b = client.post(f"/clases/{clase.id}/reservar", headers={"Authorization": f"Bearer {token_b}"}).json()
    assert reserva_b["estado"] == "lista_espera"

    response = client.delete(f"/reservas/{reserva_a['id']}", headers={"Authorization": f"Bearer {token_a}"})
    assert response.status_code == 204

    db_session.refresh(db_session.get(Reserva, uuid.UUID(reserva_b["id"])))
    reserva_b_actualizada = db_session.get(Reserva, uuid.UUID(reserva_b["id"]))
    assert reserva_b_actualizada.estado == "confirmada"


def test_cancelar_fuera_de_plazo_queda_registrado(client, db_session, sede_id):
    # 90 min: dentro de la ventana de "fuera de plazo" (120 min) pero fuera
    # del límite de bloqueo de cancelación de reserva confirmada (60 min),
    # para poder seguir probando el flag sin chocar con esa restricción.
    _, entrenador = _crear_entrenador(db_session, sede_id)
    clase = _crear_clase(db_session, sede_id, entrenador.id, fecha_hora=datetime.utcnow() + timedelta(minutes=90))
    usuario_socio, _ = _crear_socio_con_membresia(db_session, sede_id)
    token = identidad_service.create_access_token(usuario_socio)

    reserva = client.post(f"/clases/{clase.id}/reservar", headers={"Authorization": f"Bearer {token}"}).json()
    client.delete(f"/reservas/{reserva['id']}", headers={"Authorization": f"Bearer {token}"})

    reserva_actualizada = db_session.get(Reserva, uuid.UUID(reserva["id"]))
    assert reserva_actualizada.cancelada_fuera_plazo is True


def test_no_se_puede_cancelar_reserva_confirmada_con_menos_de_1h(client, db_session, sede_id):
    _, entrenador = _crear_entrenador(db_session, sede_id)
    clase = _crear_clase(db_session, sede_id, entrenador.id, fecha_hora=datetime.utcnow() + timedelta(minutes=30))
    usuario_socio, _ = _crear_socio_con_membresia(db_session, sede_id)
    token = identidad_service.create_access_token(usuario_socio)

    reserva = client.post(f"/clases/{clase.id}/reservar", headers={"Authorization": f"Bearer {token}"}).json()
    assert reserva["estado"] == "confirmada"

    response = client.delete(f"/reservas/{reserva['id']}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 409

    reserva_actualizada = db_session.get(Reserva, uuid.UUID(reserva["id"]))
    assert reserva_actualizada.estado == "confirmada"


def test_se_puede_cancelar_reserva_confirmada_con_mas_de_1h(client, db_session, sede_id):
    _, entrenador = _crear_entrenador(db_session, sede_id)
    clase = _crear_clase(db_session, sede_id, entrenador.id, fecha_hora=datetime.utcnow() + timedelta(hours=2))
    usuario_socio, _ = _crear_socio_con_membresia(db_session, sede_id)
    token = identidad_service.create_access_token(usuario_socio)

    reserva = client.post(f"/clases/{clase.id}/reservar", headers={"Authorization": f"Bearer {token}"}).json()
    assert reserva["estado"] == "confirmada"

    response = client.delete(f"/reservas/{reserva['id']}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 204

    reserva_actualizada = db_session.get(Reserva, uuid.UUID(reserva["id"]))
    assert reserva_actualizada.estado == "cancelada"


def test_salir_de_lista_de_espera_permitido_con_menos_de_1h(client, db_session, sede_id):
    _, entrenador = _crear_entrenador(db_session, sede_id)
    clase = _crear_clase(
        db_session, sede_id, entrenador.id, aforo_maximo=1, fecha_hora=datetime.utcnow() + timedelta(minutes=30)
    )
    usuario_a, _ = _crear_socio_con_membresia(db_session, sede_id, "socio-a4-clases@test.com")
    usuario_b, _ = _crear_socio_con_membresia(db_session, sede_id, "socio-b4-clases@test.com")
    token_a = identidad_service.create_access_token(usuario_a)
    token_b = identidad_service.create_access_token(usuario_b)

    client.post(f"/clases/{clase.id}/reservar", headers={"Authorization": f"Bearer {token_a}"})
    reserva_b = client.post(f"/clases/{clase.id}/reservar", headers={"Authorization": f"Bearer {token_b}"}).json()
    assert reserva_b["estado"] == "lista_espera"

    response = client.delete(f"/reservas/{reserva_b['id']}", headers={"Authorization": f"Bearer {token_b}"})
    assert response.status_code == 204

    reserva_actualizada = db_session.get(Reserva, uuid.UUID(reserva_b["id"]))
    assert reserva_actualizada.estado == "cancelada"


def test_entrenador_ve_ocupacion_solo_de_sus_clases(client, db_session, sede_id):
    usuario_e1, entrenador1 = _crear_entrenador(db_session, sede_id, "entrenador1@test.com")
    _, entrenador2 = _crear_entrenador(db_session, sede_id, "entrenador2@test.com")
    clase_propia = _crear_clase(db_session, sede_id, entrenador1.id)
    clase_ajena = _crear_clase(db_session, sede_id, entrenador2.id)
    token_e1 = identidad_service.create_access_token(usuario_e1)

    ok = client.get(f"/clases/{clase_propia.id}/ocupacion", headers={"Authorization": f"Bearer {token_e1}"})
    assert ok.status_code == 200

    forbidden = client.get(f"/clases/{clase_ajena.id}/ocupacion", headers={"Authorization": f"Bearer {token_e1}"})
    assert forbidden.status_code == 403


def test_listar_clases_filtra_por_sede(client, db_session, sede_id):
    from datetime import time as time_

    from app.modules.sedes.models import Sede

    otra_sede = Sede(
        nombre="Otra sede 2", direccion="Otra calle 2", ciudad="Bilbao", telefono="600999889",
        horario_apertura=time_(7, 0), horario_cierre=time_(22, 0), aforo_maximo=50,
    )
    db_session.add(otra_sede)
    db_session.commit()
    db_session.refresh(otra_sede)

    _, entrenador1 = _crear_entrenador(db_session, sede_id)
    _, entrenador2 = _crear_entrenador(db_session, otra_sede.id, "entrenador-otra@test.com")
    _crear_clase(db_session, sede_id, entrenador1.id)
    _crear_clase(db_session, otra_sede.id, entrenador2.id)

    token = _token_admin(db_session)
    response = client.get(f"/clases?sede_id={sede_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert all(c["sede_id"] == str(sede_id) for c in response.json())


def test_entrenador_lista_solo_sus_propias_clases(client, db_session, sede_id):
    usuario_e1, entrenador1 = _crear_entrenador(db_session, sede_id, "entrenador-lista1@test.com")
    _, entrenador2 = _crear_entrenador(db_session, sede_id, "entrenador-lista2@test.com")
    clase_propia = _crear_clase(db_session, sede_id, entrenador1.id)
    _crear_clase(db_session, sede_id, entrenador2.id)
    token_e1 = identidad_service.create_access_token(usuario_e1)

    response = client.get("/clases", headers={"Authorization": f"Bearer {token_e1}"})
    assert response.status_code == 200
    ids = [c["id"] for c in response.json()]
    assert ids == [str(clase_propia.id)]


def test_entrenador_obtiene_detalle_solo_de_sus_propias_clases(client, db_session, sede_id):
    usuario_e1, entrenador1 = _crear_entrenador(db_session, sede_id, "entrenador-det1@test.com")
    _, entrenador2 = _crear_entrenador(db_session, sede_id, "entrenador-det2@test.com")
    clase_propia = _crear_clase(db_session, sede_id, entrenador1.id)
    clase_ajena = _crear_clase(db_session, sede_id, entrenador2.id)
    token_e1 = identidad_service.create_access_token(usuario_e1)

    ok = client.get(f"/clases/{clase_propia.id}", headers={"Authorization": f"Bearer {token_e1}"})
    assert ok.status_code == 200

    forbidden = client.get(f"/clases/{clase_ajena.id}", headers={"Authorization": f"Bearer {token_e1}"})
    assert forbidden.status_code == 403


def test_reasignar_por_baja_entrenador_reasigna_clases_futuras(client, db_session, sede_id):
    _, entrenador_baja = _crear_entrenador(db_session, sede_id, "entrenador-baja@test.com")
    _, nuevo_entrenador = _crear_entrenador(db_session, sede_id, "entrenador-nuevo@test.com")
    clase_futura = _crear_clase(db_session, sede_id, entrenador_baja.id, fecha_hora=datetime.utcnow() + timedelta(days=1))
    clase_pasada = _crear_clase(db_session, sede_id, entrenador_baja.id, fecha_hora=datetime.utcnow() - timedelta(days=1))

    token = _token_admin(db_session)
    response = client.post(
        "/clases/reasignar-por-baja-entrenador",
        headers={"Authorization": f"Bearer {token}"},
        json={"entrenador_id": str(entrenador_baja.id), "decision": "reasignar", "nuevo_entrenador_id": str(nuevo_entrenador.id)},
    )
    assert response.status_code == 200
    ids_afectadas = {c["id"] for c in response.json()}
    assert str(clase_futura.id) in ids_afectadas
    assert str(clase_pasada.id) not in ids_afectadas

    db_session.refresh(clase_futura)
    assert clase_futura.entrenador_id == nuevo_entrenador.id


def test_reasignar_por_baja_entrenador_cancela_clases_futuras(client, db_session, sede_id):
    _, entrenador_baja = _crear_entrenador(db_session, sede_id, "entrenador-baja2@test.com")
    clase_futura = _crear_clase(db_session, sede_id, entrenador_baja.id, fecha_hora=datetime.utcnow() + timedelta(days=1))

    token = _token_admin(db_session)
    response = client.post(
        "/clases/reasignar-por-baja-entrenador",
        headers={"Authorization": f"Bearer {token}"},
        json={"entrenador_id": str(entrenador_baja.id), "decision": "cancelar"},
    )
    assert response.status_code == 200

    db_session.refresh(clase_futura)
    assert clase_futura.estado == "cancelada"


def test_gestor_sede_no_puede_reasignar_entrenador_de_otra_sede(client, db_session, sede_id):
    from datetime import time as time_

    from app.modules.sedes.models import Sede

    otra_sede = Sede(
        nombre="Otra sede", direccion="Otra calle", ciudad="Valencia", telefono="600999888",
        horario_apertura=time_(7, 0), horario_cierre=time_(22, 0), aforo_maximo=50,
    )
    db_session.add(otra_sede)
    db_session.commit()
    db_session.refresh(otra_sede)

    _, entrenador_baja = _crear_entrenador(db_session, otra_sede.id, "entrenador-baja-otra@test.com")
    _, nuevo_entrenador = _crear_entrenador(db_session, otra_sede.id, "entrenador-nuevo-otra@test.com")

    token = _token_gestor(db_session, sede_id)
    response = client.post(
        "/clases/reasignar-por-baja-entrenador",
        headers={"Authorization": f"Bearer {token}"},
        json={"entrenador_id": str(entrenador_baja.id), "decision": "reasignar", "nuevo_entrenador_id": str(nuevo_entrenador.id)},
    )
    assert response.status_code == 403


def test_reasignar_a_entrenador_de_otra_sede_es_rechazado(client, db_session, sede_id):
    from datetime import time as time_

    from app.modules.sedes.models import Sede

    otra_sede = Sede(
        nombre="Otra sede", direccion="Otra calle", ciudad="Valencia", telefono="600999888",
        horario_apertura=time_(7, 0), horario_cierre=time_(22, 0), aforo_maximo=50,
    )
    db_session.add(otra_sede)
    db_session.commit()
    db_session.refresh(otra_sede)

    _, entrenador_baja = _crear_entrenador(db_session, sede_id, "entrenador-baja3@test.com")
    _, entrenador_otra_sede = _crear_entrenador(db_session, otra_sede.id, "entrenador-otra-sede@test.com")

    token = _token_admin(db_session)
    response = client.post(
        "/clases/reasignar-por-baja-entrenador",
        headers={"Authorization": f"Bearer {token}"},
        json={"entrenador_id": str(entrenador_baja.id), "decision": "reasignar", "nuevo_entrenador_id": str(entrenador_otra_sede.id)},
    )
    assert response.status_code == 422


def test_clase_inexistente_devuelve_404(client, db_session):
    token = _token_admin(db_session)
    response = client.get(f"/clases/{uuid.uuid4()}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404


def test_socio_solo_ve_clases_de_su_propia_sede(client, db_session, sede_id):
    from datetime import time as time_

    from app.modules.sedes.models import Sede

    otra_sede = Sede(
        nombre="Otra sede 3", direccion="Otra calle 3", ciudad="Sevilla", telefono="600999890",
        horario_apertura=time_(7, 0), horario_cierre=time_(22, 0), aforo_maximo=50,
    )
    db_session.add(otra_sede)
    db_session.commit()
    db_session.refresh(otra_sede)

    _, entrenador_propia = _crear_entrenador(db_session, sede_id)
    _, entrenador_otra = _crear_entrenador(db_session, otra_sede.id, "entrenador-otra-socio@test.com")
    clase_propia = _crear_clase(db_session, sede_id, entrenador_propia.id)
    _crear_clase(db_session, otra_sede.id, entrenador_otra.id)

    usuario_socio, _ = _crear_socio_con_membresia(db_session, sede_id, "socio-scoping@test.com")
    token = identidad_service.create_access_token(usuario_socio)

    response = client.get("/clases", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    ids = [c["id"] for c in response.json()]
    assert ids == [str(clase_propia.id)]

    # Incluso pidiendo explícitamente la sede_id ajena, no debe verla.
    response_forzado = client.get(
        f"/clases?sede_id={otra_sede.id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert response_forzado.status_code == 200
    assert response_forzado.json() == []


def test_socio_no_puede_ver_detalle_de_clase_de_otra_sede(client, db_session, sede_id):
    from datetime import time as time_

    from app.modules.sedes.models import Sede

    otra_sede = Sede(
        nombre="Otra sede 4", direccion="Otra calle 4", ciudad="Malaga", telefono="600999891",
        horario_apertura=time_(7, 0), horario_cierre=time_(22, 0), aforo_maximo=50,
    )
    db_session.add(otra_sede)
    db_session.commit()
    db_session.refresh(otra_sede)

    _, entrenador_otra = _crear_entrenador(db_session, otra_sede.id, "entrenador-otra-det@test.com")
    clase_ajena = _crear_clase(db_session, otra_sede.id, entrenador_otra.id)

    usuario_socio, _ = _crear_socio_con_membresia(db_session, sede_id, "socio-detalle@test.com")
    token = identidad_service.create_access_token(usuario_socio)

    response = client.get(f"/clases/{clase_ajena.id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_socio_no_puede_reservar_clase_de_otra_sede(client, db_session, sede_id):
    from datetime import time as time_

    from app.modules.sedes.models import Sede

    otra_sede = Sede(
        nombre="Otra sede 5", direccion="Otra calle 5", ciudad="Zaragoza", telefono="600999892",
        horario_apertura=time_(7, 0), horario_cierre=time_(22, 0), aforo_maximo=50,
    )
    db_session.add(otra_sede)
    db_session.commit()
    db_session.refresh(otra_sede)

    _, entrenador_otra = _crear_entrenador(db_session, otra_sede.id, "entrenador-otra-res@test.com")
    clase_ajena = _crear_clase(db_session, otra_sede.id, entrenador_otra.id, aforo_maximo=5)

    usuario_socio, _ = _crear_socio_con_membresia(db_session, sede_id, "socio-reserva-otra@test.com")
    token = identidad_service.create_access_token(usuario_socio)

    # El intento se rechaza aunque el socio conozca el clase_id de memoria
    # (p.ej. copiándolo de otra pestaña) y la clase no aparezca en su listado.
    response = client.post(f"/clases/{clase_ajena.id}/reservar", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_socio_ve_clase_pasada_de_la_semana_actual_con_reserva(client, db_session, sede_id):
    _, entrenador = _crear_entrenador(db_session, sede_id)
    ahora = datetime.utcnow()
    clase = _crear_clase(db_session, sede_id, entrenador.id, fecha_hora=ahora - timedelta(minutes=30))

    usuario_socio, socio = _crear_socio_con_membresia(db_session, sede_id, "socio-semana-actual@test.com")
    db_session.add(Reserva(clase_id=clase.id, socio_id=socio.id, estado="confirmada"))
    db_session.commit()

    token = identidad_service.create_access_token(usuario_socio)
    response = client.get("/clases", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert str(clase.id) in {c["id"] for c in response.json()}


def test_socio_no_ve_clase_de_semana_anterior_aunque_tenga_reserva(client, db_session, sede_id):
    _, entrenador = _crear_entrenador(db_session, sede_id)
    ahora = datetime.utcnow()
    inicio_semana_actual = datetime.combine(ahora.date() - timedelta(days=ahora.weekday()), datetime.min.time())
    clase = _crear_clase(db_session, sede_id, entrenador.id, fecha_hora=inicio_semana_actual - timedelta(days=1))

    usuario_socio, socio = _crear_socio_con_membresia(db_session, sede_id, "socio-semana-anterior@test.com")
    db_session.add(Reserva(clase_id=clase.id, socio_id=socio.id, estado="confirmada"))
    db_session.commit()

    token = identidad_service.create_access_token(usuario_socio)
    response = client.get("/clases", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert str(clase.id) not in {c["id"] for c in response.json()}


def test_admin_y_gestor_sede_siguen_viendo_historico_completo(client, db_session, sede_id):
    _, entrenador = _crear_entrenador(db_session, sede_id)
    ahora = datetime.utcnow()
    inicio_semana_actual = datetime.combine(ahora.date() - timedelta(days=ahora.weekday()), datetime.min.time())
    clase_antigua = _crear_clase(db_session, sede_id, entrenador.id, fecha_hora=inicio_semana_actual - timedelta(days=10))

    token_admin = _token_admin(db_session)
    response_admin = client.get("/clases", headers={"Authorization": f"Bearer {token_admin}"})
    assert response_admin.status_code == 200
    assert str(clase_antigua.id) in {c["id"] for c in response_admin.json()}

    token_gestor = _token_gestor(db_session, sede_id)
    response_gestor = client.get("/clases", headers={"Authorization": f"Bearer {token_gestor}"})
    assert response_gestor.status_code == 200
    assert str(clase_antigua.id) in {c["id"] for c in response_gestor.json()}
