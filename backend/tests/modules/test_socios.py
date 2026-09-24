import uuid
from datetime import date, time
from decimal import Decimal

from app.modules.entrenadores.models import Entrenador, SocioAsignado
from app.modules.entrenamiento import service as entrenamiento_service
from app.modules.identidad import service as identidad_service
from app.modules.membresias.models import PlanMembresia
from app.modules.sedes.models import Sede
from app.modules.socios.models import HistorialAccionSocio, Socio
import pytest

pytestmark = pytest.mark.integration

EJERCICIOS_FICHA = [
    {"nombre": "Sentadilla", "series": 4, "repeticiones": 10, "dia_semana": "lunes", "descanso_segundos": 60},
]

DATOS_SOCIO = {
    "fecha_nacimiento": "1990-05-20",
    "telefono": "600111222",
    "direccion": "Calle Falsa 123",
    "contacto_emergencia_nombre": "Familiar",
    "contacto_emergencia_telefono": "600333444",
}


def _token_admin(db_session):
    admin = identidad_service.crear_usuario(db_session, "admin-socios@test.com", "password123", "admin", None)
    return identidad_service.create_access_token(admin)


def _token_gestor(db_session, sede_id):
    gestor = identidad_service.crear_usuario(db_session, "gestor-socios@test.com", "password123", "gestor_sede", sede_id)
    return identidad_service.create_access_token(gestor)


def _token_entrenador(db_session, sede_id):
    entrenador = identidad_service.crear_usuario(db_session, "entrenador-socios@test.com", "password123", "entrenador", sede_id)
    return identidad_service.create_access_token(entrenador)


def _crear_usuario_socio(db_session, sede_id, email="socio1@test.com"):
    return identidad_service.crear_usuario(db_session, email, "password123", "socio", sede_id)


def _crear_socio(db_session, usuario_id, sede_id, **overrides) -> Socio:
    datos = {
        "usuario_id": usuario_id,
        "sede_id": sede_id,
        "fecha_nacimiento": date(1990, 5, 20),
        "telefono": "600111222",
        "direccion": "Calle Falsa 123",
        "contacto_emergencia_nombre": "Familiar",
        "contacto_emergencia_telefono": "600333444",
    }
    datos.update(overrides)
    socio = Socio(**datos)
    db_session.add(socio)
    db_session.commit()
    db_session.refresh(socio)
    return socio


def test_admin_puede_dar_alta_de_socio(client, db_session, sede_id):
    usuario_socio = _crear_usuario_socio(db_session, sede_id)
    token = _token_admin(db_session)

    response = client.post(
        "/socios",
        headers={"Authorization": f"Bearer {token}"},
        json={"usuario_id": str(usuario_socio.id), "sede_id": str(sede_id), **DATOS_SOCIO},
    )
    assert response.status_code == 201
    assert response.json()["activo"] is True
    assert response.json()["notas"] == []

    socio_id = uuid.UUID(response.json()["id"])
    historial = db_session.query(HistorialAccionSocio).filter(HistorialAccionSocio.socio_id == socio_id).all()
    assert len(historial) == 1
    assert historial[0].accion == "alta"


def test_gestor_sede_no_puede_dar_alta_en_otra_sede(client, db_session, sede_id):
    otra_sede = Sede(
        nombre="Otra sede",
        direccion="Otra calle",
        ciudad="Valencia",
        telefono="600555666",
        horario_apertura=time(7, 0),
        horario_cierre=time(22, 0),
        aforo_maximo=50,
    )
    db_session.add(otra_sede)
    db_session.commit()
    db_session.refresh(otra_sede)

    usuario_socio = _crear_usuario_socio(db_session, otra_sede.id)
    token = _token_gestor(db_session, sede_id)

    response = client.post(
        "/socios",
        headers={"Authorization": f"Bearer {token}"},
        json={"usuario_id": str(usuario_socio.id), "sede_id": str(otra_sede.id), **DATOS_SOCIO},
    )
    assert response.status_code == 403


