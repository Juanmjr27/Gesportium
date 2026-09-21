import uuid
from datetime import date

import httpx
import pytest

from app.modules.asistente_ia import router as asistente_router
from app.modules.asistente_ia.models import BorradorIA, MensajeIA
from app.modules.asistente_ia.service import (
    generar_contenido_borrador,
    generar_respuesta_chat,
)
from app.modules.entrenadores.models import Entrenador, SocioAsignado
from app.modules.entrenamiento.models import PlanNutricional, Rutina
from app.modules.identidad import service as identidad_service
from app.modules.socios.models import Socio

EJERCICIOS = [
    {"nombre": "Sentadilla", "series": 4, "repeticiones": 10, "dia_semana": "lunes", "descanso_segundos": 60},
]

RUTINA_PAYLOAD = {
    "tipo_borrador": "rutina",
    "sexo": "masculino",
    "peso_kg": 78,
    "altura_cm": 178,
    "nivel_actividad_actual": "activo",
    "dias_disponibles_semana": 4,
    "equipamiento": "gimnasio_completo",
    "objetivo_principal": "ganar_masa_muscular",
}

PLAN_NUTRICIONAL_PAYLOAD = {
    "tipo_borrador": "plan_nutricional",
    "sexo": "femenino",
    "peso_kg": 65,
    "altura_cm": 165,
    "preferencia_alimentaria": "omnivoro",
    "comidas_al_dia": 4,
    "objetivo_principal": "perder_peso",
}


def _crear_socio(db_session, sede_id, email="socio-ia@test.com") -> tuple:
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


def _crear_entrenador(db_session, sede_id, email="entrenador-ia@test.com") -> tuple:
    usuario = identidad_service.crear_usuario(db_session, email, "password123", "entrenador", sede_id)
    entrenador = Entrenador(usuario_id=usuario.id, sede_id=sede_id, activo=True)
    db_session.add(entrenador)
    db_session.commit()
    db_session.refresh(entrenador)
    return usuario, entrenador


def _asignar(db_session, entrenador_id, socio_id):
    db_session.add(SocioAsignado(entrenador_id=entrenador_id, socio_id=socio_id))
    db_session.commit()


def _crear_borrador(
    db_session, socio_id, tipo="rutina", contenido=None, estado="pendiente", datos_cuestionario=None
) -> BorradorIA:
    borrador = BorradorIA(
        socio_id=socio_id,
        tipo=tipo,
        datos_cuestionario=datos_cuestionario or {"tipo_borrador": tipo},
        contenido=contenido or {"nombre": "Rutina IA", "ejercicios": EJERCICIOS},
        estado=estado,
    )
    db_session.add(borrador)
    db_session.commit()
    db_session.refresh(borrador)
    return borrador


