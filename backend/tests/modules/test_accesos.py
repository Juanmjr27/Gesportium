from datetime import date, datetime, time, timedelta

from app.core.config import settings
from app.modules.clases.models import Asistencia, Clase, Reserva
from app.modules.entrenadores.models import Entrenador
from app.modules.identidad import service as identidad_service
from app.modules.membresias import service as membresias_service
from app.modules.membresias.models import PlanMembresia
from app.modules.socios.models import Socio
import pytest

# Todos los tests de este archivo son de integracion (usan client + db_session
# contra Postgres real). Un archivo de tests unitarios nuevo debe llevar en su
# lugar: pytestmark = pytest.mark.unit
pytestmark = pytest.mark.integration

TOTEM_HEADERS = {"X-Totem-Key": settings.totem_api_key}


def _token_admin(db_session):
    admin = identidad_service.crear_usuario(db_session, "admin-accesos@test.com", "password123", "admin", None)
    return identidad_service.create_access_token(admin)


def _token_gestor(db_session, sede_id, email="gestor-accesos@test.com"):
    gestor = identidad_service.crear_usuario(db_session, email, "password123", "gestor_sede", sede_id)
    return identidad_service.create_access_token(gestor)


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


def _crear_socio_con_membresia(db_session, sede_id, email="socio-accesos@test.com", membresia_activa=True):
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
        plan = _crear_plan(db_session)
        membresia = membresias_service.crear_membresia(
            db_session, socio_id=socio.id, plan=plan, fecha_inicio=date.today(),
            renovacion_automatica=True, autor_id=usuario.id,
        )
        if membresia_activa == "congelada":
            membresias_service.congelar_membresia(db_session, membresia, origen="manual", autor_id=usuario.id)

    return usuario, socio


def _crear_entrenador(db_session, sede_id, email="entrenador-accesos@test.com"):
    usuario = identidad_service.crear_usuario(db_session, email, "password123", "entrenador", sede_id)
    entrenador = Entrenador(usuario_id=usuario.id, sede_id=sede_id, activo=True)
    db_session.add(entrenador)
    db_session.commit()
    db_session.refresh(entrenador)
    return entrenador


def test_checkin_con_membresia_activa_registra_entrada(client, db_session, sede_id):
    _, socio = _crear_socio_con_membresia(db_session, sede_id)

    response = client.post(
        "/accesos/checkin",
        headers=TOTEM_HEADERS,
        json={"socio_id": str(socio.id), "sede_id": str(sede_id)},
    )
    assert response.status_code == 201
    assert response.json()["tipo"] == "entrada"


def test_checkin_alterna_entrada_y_salida(client, db_session, sede_id):
    _, socio = _crear_socio_con_membresia(db_session, sede_id)
    body = {"socio_id": str(socio.id), "sede_id": str(sede_id)}

    primera = client.post("/accesos/checkin", headers=TOTEM_HEADERS, json=body)
    segunda = client.post("/accesos/checkin", headers=TOTEM_HEADERS, json=body)

    assert primera.json()["tipo"] == "entrada"
    assert segunda.json()["tipo"] == "salida"


def test_checkin_sin_membresia_activa_es_rechazado(client, db_session, sede_id):
    _, socio = _crear_socio_con_membresia(db_session, sede_id, membresia_activa=False)

    response = client.post(
        "/accesos/checkin",
        headers=TOTEM_HEADERS,
        json={"socio_id": str(socio.id), "sede_id": str(sede_id)},
    )
    assert response.status_code == 403


def test_checkin_con_membresia_congelada_es_rechazado(client, db_session, sede_id):
    _, socio = _crear_socio_con_membresia(db_session, sede_id, membresia_activa="congelada")

    response = client.post(
        "/accesos/checkin",
        headers=TOTEM_HEADERS,
        json={"socio_id": str(socio.id), "sede_id": str(sede_id)},
    )
    assert response.status_code == 403


def test_checkin_sin_clave_de_totem_es_rechazado(client, db_session, sede_id):
    _, socio = _crear_socio_con_membresia(db_session, sede_id)

    response = client.post(
        "/accesos/checkin",
        json={"socio_id": str(socio.id), "sede_id": str(sede_id)},
    )
    assert response.status_code == 401


