import uuid

import pytest
from fastapi import HTTPException

from app.modules.identidad import service
from app.modules.identidad.dependencies import verificar_acceso_por_sede
from app.modules.identidad.models import TokenRecuperacion, Usuario


def test_register_publico_socio_ok(client):
    response = client.post(
        "/auth/register",
        json={"email": "socio1@test.com", "password": "password123", "rol": "socio", "sede_id": None},
    )
    assert response.status_code == 422  # sede_id es obligatorio para socio


def test_register_publico_socio_con_sede_ok(client, sede_id):
    response = client.post(
        "/auth/register",
        json={"email": "socio2@test.com", "password": "password123", "rol": "socio", "sede_id": str(sede_id)},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "socio2@test.com"
    assert body["rol"] == "socio"


def test_register_publico_rol_no_socio_prohibido(client, sede_id):
    response = client.post(
        "/auth/register",
        json={"email": "entrenador1@test.com", "password": "password123", "rol": "entrenador", "sede_id": str(sede_id)},
    )
    assert response.status_code == 403


def test_register_email_duplicado(client, db_session, sede_id):
    service.crear_usuario(db_session, "duplicado@test.com", "password123", "socio", sede_id)

    response = client.post(
        "/auth/register",
        json={"email": "duplicado@test.com", "password": "password123", "rol": "socio", "sede_id": str(sede_id)},
    )
    assert response.status_code == 409


def test_admin_puede_crear_entrenador(client, db_session, sede_id):
    admin = service.crear_usuario(db_session, "admin@test.com", "password123", "admin", None)
    token = service.create_access_token(admin)

    response = client.post(
        "/auth/register",
        headers={"Authorization": f"Bearer {token}"},
        json={"email": "entrenador2@test.com", "password": "password123", "rol": "entrenador", "sede_id": str(sede_id)},
    )
    assert response.status_code == 201
    assert response.json()["rol"] == "entrenador"


def test_gestor_sede_no_puede_crear_admin(client, db_session, sede_id):
    gestor = service.crear_usuario(db_session, "gestor@test.com", "password123", "gestor_sede", sede_id)
    token = service.create_access_token(gestor)

    response = client.post(
        "/auth/register",
        headers={"Authorization": f"Bearer {token}"},
        json={"email": "otroadmin@test.com", "password": "password123", "rol": "admin", "sede_id": None},
    )
    assert response.status_code == 403


def test_login_correcto_devuelve_token(client, db_session, sede_id):
    service.crear_usuario(db_session, "loginok@test.com", "password123", "socio", sede_id)

    response = client.post("/auth/login", json={"email": "loginok@test.com", "password": "password123"})
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_password_incorrecta_registra_intento(client, db_session, sede_id):
    service.crear_usuario(db_session, "loginfail@test.com", "password123", "socio", sede_id)

    response = client.post("/auth/login", json={"email": "loginfail@test.com", "password": "incorrecta"})
    assert response.status_code == 401


def test_login_bloqueado_tras_5_intentos(client, db_session, sede_id):
    service.crear_usuario(db_session, "bloqueo@test.com", "password123", "socio", sede_id)

    for _ in range(5):
        client.post("/auth/login", json={"email": "bloqueo@test.com", "password": "incorrecta"})

    response = client.post("/auth/login", json={"email": "bloqueo@test.com", "password": "password123"})
    assert response.status_code == 429


def test_me_requiere_token(client):
    response = client.get("/auth/me")
    assert response.status_code in (401, 403)


def test_me_con_token_valido(client, db_session, sede_id):
    usuario = service.crear_usuario(db_session, "me@test.com", "password123", "socio", sede_id)
    token = service.create_access_token(usuario)

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "me@test.com"


def test_logout_requiere_token(client):
    response = client.post("/auth/logout")
    assert response.status_code in (401, 403)


def test_forgot_password_genera_token(client, db_session, sede_id):
    service.crear_usuario(db_session, "forgot@test.com", "password123", "socio", sede_id)

    response = client.post("/auth/forgot-password", json={"email": "forgot@test.com"})
    assert response.status_code == 204

    registro = db_session.query(TokenRecuperacion).join(Usuario).filter(Usuario.email == "forgot@test.com").first()
    assert registro is not None


def test_forgot_password_email_inexistente_no_filtra_info(client):
    response = client.post("/auth/forgot-password", json={"email": "noexiste@test.com"})
    assert response.status_code == 204


def test_reset_password_con_token_valido(client, db_session, sede_id):
    usuario = service.crear_usuario(db_session, "reset@test.com", "password123", "socio", sede_id)
    token_recuperacion = service.generar_token_recuperacion(db_session, usuario)

    response = client.post(
        "/auth/reset-password",
        json={"token": token_recuperacion.token, "password": "nuevapassword123"},
    )
    assert response.status_code == 204

    login_response = client.post("/auth/login", json={"email": "reset@test.com", "password": "nuevapassword123"})
    assert login_response.status_code == 200


def test_reset_password_token_invalido(client):
    response = client.post("/auth/reset-password", json={"token": "no-existe", "password": "nuevapassword123"})
    assert response.status_code == 400


def test_verificar_acceso_por_sede_admin_siempre_pasa():
    admin = Usuario(id=uuid.uuid4(), rol="admin", sede_id=None)
    verificar_acceso_por_sede(admin, sede_id=uuid.uuid4())


def test_verificar_acceso_por_sede_gestor_sede_coincide_pasa():
    sede_id = uuid.uuid4()
    gestor = Usuario(id=uuid.uuid4(), rol="gestor_sede", sede_id=sede_id)
    verificar_acceso_por_sede(gestor, sede_id=sede_id)


def test_verificar_acceso_por_sede_gestor_sede_distinta_falla():
    gestor = Usuario(id=uuid.uuid4(), rol="gestor_sede", sede_id=uuid.uuid4())
    with pytest.raises(HTTPException) as exc:
        verificar_acceso_por_sede(gestor, sede_id=uuid.uuid4())
    assert exc.value.status_code == 403


def test_verificar_acceso_por_sede_propietario_coincide_pasa():
    socio_id = uuid.uuid4()
    socio = Usuario(id=socio_id, rol="socio", sede_id=None)
    verificar_acceso_por_sede(
        socio, sede_id=uuid.uuid4(), propietario_id=socio_id, rol_propietario="socio"
    )


def test_verificar_acceso_por_sede_propietario_distinto_falla():
    socio = Usuario(id=uuid.uuid4(), rol="socio", sede_id=None)
    with pytest.raises(HTTPException) as exc:
        verificar_acceso_por_sede(
            socio, sede_id=uuid.uuid4(), propietario_id=uuid.uuid4(), rol_propietario="socio"
        )
    assert exc.value.status_code == 403


def test_verificar_acceso_por_sede_sin_rol_propietario_solo_admin_gestor():
    # Caso de sedes/entrenadores: sin propietario_id/rol_propietario, ningún
    # otro rol distinto de admin/gestor_sede puede pasar.
    entrenador = Usuario(id=uuid.uuid4(), rol="entrenador", sede_id=uuid.uuid4())
    with pytest.raises(HTTPException) as exc:
        verificar_acceso_por_sede(entrenador, sede_id=uuid.uuid4())
    assert exc.value.status_code == 403