def test_socio_envia_mensaje_y_recibe_respuesta(client, db_session, sede_id, monkeypatch):
    usuario, _socio = _crear_socio(db_session, sede_id)
    token = identidad_service.create_access_token(usuario)
    monkeypatch.setattr(asistente_router, "generar_respuesta_chat", lambda historial, mensaje: "Abrimos de 7 a 22.")

    response = client.post(
        "/asistente/mensaje", json={"contenido": "¿A qué hora abren?"}, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    assert response.json()["rol"] == "asistente"
    assert response.json()["contenido"] == "Abrimos de 7 a 22."

    mensajes = db_session.query(MensajeIA).all()
    assert len(mensajes) == 2
    assert {m.rol for m in mensajes} == {"socio", "asistente"}


def test_mensaje_si_ollama_no_responde_devuelve_503_sin_bloquear(client, db_session, sede_id, monkeypatch):
    usuario, _socio = _crear_socio(db_session, sede_id)
    token = identidad_service.create_access_token(usuario)
    monkeypatch.setattr(asistente_router, "generar_respuesta_chat", lambda historial, mensaje: None)

    response = client.post(
        "/asistente/mensaje", json={"contenido": "Hola"}, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 503

    # El mensaje del socio queda registrado aunque el asistente falle.
    mensajes = db_session.query(MensajeIA).all()
    assert len(mensajes) == 1
    assert mensajes[0].rol == "socio"


def test_historial_vacio_si_no_hay_conversacion(client, db_session, sede_id):
    usuario, _socio = _crear_socio(db_session, sede_id)
    token = identidad_service.create_access_token(usuario)

    response = client.get("/asistente/historial", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == []


def test_historial_devuelve_conversacion_ordenada(client, db_session, sede_id, monkeypatch):
    usuario, _socio = _crear_socio(db_session, sede_id)
    token = identidad_service.create_access_token(usuario)
    monkeypatch.setattr(asistente_router, "generar_respuesta_chat", lambda historial, mensaje: "Respuesta 1")
    client.post("/asistente/mensaje", json={"contenido": "Pregunta 1"}, headers={"Authorization": f"Bearer {token}"})

    response = client.get("/asistente/historial", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0]["contenido"] == "Pregunta 1"
    assert body[1]["contenido"] == "Respuesta 1"


def test_socio_no_ve_historial_de_otro_socio(client, db_session, sede_id, monkeypatch):
    usuario1, _socio1 = _crear_socio(db_session, sede_id, "socio1-ia@test.com")
    usuario2, _socio2 = _crear_socio(db_session, sede_id, "socio2-ia@test.com")
    token1 = identidad_service.create_access_token(usuario1)
    token2 = identidad_service.create_access_token(usuario2)

    monkeypatch.setattr(asistente_router, "generar_respuesta_chat", lambda historial, mensaje: "Respuesta")
    client.post("/asistente/mensaje", json={"contenido": "Secreto de socio1"}, headers={"Authorization": f"Bearer {token1}"})

    response = client.get("/asistente/historial", headers={"Authorization": f"Bearer {token2}"})
    assert response.status_code == 200
    assert response.json() == []


def test_socio_solicita_borrador_de_rutina(client, db_session, sede_id, monkeypatch):
    usuario, _socio = _crear_socio(db_session, sede_id)
    token = identidad_service.create_access_token(usuario)
    contenido = {"nombre": "Rutina IA", "ejercicios": EJERCICIOS}
    monkeypatch.setattr(asistente_router, "generar_contenido_borrador", lambda *a, **k: contenido)

    response = client.post(
        "/asistente/borrador",
        json=RUTINA_PAYLOAD,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["estado"] == "pendiente"
    assert body["contenido"] == contenido


def test_socio_solicita_borrador_de_plan_nutricional(client, db_session, sede_id, monkeypatch):
    usuario, _socio = _crear_socio(db_session, sede_id)
    token = identidad_service.create_access_token(usuario)
    contenido = {"nombre": "Plan IA", "notas": "Bajo en grasas"}
    monkeypatch.setattr(asistente_router, "generar_contenido_borrador", lambda *a, **k: contenido)

    response = client.post(
        "/asistente/borrador",
        json=PLAN_NUTRICIONAL_PAYLOAD,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["tipo"] == "plan_nutricional"
    assert body["contenido"] == contenido


def test_solicitar_borrador_rutina_sin_campos_obligatorios_de_rutina_falla_422(client, db_session, sede_id):
    usuario, _socio = _crear_socio(db_session, sede_id)
    token = identidad_service.create_access_token(usuario)
    payload = {
        "tipo_borrador": "rutina",
        "peso_kg": 78,
        "altura_cm": 178,
        "objetivo_principal": "ganar_masa_muscular",
        # faltan nivel_actividad_actual, dias_disponibles_semana, equipamiento
    }

    response = client.post("/asistente/borrador", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 422


def test_solicitar_borrador_plan_nutricional_sin_campos_obligatorios_falla_422(client, db_session, sede_id):
    usuario, _socio = _crear_socio(db_session, sede_id)
    token = identidad_service.create_access_token(usuario)
    payload = {
        "tipo_borrador": "plan_nutricional",
        "peso_kg": 65,
        "altura_cm": 165,
        "objetivo_principal": "perder_peso",
        # faltan preferencia_alimentaria, comidas_al_dia
    }

    response = client.post("/asistente/borrador", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 422


@pytest.mark.parametrize(
    "campo, valor",
    [
        ("peso_kg", 19),
        ("peso_kg", 301),
        ("altura_cm", 99),
        ("altura_cm", 251),
        ("dias_disponibles_semana", 0),
        ("dias_disponibles_semana", 8),
        ("objetivo_detalle", "x" * 281),
    ],
)
def test_solicitar_borrador_rutina_rechaza_valores_fuera_de_rango(client, db_session, sede_id, campo, valor):
    usuario, _socio = _crear_socio(db_session, sede_id)
    token = identidad_service.create_access_token(usuario)
    payload = {**RUTINA_PAYLOAD, campo: valor}

    response = client.post("/asistente/borrador", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 422


@pytest.mark.parametrize("campo, valor", [("comidas_al_dia", 1), ("comidas_al_dia", 7)])
def test_solicitar_borrador_plan_nutricional_rechaza_comidas_al_dia_fuera_de_rango(
    client, db_session, sede_id, campo, valor
):
    usuario, _socio = _crear_socio(db_session, sede_id)
    token = identidad_service.create_access_token(usuario)
    payload = {**PLAN_NUTRICIONAL_PAYLOAD, campo: valor}

    response = client.post("/asistente/borrador", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 422


def test_borrador_si_ollama_no_responde_devuelve_503(client, db_session, sede_id, monkeypatch):
    usuario, _socio = _crear_socio(db_session, sede_id)
    token = identidad_service.create_access_token(usuario)
    monkeypatch.setattr(asistente_router, "generar_contenido_borrador", lambda *a, **k: None)

    response = client.post(
        "/asistente/borrador",
        json=PLAN_NUTRICIONAL_PAYLOAD,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 503
    assert db_session.query(BorradorIA).count() == 0


def test_datos_cuestionario_se_persiste_y_pendientes_lo_devuelve(client, db_session, sede_id, monkeypatch):
    usuario_e, entrenador = _crear_entrenador(db_session, sede_id)
    usuario_s, socio = _crear_socio(db_session, sede_id)
    _asignar(db_session, entrenador.id, socio.id)
    token_s = identidad_service.create_access_token(usuario_s)
    token_e = identidad_service.create_access_token(usuario_e)
    contenido = {"nombre": "Rutina IA", "ejercicios": EJERCICIOS}
    monkeypatch.setattr(asistente_router, "generar_contenido_borrador", lambda *a, **k: contenido)

    response = client.post("/asistente/borrador", json=RUTINA_PAYLOAD, headers={"Authorization": f"Bearer {token_s}"})
    assert response.status_code == 201
    borrador_id = response.json()["id"]

    borrador_db = db_session.get(BorradorIA, uuid.UUID(borrador_id))
    assert borrador_db.datos_cuestionario["peso_kg"] == RUTINA_PAYLOAD["peso_kg"]
    assert borrador_db.datos_cuestionario["equipamiento"] == RUTINA_PAYLOAD["equipamiento"]

    response_pendientes = client.get(
        "/asistente/borradores-pendientes", headers={"Authorization": f"Bearer {token_e}"}
    )
    assert response_pendientes.status_code == 200
    body = response_pendientes.json()
    assert len(body) == 1
    assert body[0]["datos_cuestionario"]["peso_kg"] == RUTINA_PAYLOAD["peso_kg"]
    assert body[0]["contenido"] == contenido


def test_entrenador_ve_borradores_pendientes_de_sus_socios(client, db_session, sede_id):
    usuario_e, entrenador = _crear_entrenador(db_session, sede_id)
    _usuario_s1, socio1 = _crear_socio(db_session, sede_id, "socio1-borr@test.com")
    _usuario_s2, socio2 = _crear_socio(db_session, sede_id, "socio2-borr@test.com")
    _asignar(db_session, entrenador.id, socio1.id)
    _crear_borrador(db_session, socio1.id)
    _crear_borrador(db_session, socio2.id)  # socio no asignado a este entrenador

    token_e = identidad_service.create_access_token(usuario_e)
    response = client.get("/asistente/borradores-pendientes", headers={"Authorization": f"Bearer {token_e}"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["socio_id"] == str(socio1.id)


def test_entrenador_aprueba_borrador_de_rutina_crea_rutina_real(client, db_session, sede_id):
    usuario_e, entrenador = _crear_entrenador(db_session, sede_id)
    _usuario_s, socio = _crear_socio(db_session, sede_id)
    _asignar(db_session, entrenador.id, socio.id)
    borrador = _crear_borrador(db_session, socio.id, "rutina", {"nombre": "Rutina IA", "ejercicios": EJERCICIOS})
    token_e = identidad_service.create_access_token(usuario_e)

    response = client.post(f"/asistente/borradores/{borrador.id}/aprobar", headers={"Authorization": f"Bearer {token_e}"})
    assert response.status_code == 200
    assert response.json()["estado"] == "aprobado"
    assert response.json()["entrenador_revisor_id"] == str(entrenador.id)

    rutina = db_session.query(Rutina).filter(Rutina.borrador_id == borrador.id).one()
    assert rutina.origen == "ia"
    assert rutina.socio_id == socio.id


def test_entrenador_aprueba_borrador_de_nutricion_crea_plan_real(client, db_session, sede_id):
    usuario_e, entrenador = _crear_entrenador(db_session, sede_id)
    _usuario_s, socio = _crear_socio(db_session, sede_id)
    _asignar(db_session, entrenador.id, socio.id)
    borrador = _crear_borrador(db_session, socio.id, "plan_nutricional", {"nombre": "Plan IA", "notas": "Bajo en grasas"})
    token_e = identidad_service.create_access_token(usuario_e)

    response = client.post(f"/asistente/borradores/{borrador.id}/aprobar", headers={"Authorization": f"Bearer {token_e}"})
    assert response.status_code == 200

    plan = db_session.query(PlanNutricional).filter(PlanNutricional.borrador_id == borrador.id).one()
    assert plan.origen == "ia"


def test_aprobar_borrador_con_contenido_invalido_rechaza_aprobacion(client, db_session, sede_id):
    usuario_e, entrenador = _crear_entrenador(db_session, sede_id)
    _usuario_s, socio = _crear_socio(db_session, sede_id)
    _asignar(db_session, entrenador.id, socio.id)
    borrador = _crear_borrador(db_session, socio.id, "rutina", {"nombre": "Rutina IA"})  # falta "ejercicios"
    token_e = identidad_service.create_access_token(usuario_e)

    response = client.post(f"/asistente/borradores/{borrador.id}/aprobar", headers={"Authorization": f"Bearer {token_e}"})
    assert response.status_code == 400

    db_session.refresh(borrador)
    assert borrador.estado == "pendiente"


def test_entrenador_no_puede_aprobar_borrador_de_socio_no_asignado(client, db_session, sede_id):
    usuario_e, _entrenador = _crear_entrenador(db_session, sede_id)
    _usuario_s, socio = _crear_socio(db_session, sede_id)
    borrador = _crear_borrador(db_session, socio.id)
    token_e = identidad_service.create_access_token(usuario_e)

    response = client.post(f"/asistente/borradores/{borrador.id}/aprobar", headers={"Authorization": f"Bearer {token_e}"})
    assert response.status_code == 403


def test_no_se_puede_aprobar_borrador_ya_revisado(client, db_session, sede_id):
    usuario_e, entrenador = _crear_entrenador(db_session, sede_id)
    _usuario_s, socio = _crear_socio(db_session, sede_id)
    _asignar(db_session, entrenador.id, socio.id)
    borrador = _crear_borrador(db_session, socio.id, estado="aprobado")
    token_e = identidad_service.create_access_token(usuario_e)

    response = client.post(f"/asistente/borradores/{borrador.id}/aprobar", headers={"Authorization": f"Bearer {token_e}"})
    assert response.status_code == 409


def test_entrenador_rechaza_borrador_con_motivo(client, db_session, sede_id):
    usuario_e, entrenador = _crear_entrenador(db_session, sede_id)
    _usuario_s, socio = _crear_socio(db_session, sede_id)
    _asignar(db_session, entrenador.id, socio.id)
    borrador = _crear_borrador(db_session, socio.id)
    token_e = identidad_service.create_access_token(usuario_e)

    response = client.post(
        f"/asistente/borradores/{borrador.id}/rechazar",
        json={"motivo": "No se ajusta a las condiciones médicas del socio."},
        headers={"Authorization": f"Bearer {token_e}"},
    )
    assert response.status_code == 200
    assert response.json()["estado"] == "rechazado"
    assert response.json()["motivo_rechazo"] == "No se ajusta a las condiciones médicas del socio."

    assert db_session.query(Rutina).filter(Rutina.borrador_id == borrador.id).count() == 0

    db_session.refresh(borrador)
    assert borrador.motivo_rechazo == "No se ajusta a las condiciones médicas del socio."


def test_rechazar_borrador_sin_motivo_falla_422(client, db_session, sede_id):
    usuario_e, entrenador = _crear_entrenador(db_session, sede_id)
    _usuario_s, socio = _crear_socio(db_session, sede_id)
    _asignar(db_session, entrenador.id, socio.id)
    borrador = _crear_borrador(db_session, socio.id)
    token_e = identidad_service.create_access_token(usuario_e)

    response = client.post(
        f"/asistente/borradores/{borrador.id}/rechazar",
        json={},
        headers={"Authorization": f"Bearer {token_e}"},
    )
    assert response.status_code == 422
    db_session.refresh(borrador)
    assert borrador.estado == "pendiente"


def test_rechazar_borrador_con_motivo_vacio_falla_422(client, db_session, sede_id):
    usuario_e, entrenador = _crear_entrenador(db_session, sede_id)
    _usuario_s, socio = _crear_socio(db_session, sede_id)
    _asignar(db_session, entrenador.id, socio.id)
    borrador = _crear_borrador(db_session, socio.id)
    token_e = identidad_service.create_access_token(usuario_e)

    response = client.post(
        f"/asistente/borradores/{borrador.id}/rechazar",
        json={"motivo": ""},
        headers={"Authorization": f"Bearer {token_e}"},
    )
    assert response.status_code == 422


def test_entrenador_edita_borrador_pendiente_de_socio_asignado(client, db_session, sede_id):
    usuario_e, entrenador = _crear_entrenador(db_session, sede_id)
    _usuario_s, socio = _crear_socio(db_session, sede_id)
    _asignar(db_session, entrenador.id, socio.id)
    borrador = _crear_borrador(db_session, socio.id, "rutina", {"nombre": "Rutina IA", "ejercicios": EJERCICIOS})
    token_e = identidad_service.create_access_token(usuario_e)

    nuevo_contenido = {"nombre": "Rutina IA editada", "ejercicios": EJERCICIOS}
    response = client.patch(
        f"/asistente/borradores/{borrador.id}",
        json={"contenido": nuevo_contenido},
        headers={"Authorization": f"Bearer {token_e}"},
    )
    assert response.status_code == 200
    assert response.json()["contenido"] == nuevo_contenido
    assert response.json()["estado"] == "pendiente"

    db_session.refresh(borrador)
    assert borrador.contenido == nuevo_contenido
    assert borrador.estado == "pendiente"


def test_entrenador_no_puede_editar_borrador_de_socio_no_asignado(client, db_session, sede_id):
    usuario_e, _entrenador = _crear_entrenador(db_session, sede_id)
    _usuario_s, socio = _crear_socio(db_session, sede_id)
    borrador = _crear_borrador(db_session, socio.id)
    token_e = identidad_service.create_access_token(usuario_e)

    response = client.patch(
        f"/asistente/borradores/{borrador.id}",
        json={"contenido": {"nombre": "Hackeado", "ejercicios": EJERCICIOS}},
        headers={"Authorization": f"Bearer {token_e}"},
    )
    assert response.status_code == 403


def test_entrenador_no_puede_editar_borrador_ya_revisado(client, db_session, sede_id):
    usuario_e, entrenador = _crear_entrenador(db_session, sede_id)
    _usuario_s, socio = _crear_socio(db_session, sede_id)
    _asignar(db_session, entrenador.id, socio.id)
    borrador = _crear_borrador(db_session, socio.id, estado="aprobado")
    token_e = identidad_service.create_access_token(usuario_e)

    response = client.patch(
        f"/asistente/borradores/{borrador.id}",
        json={"contenido": {"nombre": "Rutina IA editada", "ejercicios": EJERCICIOS}},
        headers={"Authorization": f"Bearer {token_e}"},
    )
    assert response.status_code == 409


def test_socio_no_puede_ver_borradores_pendientes(client, db_session, sede_id):
    usuario, _socio = _crear_socio(db_session, sede_id)
    token = identidad_service.create_access_token(usuario)

    response = client.get("/asistente/borradores-pendientes", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_ollama_client_chat_devuelve_none_si_no_hay_conexion(monkeypatch):
    def _post_falla(*args, **kwargs):
        raise httpx.ConnectError("no se pudo conectar")

    monkeypatch.setattr(httpx, "post", _post_falla)
    assert generar_respuesta_chat([], "Hola") is None


def test_ollama_client_borrador_devuelve_none_si_respuesta_no_es_json(monkeypatch):
    class _RespuestaFalsa:
        def raise_for_status(self):
            return None

        def json(self):
            return {"response": "esto no es json"}

    monkeypatch.setattr(httpx, "post", lambda *a, **k: _RespuestaFalsa())
    assert generar_contenido_borrador("rutina", 30, {"objetivo_principal": "ganar_masa_muscular"}, None) is None