def test_alta_con_usuario_no_socio_devuelve_422(client, db_session, sede_id):
    entrenador = identidad_service.crear_usuario(db_session, "entrenador-alta@test.com", "password123", "entrenador", sede_id)
    token = _token_admin(db_session)

    response = client.post(
        "/socios",
        headers={"Authorization": f"Bearer {token}"},
        json={"usuario_id": str(entrenador.id), "sede_id": str(sede_id), **DATOS_SOCIO},
    )
    assert response.status_code == 422


def test_alta_duplicada_devuelve_409(client, db_session, sede_id):
    usuario_socio = _crear_usuario_socio(db_session, sede_id)
    _crear_socio(db_session, usuario_socio.id, sede_id)
    token = _token_admin(db_session)

    response = client.post(
        "/socios",
        headers={"Authorization": f"Bearer {token}"},
        json={"usuario_id": str(usuario_socio.id), "sede_id": str(sede_id), **DATOS_SOCIO},
    )
    assert response.status_code == 409


def test_gestor_sede_ve_solo_socios_de_su_sede(client, db_session, sede_id):
    otra_sede = Sede(
        nombre="Otra sede 2",
        direccion="Otra calle 2",
        ciudad="Bilbao",
        telefono="600555667",
        horario_apertura=time(7, 0),
        horario_cierre=time(22, 0),
        aforo_maximo=50,
    )
    db_session.add(otra_sede)
    db_session.commit()
    db_session.refresh(otra_sede)

    usuario_propia = _crear_usuario_socio(db_session, sede_id, "socio-propia@test.com")
    usuario_otra = _crear_usuario_socio(db_session, otra_sede.id, "socio-otra@test.com")
    _crear_socio(db_session, usuario_propia.id, sede_id)
    _crear_socio(db_session, usuario_otra.id, otra_sede.id)

    token = _token_gestor(db_session, sede_id)
    response = client.get("/socios", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    ids_sede = {s["sede_id"] for s in response.json()}
    assert ids_sede == {str(sede_id)}


def test_entrenador_sin_asignaciones_ve_listado_vacio(client, db_session, sede_id):
    usuario_socio = _crear_usuario_socio(db_session, sede_id)
    _crear_socio(db_session, usuario_socio.id, sede_id)
    token = _token_entrenador(db_session, sede_id)

    response = client.get("/socios", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == []


def test_entrenador_ve_solo_sus_socios_asignados(client, db_session, sede_id):
    usuario_entrenador = identidad_service.crear_usuario(
        db_session, "entrenador-asignado@test.com", "password123", "entrenador", sede_id
    )
    entrenador = Entrenador(usuario_id=usuario_entrenador.id, sede_id=sede_id, activo=True)
    db_session.add(entrenador)
    db_session.commit()
    db_session.refresh(entrenador)

    usuario_asignado = _crear_usuario_socio(db_session, sede_id, "socio-asignado@test.com")
    socio_asignado = _crear_socio(db_session, usuario_asignado.id, sede_id)
    usuario_no_asignado = _crear_usuario_socio(db_session, sede_id, "socio-no-asignado@test.com")
    socio_no_asignado = _crear_socio(db_session, usuario_no_asignado.id, sede_id)

    db_session.add(SocioAsignado(entrenador_id=entrenador.id, socio_id=socio_asignado.id))
    db_session.commit()

    token = identidad_service.create_access_token(usuario_entrenador)

    listado = client.get("/socios", headers={"Authorization": f"Bearer {token}"})
    assert listado.status_code == 200
    ids = {s["id"] for s in listado.json()}
    assert ids == {str(socio_asignado.id)}

    detalle_asignado = client.get(f"/socios/{socio_asignado.id}", headers={"Authorization": f"Bearer {token}"})
    assert detalle_asignado.status_code == 200

    detalle_no_asignado = client.get(f"/socios/{socio_no_asignado.id}", headers={"Authorization": f"Bearer {token}"})
    assert detalle_no_asignado.status_code == 403


def test_socio_puede_ver_su_propio_detalle_sin_notas(client, db_session, sede_id):
    usuario_socio = _crear_usuario_socio(db_session, sede_id)
    socio = _crear_socio(db_session, usuario_socio.id, sede_id)
    token = identidad_service.create_access_token(usuario_socio)

    response = client.get(f"/socios/{socio.id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert "notas" not in response.json()


def test_socio_no_puede_ver_otro_socio(client, db_session, sede_id):
    usuario_socio = _crear_usuario_socio(db_session, sede_id, "socio-a@test.com")
    otro_usuario_socio = _crear_usuario_socio(db_session, sede_id, "socio-b@test.com")
    otro_socio = _crear_socio(db_session, otro_usuario_socio.id, sede_id)
    token = identidad_service.create_access_token(usuario_socio)

    response = client.get(f"/socios/{otro_socio.id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_notas_no_visibles_para_propio_socio_pero_si_para_admin(client, db_session, sede_id):
    usuario_socio = _crear_usuario_socio(db_session, sede_id)
    socio = _crear_socio(db_session, usuario_socio.id, sede_id)
    token_admin = _token_admin(db_session)

    nota_response = client.post(
        f"/socios/{socio.id}/notas",
        headers={"Authorization": f"Bearer {token_admin}"},
        json={"contenido": "Nota interna de seguimiento"},
    )
    assert nota_response.status_code == 201

    detalle_admin = client.get(f"/socios/{socio.id}", headers={"Authorization": f"Bearer {token_admin}"})
    assert len(detalle_admin.json()["notas"]) == 1

    token_socio = identidad_service.create_access_token(usuario_socio)
    detalle_socio = client.get(f"/socios/{socio.id}", headers={"Authorization": f"Bearer {token_socio}"})
    assert "notas" not in detalle_socio.json()


def test_socio_puede_editar_sus_datos_de_contacto(client, db_session, sede_id):
    usuario_socio = _crear_usuario_socio(db_session, sede_id)
    socio = _crear_socio(db_session, usuario_socio.id, sede_id)
    token = identidad_service.create_access_token(usuario_socio)

    response = client.put(
        f"/socios/{socio.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"telefono": "699888777"},
    )
    assert response.status_code == 200
    assert response.json()["telefono"] == "699888777"


def test_socio_no_puede_editar_fecha_nacimiento(client, db_session, sede_id):
    usuario_socio = _crear_usuario_socio(db_session, sede_id)
    socio = _crear_socio(db_session, usuario_socio.id, sede_id)
    token = identidad_service.create_access_token(usuario_socio)

    response = client.put(
        f"/socios/{socio.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"fecha_nacimiento": "2000-01-01"},
    )
    assert response.status_code == 403


def test_gestor_sede_no_puede_editar_socio_de_otra_sede(client, db_session, sede_id):
    otra_sede = Sede(
        nombre="Otra sede 3",
        direccion="Otra calle 3",
        ciudad="Zaragoza",
        telefono="600555668",
        horario_apertura=time(7, 0),
        horario_cierre=time(22, 0),
        aforo_maximo=50,
    )
    db_session.add(otra_sede)
    db_session.commit()
    db_session.refresh(otra_sede)

    usuario_socio = _crear_usuario_socio(db_session, otra_sede.id)
    socio = _crear_socio(db_session, usuario_socio.id, otra_sede.id)
    token = _token_gestor(db_session, sede_id)

    response = client.put(
        f"/socios/{socio.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"telefono": "699888777"},
    )
    assert response.status_code == 403


def test_put_socio_con_fecha_nacimiento_null_devuelve_422(client, db_session, sede_id):
    usuario_socio = _crear_usuario_socio(db_session, sede_id)
    socio = _crear_socio(db_session, usuario_socio.id, sede_id)
    token = _token_admin(db_session)

    response = client.put(
        f"/socios/{socio.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"fecha_nacimiento": None},
    )
    assert response.status_code == 422


def test_put_socio_parcial_sigue_funcionando(client, db_session, sede_id):
    usuario_socio = _crear_usuario_socio(db_session, sede_id)
    socio = _crear_socio(db_session, usuario_socio.id, sede_id)
    token = _token_admin(db_session)

    response_omitido = client.put(
        f"/socios/{socio.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"telefono": "699111222"},
    )
    assert response_omitido.status_code == 200
    assert response_omitido.json()["telefono"] == "699111222"
    assert response_omitido.json()["fecha_nacimiento"] == str(socio.fecha_nacimiento)

    response_valido = client.put(
        f"/socios/{socio.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"fecha_nacimiento": "2001-05-20"},
    )
    assert response_valido.status_code == 200
    assert response_valido.json()["fecha_nacimiento"] == "2001-05-20"


def test_admin_puede_dar_de_baja_socio(client, db_session, sede_id):
    usuario_socio = _crear_usuario_socio(db_session, sede_id)
    socio = _crear_socio(db_session, usuario_socio.id, sede_id)
    token = _token_admin(db_session)

    response = client.delete(f"/socios/{socio.id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 204

    db_session.refresh(socio)
    assert socio.activo is False
    assert socio.fecha_baja == date.today()

    historial = (
        db_session.query(HistorialAccionSocio)
        .filter(HistorialAccionSocio.socio_id == socio.id, HistorialAccionSocio.accion == "baja")
        .all()
    )
    assert len(historial) == 1


def test_subir_documento_de_socio(client, db_session, sede_id):
    usuario_socio = _crear_usuario_socio(db_session, sede_id)
    socio = _crear_socio(db_session, usuario_socio.id, sede_id)
    token = _token_admin(db_session)

    response = client.post(
        f"/socios/{socio.id}/documentos",
        headers={"Authorization": f"Bearer {token}"},
        json={"tipo": "aptitud_medica", "archivo_url": "https://files.test/cert.pdf", "fecha_caducidad": "2027-01-01"},
    )
    assert response.status_code == 201
    assert response.json()["tipo"] == "aptitud_medica"


def test_transferir_socio_actualiza_sede_y_registra_historial(client, db_session, sede_id):
    nueva_sede = Sede(
        nombre="Sede destino",
        direccion="Calle destino",
        ciudad="Malaga",
        telefono="600555669",
        horario_apertura=time(7, 0),
        horario_cierre=time(22, 0),
        aforo_maximo=50,
    )
    db_session.add(nueva_sede)
    db_session.commit()
    db_session.refresh(nueva_sede)

    usuario_socio = _crear_usuario_socio(db_session, sede_id)
    socio = _crear_socio(db_session, usuario_socio.id, sede_id)
    token = _token_admin(db_session)

    response = client.post(
        f"/socios/{socio.id}/transferir",
        headers={"Authorization": f"Bearer {token}"},
        json={"nueva_sede_id": str(nueva_sede.id)},
    )
    assert response.status_code == 200
    assert response.json()["sede_id"] == str(nueva_sede.id)


def _crear_plan_membresia(db_session, sede_id) -> PlanMembresia:
    plan = PlanMembresia(nombre="Mensual", precio=Decimal("30.00"), duracion="mensual", alcance="sede_unica", sede_id=sede_id, activo=True)
    db_session.add(plan)
    db_session.commit()
    db_session.refresh(plan)
    return plan


def _crear_entrenador_asignado(db_session, sede_id, socio_id, email="entrenador-ficha@test.com") -> tuple:
    usuario_entrenador = identidad_service.crear_usuario(db_session, email, "password123", "entrenador", sede_id)
    entrenador = Entrenador(usuario_id=usuario_entrenador.id, sede_id=sede_id, especialidades=["yoga"], activo=True)
    db_session.add(entrenador)
    db_session.commit()
    db_session.refresh(entrenador)
    db_session.add(SocioAsignado(entrenador_id=entrenador.id, socio_id=socio_id))
    db_session.commit()
    return usuario_entrenador, entrenador


def test_admin_ve_ficha_completa_de_socio_sin_notas(client, db_session, sede_id):
    usuario_socio = _crear_usuario_socio(db_session, sede_id)
    socio = _crear_socio(db_session, usuario_socio.id, sede_id)
    plan = _crear_plan_membresia(db_session, sede_id)
    _, entrenador = _crear_entrenador_asignado(db_session, sede_id, socio.id)
    entrenamiento_service.crear_rutina(db_session, entrenador.id, socio.id, "Fuerza", EJERCICIOS_FICHA)
    entrenamiento_service.crear_plan_nutricional(db_session, entrenador.id, socio.id, "Definición", "Comidas cada 3 horas")

    token_admin = _token_admin(db_session)
    membresia_resp = client.post(
        "/membresias",
        headers={"Authorization": f"Bearer {token_admin}"},
        json={"socio_id": str(socio.id), "plan_id": str(plan.id)},
    )
    assert membresia_resp.status_code == 201

    response = client.get(f"/socios/{socio.id}/ficha", headers={"Authorization": f"Bearer {token_admin}"})
    assert response.status_code == 200
    body = response.json()
    assert "notas" not in body
    assert body["membresia"]["estado"] == "activa"
    assert body["entrenador_asignado"]["email"] == "entrenador-ficha@test.com"
    assert len(body["rutinas"]) == 1
    assert len(body["rutinas"][0]["ejercicios"]) == 1
    assert len(body["planes_nutricionales"]) == 1


def test_gestor_sede_no_puede_ver_ficha_de_socio_de_otra_sede(client, db_session, sede_id):
    otra_sede = Sede(
        nombre="Otra sede ficha",
        direccion="Otra calle ficha",
        ciudad="Sevilla",
        telefono="600555670",
        horario_apertura=time(7, 0),
        horario_cierre=time(22, 0),
        aforo_maximo=50,
    )
    db_session.add(otra_sede)
    db_session.commit()
    db_session.refresh(otra_sede)

    usuario_socio = _crear_usuario_socio(db_session, otra_sede.id)
    socio = _crear_socio(db_session, usuario_socio.id, otra_sede.id)
    token = _token_gestor(db_session, sede_id)

    response = client.get(f"/socios/{socio.id}/ficha", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_entrenador_ve_ficha_de_socio_asignado_sin_notas(client, db_session, sede_id):
    usuario_socio = _crear_usuario_socio(db_session, sede_id)
    socio = _crear_socio(db_session, usuario_socio.id, sede_id)
    usuario_entrenador, entrenador = _crear_entrenador_asignado(db_session, sede_id, socio.id, "entrenador-ficha-2@test.com")
    token = identidad_service.create_access_token(usuario_entrenador)

    response = client.get(f"/socios/{socio.id}/ficha", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert "notas" not in response.json()
    assert response.json()["entrenador_asignado"]["id"] == str(entrenador.id)


def test_entrenador_no_puede_ver_ficha_de_socio_no_asignado(client, db_session, sede_id):
    usuario_socio = _crear_usuario_socio(db_session, sede_id)
    socio = _crear_socio(db_session, usuario_socio.id, sede_id)
    token = _token_entrenador(db_session, sede_id)

    response = client.get(f"/socios/{socio.id}/ficha", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_socio_inexistente_devuelve_404(client, db_session):
    token = _token_admin(db_session)
    response = client.get(f"/socios/{uuid.uuid4()}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404


def test_socio_puede_resolver_su_propio_socio_id_via_me(client, db_session, sede_id):
    usuario_socio = _crear_usuario_socio(db_session, sede_id)
    socio = _crear_socio(db_session, usuario_socio.id, sede_id)
    token = identidad_service.create_access_token(usuario_socio)

    response = client.get("/socios/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["id"] == str(socio.id)
    assert "notas" not in response.json()


def test_me_devuelve_404_si_usuario_sin_socio_asociado(client, db_session, sede_id):
    usuario_socio = _crear_usuario_socio(db_session, sede_id, "sin-socio@test.com")
    token = identidad_service.create_access_token(usuario_socio)

    response = client.get("/socios/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404


def test_me_no_accesible_para_otros_roles(client, db_session):
    token = _token_admin(db_session)
    response = client.get("/socios/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
