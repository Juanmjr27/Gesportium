import uuid
from datetime import date

import pytest

from app.modules.asistente_ia.models import BorradorIA
from app.modules.entrenadores.models import Entrenador, SocioAsignado
from app.modules.entrenamiento import service as entrenamiento_service
from app.modules.entrenamiento.models import CumplimientoRutina, EjercicioRutina, Rutina
from app.modules.identidad import service as identidad_service
from app.modules.socios.models import Socio

EJERCICIOS = [
    {"nombre": "Sentadilla", "series": 4, "repeticiones": 10, "dia_semana": "lunes", "descanso_segundos": 60},
    {"nombre": "Press banca", "series": 3, "repeticiones": 8, "dia_semana": "miercoles", "descanso_segundos": 90},
]


def _crear_entrenador(db_session, sede_id, email="entrenador-entr@test.com") -> tuple:
    usuario = identidad_service.crear_usuario(db_session, email, "password123", "entrenador", sede_id)
    entrenador = Entrenador(usuario_id=usuario.id, sede_id=sede_id, activo=True)
    db_session.add(entrenador)
    db_session.commit()
    db_session.refresh(entrenador)
    return usuario, entrenador


def _crear_socio(db_session, sede_id, email="socio-entr@test.com") -> tuple:
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


def _asignar(db_session, entrenador_id, socio_id):
    db_session.add(SocioAsignado(entrenador_id=entrenador_id, socio_id=socio_id))
    db_session.commit()


def _crear_borrador(db_session, socio_id, tipo, contenido) -> BorradorIA:
    borrador = BorradorIA(
        socio_id=socio_id, tipo=tipo, datos_cuestionario={"tipo_borrador": tipo}, contenido=contenido, estado="pendiente"
    )
    db_session.add(borrador)
    db_session.commit()
    db_session.refresh(borrador)
    return borrador