def test_checkin_marca_asistencia_de_reserva_en_curso(client, db_session, sede_id):
    _, socio = _crear_socio_con_membresia(db_session, sede_id)
    entrenador = _crear_entrenador(db_session, sede_id)

    clase = Clase(
        sede_id=sede_id, entrenador_id=entrenador.id, nombre="Yoga", tipo="yoga",
        fecha_hora=datetime.utcnow() - timedelta(minutes=10), duracion_minutos=60,
        aforo_maximo=10, recurrente=False, regla_recurrencia=None, estado="activa",
    )
    db_session.add(clase)
    db_session.commit()
    db_session.refresh(clase)

    reserva = Reserva(clase_id=clase.id, socio_id=socio.id, estado="confirmada")
    db_session.add(reserva)
    db_session.commit()
    db_session.refresh(reserva)

    response = client.post(
        "/accesos/checkin",
        headers=TOTEM_HEADERS,
        json={"socio_id": str(socio.id), "sede_id": str(sede_id)},
    )
    assert response.status_code == 201

    asistencia = db_session.query(Asistencia).filter(Asistencia.reserva_id == reserva.id).first()
    assert asistencia is not None
    assert asistencia.fecha_checkin is not None


def test_admin_ve_aforo_actual_de_una_sede(client, db_session, sede_id):
    _, socio = _crear_socio_con_membresia(db_session, sede_id)
    client.post("/accesos/checkin", headers=TOTEM_HEADERS, json={"socio_id": str(socio.id), "sede_id": str(sede_id)})

    token = _token_admin(db_session)
    response = client.get(f"/sedes/{sede_id}/aforo-actual", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["ocupacion_actual"] == 1
    assert body["aforo_superado"] is False


def test_aforo_actual_no_cuenta_socios_que_ya_salieron(client, db_session, sede_id):
    _, socio = _crear_socio_con_membresia(db_session, sede_id)
    body = {"socio_id": str(socio.id), "sede_id": str(sede_id)}
    client.post("/accesos/checkin", headers=TOTEM_HEADERS, json=body)
    client.post("/accesos/checkin", headers=TOTEM_HEADERS, json=body)

    token = _token_admin(db_session)
    response = client.get(f"/sedes/{sede_id}/aforo-actual", headers={"Authorization": f"Bearer {token}"})
    assert response.json()["ocupacion_actual"] == 0


def test_gestor_sede_no_ve_aforo_de_otra_sede(client, db_session, sede_id):
    from app.modules.sedes.models import Sede

    otra_sede = Sede(
        nombre="Otra sede accesos", direccion="Otra calle", ciudad="Sevilla", telefono="600999888",
        horario_apertura=time(7, 0), horario_cierre=time(22, 0), aforo_maximo=50,
    )
    db_session.add(otra_sede)
    db_session.commit()
    db_session.refresh(otra_sede)

    token = _token_gestor(db_session, sede_id)
    response = client.get(f"/sedes/{otra_sede.id}/aforo-actual", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_socio_ve_su_propio_historial_de_accesos(client, db_session, sede_id):
    usuario, socio = _crear_socio_con_membresia(db_session, sede_id)
    client.post("/accesos/checkin", headers=TOTEM_HEADERS, json={"socio_id": str(socio.id), "sede_id": str(sede_id)})

    token = identidad_service.create_access_token(usuario)
    response = client.get(f"/accesos/{socio.id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_socio_no_ve_historial_de_accesos_ajeno(client, db_session, sede_id):
    _, socio_a = _crear_socio_con_membresia(db_session, sede_id, email="socio-a-accesos@test.com")
    usuario_b, _ = _crear_socio_con_membresia(db_session, sede_id, email="socio-b-accesos@test.com")

    token_b = identidad_service.create_access_token(usuario_b)
    response = client.get(f"/accesos/{socio_a.id}", headers={"Authorization": f"Bearer {token_b}"})
    assert response.status_code == 403
