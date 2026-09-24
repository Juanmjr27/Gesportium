import uuid
from datetime import date, datetime, time, timedelta

from app.modules.clases.models import Clase
from app.modules.entrenadores.models import Entrenador, SocioAsignado
from app.modules.identidad import service as identidad_service
from app.modules.identidad.models import Usuario
from app.modules.sedes.models import Sede
from app.modules.socios.models import Socio
import pytest

pytestmark = pytest.mark.integration


def _token_admin(db_session):
    admin = identidad_service.crear_usuario(db_session, "admin-entrenadores@test.com", "password123", "admin", None)
    return identidad_service.create_access_token(admin)


def _token_gestor(db_session, sede_id, email="gestor-entrenadores@test.com"):
    gestor = identidad_service.crear_usuario(db_session, email, "password123", "gestor_sede", sede_id)
    return identidad_service.create_access_token(gestor)


def _crear_usuario_entrenador(db_session, sede_id, email="usuario-entrenador@test.com"):
    return identidad_service.crear_usuario(db_session, email, "password123", "entrenador", sede_id)


def _crear_entrenador(db_session, sede_id, email="entrenador@test.com", activo=True) -> tuple:
    usuario = _crear_usuario_entrenador(db_session, sede_id, email)
    entrenador = Entrenador(usuario_id=usuario.id, sede_id=sede_id, especialidades=["yoga"], activo=activo)
    db_session.add(entrenador)
    db_session.commit()
    db_session.refresh(entrenador)
    return usuario, entrenador


def _crear_socio(db_session, sede_id, email="socio-entrenadores@test.com") -> Socio:
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
    return socio


def _crear_otra_sede(db_session, nombre="Otra sede") -> Sede:
    sede = Sede(
        nombre=nombre, direccion="Otra calle", ciudad="Valencia", telefono="600999888",
        horario_apertura=time(7, 0), horario_cierre=time(22, 0), aforo_maximo=50,
    )
    db_session.add(sede)
    db_session.commit()
    db_session.refresh(sede)
    return sede