def test_entrenador_crea_rutina_para_socio_asignado(client, db_session, sede_id):
    usuario_e, entrenador = _crear_entrenador(db_session, sede_id)
    _usuario_s, socio = _crear_socio(db_session, sede_id)
    _asignar(db_session, entrenador.id, socio.id)
    token = identidad_service.create_access_token(usuario_e)

    response = client.post(
        "/rutinas",
        headers={"Authorization": f"Bearer {token}"},
        json={"socio_id": str(socio.id), "nombre": "Fuerza", "ejercicios": EJERCICIOS},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["origen"] == "manual"
    assert len(body["ejercicios"]) == 2


def test_entrenador_no_puede_crear_rutina_para_socio_no_asignado(client, db_session, sede_id):
    usuario_e, _entrenador = _crear_entrenador(db_session, sede_id)
    _usuario_s, socio = _crear_socio(db_session, sede_id)
    token = identidad_service.create_access_token(usuario_e)

    response = client.post(
        "/rutinas",
        headers={"Authorization": f"Bearer {token}"},
        json={"socio_id": str(socio.id), "nombre": "Fuerza", "ejercicios": EJERCICIOS},
    )
    assert response.status_code == 403


def test_socio_ve_sus_propias_rutinas(client, db_session, sede_id):
    _usuario_e, entrenador = _crear_entrenador(db_session, sede_id)
    usuario_s, socio = _crear_socio(db_session, sede_id)
    _asignar(db_session, entrenador.id, socio.id)
    entrenamiento_service.crear_rutina(db_session, entrenador.id, socio.id, "Fuerza", EJERCICIOS)

    token_s = identidad_service.create_access_token(usuario_s)
    response = client.get(f"/rutinas/{socio.id}", headers={"Authorization": f"Bearer {token_s}"})
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_socio_no_puede_ver_rutinas_ajenas(client, db_session, sede_id):
    _usuario_e, entrenador = _crear_entrenador(db_session, sede_id)
    _usuario_s1, socio1 = _crear_socio(db_session, sede_id, "socio1-entr@test.com")
    usuario_s2, _socio2 = _crear_socio(db_session, sede_id, "socio2-entr@test.com")
    _asignar(db_session, entrenador.id, socio1.id)
    entrenamiento_service.crear_rutina(db_session, entrenador.id, socio1.id, "Fuerza", EJERCICIOS)

    token_s2 = identidad_service.create_access_token(usuario_s2)
    response = client.get(f"/rutinas/{socio1.id}", headers={"Authorization": f"Bearer {token_s2}"})
    assert response.status_code == 403


def test_no_se_puede_editar_rutina_archivada(client, db_session, sede_id):
    usuario_e, entrenador = _crear_entrenador(db_session, sede_id)
    _usuario_s, socio = _crear_socio(db_session, sede_id)
    _asignar(db_session, entrenador.id, socio.id)
    rutina = entrenamiento_service.crear_rutina(db_session, entrenador.id, socio.id, "Fuerza", EJERCICIOS)
    token = identidad_service.create_access_token(usuario_e)

    archivar = client.put(f"/rutinas/{rutina.id}", headers={"Authorization": f"Bearer {token}"}, json={"activa": False})
    assert archivar.status_code == 200
    assert archivar.json()["activa"] is False

    response = client.put(f"/rutinas/{rutina.id}", headers={"Authorization": f"Bearer {token}"}, json={"nombre": "Otro nombre"})
    assert response.status_code == 409


def test_entrenador_crea_plan_nutricional(client, db_session, sede_id):
    usuario_e, entrenador = _crear_entrenador(db_session, sede_id)
    usuario_s, socio = _crear_socio(db_session, sede_id)
    _asignar(db_session, entrenador.id, socio.id)
    token = identidad_service.create_access_token(usuario_e)

    response = client.post(
        "/planes-nutricionales",
        headers={"Authorization": f"Bearer {token}"},
        json={"socio_id": str(socio.id), "nombre": "Definición", "notas": "Comidas cada 3 horas"},
    )
    assert response.status_code == 201
    assert response.json()["notas"] == "Comidas cada 3 horas"

    token_s = identidad_service.create_access_token(usuario_s)
    ver = client.get(f"/planes-nutricionales/{socio.id}", headers={"Authorization": f"Bearer {token_s}"})
    assert ver.status_code == 200
    assert len(ver.json()) == 1


def test_socio_marca_cumplimiento_es_idempotente_por_dia(client, db_session, sede_id):
    _usuario_e, entrenador = _crear_entrenador(db_session, sede_id)
    usuario_s, socio = _crear_socio(db_session, sede_id)
    _asignar(db_session, entrenador.id, socio.id)
    rutina = entrenamiento_service.crear_rutina(db_session, entrenador.id, socio.id, "Fuerza", EJERCICIOS)

    ejercicio = db_session.query(EjercicioRutina).filter(EjercicioRutina.rutina_id == rutina.id).first()
    token_s = identidad_service.create_access_token(usuario_s)

    primera = client.post(
        f"/rutinas/{rutina.id}/completar",
        headers={"Authorization": f"Bearer {token_s}"},
        json={"ejercicio_id": str(ejercicio.id), "fecha": "2026-08-10", "completado": True},
    )
    assert primera.status_code == 201

    segunda = client.post(
        f"/rutinas/{rutina.id}/completar",
        headers={"Authorization": f"Bearer {token_s}"},
        json={"ejercicio_id": str(ejercicio.id), "fecha": "2026-08-10", "completado": False},
    )
    assert segunda.status_code == 201
    assert segunda.json()["id"] == primera.json()["id"]
    assert segunda.json()["completado"] is False

    total = db_session.query(CumplimientoRutina).filter(CumplimientoRutina.ejercicio_id == ejercicio.id).count()
    assert total == 1


def test_socio_no_puede_completar_ejercicio_de_rutina_ajena(client, db_session, sede_id):
    _usuario_e, entrenador = _crear_entrenador(db_session, sede_id)
    _usuario_s1, socio1 = _crear_socio(db_session, sede_id, "socio1b-entr@test.com")
    usuario_s2, _socio2 = _crear_socio(db_session, sede_id, "socio2b-entr@test.com")
    _asignar(db_session, entrenador.id, socio1.id)
    rutina = entrenamiento_service.crear_rutina(db_session, entrenador.id, socio1.id, "Fuerza", EJERCICIOS)

    ejercicio = db_session.query(EjercicioRutina).filter(EjercicioRutina.rutina_id == rutina.id).first()
    token_s2 = identidad_service.create_access_token(usuario_s2)

    response = client.post(
        f"/rutinas/{rutina.id}/completar",
        headers={"Authorization": f"Bearer {token_s2}"},
        json={"ejercicio_id": str(ejercicio.id)},
    )
    assert response.status_code == 403


def test_entrenador_ve_cumplimiento_de_su_rutina(client, db_session, sede_id):
    usuario_e, entrenador = _crear_entrenador(db_session, sede_id)
    _usuario_s, socio = _crear_socio(db_session, sede_id)
    _asignar(db_session, entrenador.id, socio.id)
    rutina = entrenamiento_service.crear_rutina(db_session, entrenador.id, socio.id, "Fuerza", EJERCICIOS)

    ejercicio = db_session.query(EjercicioRutina).filter(EjercicioRutina.rutina_id == rutina.id).first()
    entrenamiento_service.marcar_cumplimiento(db_session, ejercicio.id, socio.id, date.today(), True)

    token_e = identidad_service.create_access_token(usuario_e)
    response = client.get(f"/rutinas/{rutina.id}/cumplimiento", headers={"Authorization": f"Bearer {token_e}"})
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_crear_rutina_desde_borrador_valido(db_session, sede_id):
    _, entrenador = _crear_entrenador(db_session, sede_id)
    _, socio = _crear_socio(db_session, sede_id)
    contenido = {"nombre": "Rutina IA", "ejercicios": EJERCICIOS}
    borrador = _crear_borrador(db_session, socio.id, "rutina", contenido)

    rutina = entrenamiento_service.crear_rutina_desde_borrador(db_session, entrenador.id, socio.id, borrador.id, contenido)

    assert rutina.origen == "ia"
    assert rutina.borrador_id == borrador.id
    assert db_session.query(Rutina).filter(Rutina.id == rutina.id).count() == 1


def test_crear_rutina_desde_borrador_con_contenido_invalido_lanza_error(db_session, sede_id):
    _, entrenador = _crear_entrenador(db_session, sede_id)
    _, socio = _crear_socio(db_session, sede_id)

    contenido = {"nombre": "Rutina IA"}  # falta "ejercicios"
    with pytest.raises(ValueError):
        entrenamiento_service.crear_rutina_desde_borrador(db_session, entrenador.id, socio.id, uuid.uuid4(), contenido)


def test_crear_rutina_desde_borrador_con_dias_acentuados(db_session, sede_id):
    _, entrenador = _crear_entrenador(db_session, sede_id)
    _, socio = _crear_socio(db_session, sede_id)
    ejercicios_acentuados = [
        {"nombre": "Sentadilla", "series": 4, "repeticiones": 10, "dia_semana": "miércoles", "descanso_segundos": 60},
        {"nombre": "Zancadas", "series": 3, "repeticiones": 12, "dia_semana": "Sábado", "descanso_segundos": 45},
    ]
    contenido = {"nombre": "Rutina IA con tildes", "ejercicios": ejercicios_acentuados}
    borrador = _crear_borrador(db_session, socio.id, "rutina", contenido)

    rutina = entrenamiento_service.crear_rutina_desde_borrador(db_session, entrenador.id, socio.id, borrador.id, contenido)

    dias_guardados = {
        e.dia_semana for e in db_session.query(EjercicioRutina).filter(EjercicioRutina.rutina_id == rutina.id)
    }
    assert dias_guardados == {"miercoles", "sabado"}


def test_crear_plan_nutricional_desde_borrador_valido(db_session, sede_id):
    _, entrenador = _crear_entrenador(db_session, sede_id)
    _, socio = _crear_socio(db_session, sede_id)
    contenido = {"nombre": "Plan IA", "notas": "Bajo en carbohidratos"}
    borrador = _crear_borrador(db_session, socio.id, "nutricion", contenido)

    plan = entrenamiento_service.crear_plan_nutricional_desde_borrador(db_session, entrenador.id, socio.id, borrador.id, contenido)

    assert plan.origen == "ia"
    assert plan.borrador_id == borrador.id


def test_crear_plan_nutricional_desde_borrador_con_contenido_invalido_lanza_error(db_session, sede_id):
    _, entrenador = _crear_entrenador(db_session, sede_id)
    _, socio = _crear_socio(db_session, sede_id)

    contenido = {"notas": "Sin nombre"}  # falta "nombre"
    with pytest.raises(ValueError):
        entrenamiento_service.crear_plan_nutricional_desde_borrador(db_session, entrenador.id, socio.id, uuid.uuid4(), contenido)
