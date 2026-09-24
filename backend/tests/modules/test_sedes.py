import uuid
from datetime import date, time

from app.modules.identidad import service as identidad_service
from app.modules.sedes.models import Sede
from app.modules.socios.models import Socio
import pytest

pytestmark = pytest.mark.integration


def _crear_sede(db_session, **overrides) -> Sede:
    datos = {
        "nombre": "Sede Centro",
        "direccion": "Calle Mayor 1",
        "ciudad": "Madrid",
        "telefono": "600000000",
        "horario_apertura": time(7, 0),
        "horario_cierre": time(22, 0),
        "aforo_maximo": 100,
        "activa": True,
    }
    datos.update(overrides)
    sede = Sede(**datos)
    db_session.add(sede)
    db_session.commit()
    db_session.refresh(sede)
    return sede


def _token_admin(db_session):
    admin = identidad_service.crear_usuario(db_session, "admin-sedes@test.com", "password123", "admin", None)
    return identidad_service.create_access_token(admin)


def _token_gestor(db_session, sede_id):
    gestor = identidad_service.crear_usuario(db_session, "gestor-sedes@test.com", "password123", "gestor_sede", sede_id)
    return identidad_service.create_access_token(gestor)


def test_listado_publico_solo_muestra_sedes_activas_y_datos_basicos(client, db_session):
    activa = _crear_sede(db_session, nombre="Activa")
    _crear_sede(db_session, nombre="Inactiva", activa=False)

    response = client.get("/sedes")
    assert response.status_code == 200
    body = response.json()

    nombres = [s["nombre"] for s in body]
    assert "Activa" in nombres
    assert "Inactiva" not in nombres

    sede_publica = next(s for s in body if s["id"] == str(activa.id))
    assert "telefono" not in sede_publica
    assert "aforo_maximo" not in sede_publica


def test_detalle_sede_requiere_token(client, db_session):
    sede = _crear_sede(db_session)
    response = client.get(f"/sedes/{sede.id}")
    assert response.status_code in (401, 403)


def test_admin_ve_detalle_de_cualquier_sede(client, db_session):
    sede = _crear_sede(db_session)
    token = _token_admin(db_session)

    response = client.get(f"/sedes/{sede.id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["telefono"] == sede.telefono


def test_gestor_sede_ve_su_propia_sede(client, db_session):
    sede = _crear_sede(db_session)
    token = _token_gestor(db_session, sede.id)

    response = client.get(f"/sedes/{sede.id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


def test_gestor_sede_no_puede_ver_otra_sede(client, db_session):
    sede = _crear_sede(db_session)
    otra_sede = _crear_sede(db_session, nombre="Otra")
    token = _token_gestor(db_session, sede.id)

    response = client.get(f"/sedes/{otra_sede.id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_sede_inexistente_devuelve_404(client, db_session):
    token = _token_admin(db_session)
    response = client.get(f"/sedes/{uuid.uuid4()}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404


def test_admin_puede_crear_sede(client, db_session):
    token = _token_admin(db_session)
    response = client.post(
        "/sedes",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "nombre": "Sede Nueva",
            "direccion": "Av. Siempre Viva 123",
            "ciudad": "Sevilla",
            "telefono": "611111111",
            "horario_apertura": "08:00:00",
            "horario_cierre": "21:00:00",
            "aforo_maximo": 50,
        },
    )
    assert response.status_code == 201
    assert response.json()["activa"] is True


def test_gestor_sede_no_puede_crear_sede(client, db_session):
    sede = _crear_sede(db_session)
    token = _token_gestor(db_session, sede.id)

    response = client.post(
        "/sedes",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "nombre": "Sede Nueva",
            "direccion": "Av. Siempre Viva 123",
            "ciudad": "Sevilla",
            "telefono": "611111111",
            "horario_apertura": "08:00:00",
            "horario_cierre": "21:00:00",
            "aforo_maximo": 50,
        },
    )
    assert response.status_code == 403


def test_admin_puede_editar_cualquier_sede(client, db_session):
    sede = _crear_sede(db_session)
    token = _token_admin(db_session)

    response = client.put(
        f"/sedes/{sede.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"ciudad": "Barcelona"},
    )
    assert response.status_code == 200
    assert response.json()["ciudad"] == "Barcelona"


def test_gestor_sede_no_puede_editar_otra_sede(client, db_session):
    sede = _crear_sede(db_session)
    otra_sede = _crear_sede(db_session, nombre="Otra")
    token = _token_gestor(db_session, sede.id)

    response = client.put(
        f"/sedes/{otra_sede.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"ciudad": "Barcelona"},
    )
    assert response.status_code == 403


def test_admin_puede_dar_de_baja_sede_sin_socios(client, db_session):
    sede = _crear_sede(db_session)
    token = _token_admin(db_session)

    response = client.delete(f"/sedes/{sede.id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 204

    db_session.refresh(sede)
    assert sede.activa is False


def test_no_se_puede_dar_de_baja_sede_con_socios_activos(client, db_session):
    sede = _crear_sede(db_session)
    usuario_socio = identidad_service.crear_usuario(db_session, "socio-sede@test.com", "password123", "socio", sede.id)
    db_session.add(
        Socio(
            usuario_id=usuario_socio.id,
            sede_id=sede.id,
            fecha_nacimiento=date(1990, 1, 1),
            telefono="600000001",
            direccion="Calle Falsa 1",
            contacto_emergencia_nombre="Contacto",
            contacto_emergencia_telefono="600000002",
        )
    )
    db_session.commit()
    token = _token_admin(db_session)

    response = client.delete(f"/sedes/{sede.id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 409


def test_gestor_sede_no_puede_dar_de_baja(client, db_session):
    sede = _crear_sede(db_session)
    token = _token_gestor(db_session, sede.id)

    response = client.delete(f"/sedes/{sede.id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