def test_admin_crea_entrenador(client, db_session, sede_id):
    token = _token_admin(db_session)

    response = client.post(
        "/entrenadores",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "email": "nuevo-entrenador@test.com",
            "password": "password123",
            "sede_id": str(sede_id),
            "especialidades": ["crossfit"],
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["activo"] is True
    assert body["especialidades"] == ["crossfit"]

    usuario_creado = db_session.query(Usuario).filter(Usuario.email == "nuevo-entrenador@test.com").first()
    assert usuario_creado is not None
    assert usuario_creado.rol == "entrenador"
    assert str(usuario_creado.id) == body["usuario_id"]

    login = client.post("/auth/login", json={"email": "nuevo-entrenador@test.com", "password": "password123"})
    assert login.status_code == 200


def test_crear_entrenador_con_email_ya_registrado_devuelve_409(client, db_session, sede_id):
    _, _ = _crear_entrenador(db_session, sede_id, "entrenador-existente@test.com")
    token = _token_admin(db_session)

    response = client.post(
        "/entrenadores",
        headers={"Authorization": f"Bearer {token}"},
        json={"email": "entrenador-existente@test.com", "password": "password123", "sede_id": str(sede_id)},
    )
    assert response.status_code == 409
    assert "email" in response.json()["detail"].lower()


def test_gestor_sede_no_puede_crear_entrenador_en_otra_sede(client, db_session, sede_id):
    otra_sede = _crear_otra_sede(db_session)
    token = _token_gestor(db_session, sede_id)

    response = client.post(
        "/entrenadores",
        headers={"Authorization": f"Bearer {token}"},
        json={"email": "entrenador-otra@test.com", "password": "password123", "sede_id": str(otra_sede.id)},
    )
    assert response.status_code == 403


def test_gestor_sede_lista_solo_su_sede(client, db_session, sede_id):
    otra_sede = _crear_otra_sede(db_session, "Otra sede 2")
    _crear_entrenador(db_session, sede_id, "entrenador-propia@test.com")
    _crear_entrenador(db_session, otra_sede.id, "entrenador-ajena@test.com")
    token = _token_gestor(db_session, sede_id)

    response = client.get("/entrenadores", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    ids_sede = {e["sede_id"] for e in response.json()}
    assert ids_sede == {str(sede_id)}


def test_entrenador_ve_su_propio_detalle_no_el_ajeno(client, db_session, sede_id):
    usuario1, entrenador1 = _crear_entrenador(db_session, sede_id, "entrenador1@test.com")
    _, entrenador2 = _crear_entrenador(db_session, sede_id, "entrenador2@test.com")
    token1 = identidad_service.create_access_token(usuario1)

    propio = client.get(f"/entrenadores/{entrenador1.id}", headers={"Authorization": f"Bearer {token1}"})
    assert propio.status_code == 200

    ajeno = client.get(f"/entrenadores/{entrenador2.id}", headers={"Authorization": f"Bearer {token1}"})
    assert ajeno.status_code == 403


def test_admin_edita_especialidades(client, db_session, sede_id):
    _, entrenador = _crear_entrenador(db_session, sede_id)
    token = _token_admin(db_session)

    response = client.put(
        f"/entrenadores/{entrenador.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"especialidades": ["nutricion", "yoga"]},
    )
    assert response.status_code == 200
    assert response.json()["especialidades"] == ["nutricion", "yoga"]


def test_gestor_sede_asigna_socio(client, db_session, sede_id):
    _, entrenador = _crear_entrenador(db_session, sede_id)
    socio = _crear_socio(db_session, sede_id)
    token = _token_gestor(db_session, sede_id)

    response = client.post(
        f"/entrenadores/{entrenador.id}/socios",
        headers={"Authorization": f"Bearer {token}"},
        json={"socio_id": str(socio.id)},
    )
    assert response.status_code == 201
    assert response.json()["fecha_fin"] is None


def test_admin_asigna_y_desasigna_socio(client, db_session, sede_id):
    _, entrenador = _crear_entrenador(db_session, sede_id)
    socio = _crear_socio(db_session, sede_id)
    token = _token_admin(db_session)

    asignar = client.post(
        f"/entrenadores/{entrenador.id}/socios",
        headers={"Authorization": f"Bearer {token}"},
        json={"socio_id": str(socio.id)},
    )
    assert asignar.status_code == 201

    desasignar = client.delete(f"/entrenadores/{entrenador.id}/socios/{socio.id}", headers={"Authorization": f"Bearer {token}"})
    assert desasignar.status_code == 204


def test_asignar_socio_duplicado_devuelve_409(client, db_session, sede_id):
    _, entrenador = _crear_entrenador(db_session, sede_id)
    socio = _crear_socio(db_session, sede_id)
    token = _token_gestor(db_session, sede_id)

    client.post(f"/entrenadores/{entrenador.id}/socios", headers={"Authorization": f"Bearer {token}"}, json={"socio_id": str(socio.id)})
    response = client.post(f"/entrenadores/{entrenador.id}/socios", headers={"Authorization": f"Bearer {token}"}, json={"socio_id": str(socio.id)})
    assert response.status_code == 409


def test_asignar_socio_de_otra_sede_devuelve_409(client, db_session, sede_id):
    otra_sede = _crear_otra_sede(db_session)
    _, entrenador = _crear_entrenador(db_session, sede_id)
    socio_otra_sede = _crear_socio(db_session, otra_sede.id, "socio-otra-sede@test.com")
    token = _token_gestor(db_session, sede_id)

    response = client.post(
        f"/entrenadores/{entrenador.id}/socios",
        headers={"Authorization": f"Bearer {token}"},
        json={"socio_id": str(socio_otra_sede.id)},
    )
    assert response.status_code == 409


def test_no_se_puede_asignar_socio_a_entrenador_de_baja(client, db_session, sede_id):
    _, entrenador = _crear_entrenador(db_session, sede_id, activo=False)
    socio = _crear_socio(db_session, sede_id)
    token = _token_gestor(db_session, sede_id)

    response = client.post(
        f"/entrenadores/{entrenador.id}/socios",
        headers={"Authorization": f"Bearer {token}"},
        json={"socio_id": str(socio.id)},
    )
    assert response.status_code == 409


def test_desasignar_socio_establece_fecha_fin(client, db_session, sede_id):
    _, entrenador = _crear_entrenador(db_session, sede_id)
    socio = _crear_socio(db_session, sede_id)
    token = _token_gestor(db_session, sede_id)

    client.post(f"/entrenadores/{entrenador.id}/socios", headers={"Authorization": f"Bearer {token}"}, json={"socio_id": str(socio.id)})
    response = client.delete(f"/entrenadores/{entrenador.id}/socios/{socio.id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 204

    asignacion = db_session.query(SocioAsignado).filter(SocioAsignado.entrenador_id == entrenador.id).first()
    assert asignacion.fecha_fin == date.today()


def test_entrenador_ve_solo_sus_socios_asignados(client, db_session, sede_id):
    usuario1, entrenador1 = _crear_entrenador(db_session, sede_id, "entrenador-socios1@test.com")
    usuario2, _entrenador2 = _crear_entrenador(db_session, sede_id, "entrenador-socios2@test.com")
    socio = _crear_socio(db_session, sede_id)
    token_gestor = _token_gestor(db_session, sede_id)

    client.post(f"/entrenadores/{entrenador1.id}/socios", headers={"Authorization": f"Bearer {token_gestor}"}, json={"socio_id": str(socio.id)})

    token1 = identidad_service.create_access_token(usuario1)
    ok = client.get(f"/entrenadores/{entrenador1.id}/socios", headers={"Authorization": f"Bearer {token1}"})
    assert ok.status_code == 200
    assert len(ok.json()) == 1

    token2 = identidad_service.create_access_token(usuario2)
    forbidden = client.get(f"/entrenadores/{entrenador1.id}/socios", headers={"Authorization": f"Bearer {token2}"})
    assert forbidden.status_code == 403


def test_baja_entrenador_sin_clases_futuras(client, db_session, sede_id):
    _, entrenador = _crear_entrenador(db_session, sede_id)
    token = _token_admin(db_session)

    response = client.request(
        "DELETE",
        f"/entrenadores/{entrenador.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )
    assert response.status_code == 200
    assert response.json()["activo"] is False


def test_baja_entrenador_con_clases_futuras_requiere_confirmacion(client, db_session, sede_id):
    _, entrenador = _crear_entrenador(db_session, sede_id)
    clase = Clase(
        sede_id=sede_id, entrenador_id=entrenador.id, nombre="Yoga", tipo="yoga",
        fecha_hora=datetime.utcnow() + timedelta(days=1), duracion_minutos=60,
        aforo_maximo=10, recurrente=False, estado="activa",
    )
    db_session.add(clase)
    db_session.commit()
    token = _token_admin(db_session)

    response = client.request(
        "DELETE",
        f"/entrenadores/{entrenador.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["requiere_confirmacion"] is True
    assert len(body["clases_futuras"]) == 1

    db_session.refresh(entrenador)
    assert entrenador.activo is True


def test_baja_entrenador_confirmando_reasignacion(client, db_session, sede_id):
    _, entrenador = _crear_entrenador(db_session, sede_id, "entrenador-baja@test.com")
    _, nuevo_entrenador = _crear_entrenador(db_session, sede_id, "entrenador-nuevo@test.com")
    clase = Clase(
        sede_id=sede_id, entrenador_id=entrenador.id, nombre="Yoga", tipo="yoga",
        fecha_hora=datetime.utcnow() + timedelta(days=1), duracion_minutos=60,
        aforo_maximo=10, recurrente=False, estado="activa",
    )
    db_session.add(clase)
    db_session.commit()
    db_session.refresh(clase)
    token = _token_admin(db_session)

    response = client.request(
        "DELETE",
        f"/entrenadores/{entrenador.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"confirmar": True, "decision": "reasignar", "nuevo_entrenador_id": str(nuevo_entrenador.id)},
    )
    assert response.status_code == 200
    assert response.json()["activo"] is False

    db_session.refresh(clase)
    assert clase.entrenador_id == nuevo_entrenador.id


def test_baja_entrenador_confirmando_cancelacion(client, db_session, sede_id):
    _, entrenador = _crear_entrenador(db_session, sede_id, "entrenador-baja2@test.com")
    clase = Clase(
        sede_id=sede_id, entrenador_id=entrenador.id, nombre="Yoga", tipo="yoga",
        fecha_hora=datetime.utcnow() + timedelta(days=1), duracion_minutos=60,
        aforo_maximo=10, recurrente=False, estado="activa",
    )
    db_session.add(clase)
    db_session.commit()
    db_session.refresh(clase)
    token = _token_admin(db_session)

    response = client.request(
        "DELETE",
        f"/entrenadores/{entrenador.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"confirmar": True, "decision": "cancelar"},
    )
    assert response.status_code == 200

    db_session.refresh(clase)
    assert clase.estado == "cancelada"


def test_entrenador_inexistente_devuelve_404(client, db_session):
    token = _token_admin(db_session)
    response = client.get(f"/entrenadores/{uuid.uuid4()}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404


