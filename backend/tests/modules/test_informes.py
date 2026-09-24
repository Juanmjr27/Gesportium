from datetime import date, datetime, time

import httpx
import pytest

from app.modules.clases.models import Clase, Reserva
from app.modules.crm.models import Lead
from app.modules.entrenadores.models import Entrenador
from app.modules.identidad import service as identidad_service
from app.modules.informes import ollama_client
from app.modules.informes import router as informes_router
from app.modules.membresias import service as membresias_service
from app.modules.membresias.models import PlanMembresia
from app.modules.pagos import service as pagos_service
from app.modules.sedes.models import Sede
from app.modules.socios import service as socios_service
from app.modules.socios.schemas import SocioCreate

pytestmark = pytest.mark.integration


def _token_admin(db_session):
    admin = identidad_service.crear_usuario(db_session, "admin-inf@test.com", "password123", "admin", None)
    return identidad_service.create_access_token(admin)


def _token_gestor(db_session, sede_id, email="gestor-inf@test.com"):
    gestor = identidad_service.crear_usuario(db_session, email, "password123", "gestor_sede", sede_id)
    return identidad_service.create_access_token(gestor)


def _crear_socio_completo(db_session, sede_id, email="socio-inf@test.com") -> tuple:
    usuario = identidad_service.crear_usuario(db_session, email, "password123", "socio", sede_id)
    socio = socios_service.crear_socio(
        db_session,
        SocioCreate(
            usuario_id=usuario.id,
            sede_id=sede_id,
            fecha_nacimiento=date(1990, 1, 1),
            telefono="600111222",
            direccion="Calle Falsa 1",
            contacto_emergencia_nombre="Familiar",
            contacto_emergencia_telefono="600333444",
        ),
        autor_id=usuario.id,
    )
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


def _crear_entrenador(db_session, sede_id, email="entrenador-inf@test.com") -> Entrenador:
    usuario = identidad_service.crear_usuario(db_session, email, "password123", "entrenador", sede_id)
    entrenador = Entrenador(usuario_id=usuario.id, sede_id=sede_id, activo=True)
    db_session.add(entrenador)
    db_session.commit()
    db_session.refresh(entrenador)
    return entrenador


def _crear_clase(db_session, sede_id, entrenador_id, aforo_maximo=10) -> Clase:
    clase = Clase(
        sede_id=sede_id, entrenador_id=entrenador_id, nombre="Yoga", tipo="yoga",
        fecha_hora=datetime.combine(date.today(), time(10, 0)), duracion_minutos=60,
        aforo_maximo=aforo_maximo, recurrente=False, regla_recurrencia=None, estado="activa",
    )
    db_session.add(clase)
    db_session.commit()
    db_session.refresh(clase)
    return clase


def _rango_mes_actual() -> tuple[str, str]:
    hoy = date.today()
    return hoy.replace(day=1).isoformat(), hoy.isoformat()


def test_informe_socios_admin(client, db_session, sede_id):
    _crear_socio_completo(db_session, sede_id)
    inicio, fin = _rango_mes_actual()

    token = _token_admin(db_session)
    response = client.get(
        f"/informes/socios?fecha_inicio={inicio}&fecha_fin={fin}&sede_id={sede_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total_altas"] == 1
    assert body["total_bajas"] == 0
    assert body["socios_activos_al_cierre"] == 1
    assert len(body["detalle"]) == 1
    assert body["detalle"][0]["email"] == "socio-inf@test.com"


def test_informe_financiero_separa_ingresos_e_impagos(client, db_session, sede_id):
    usuario, socio = _crear_socio_completo(db_session, sede_id)
    plan = _crear_plan(db_session)
    membresia = membresias_service.crear_membresia(
        db_session, socio_id=socio.id, plan=plan, fecha_inicio=date.today(),
        renovacion_automatica=True, autor_id=usuario.id,
    )
    pago_ok = pagos_service.generar_cobro_pendiente(db_session, membresia, plan)
    pagos_service.intentar_cobro(db_session, pago_ok, exitoso=True)

    _, socio2 = _crear_socio_completo(db_session, sede_id, email="socio-inf-2@test.com")
    membresia2 = membresias_service.crear_membresia(
        db_session, socio_id=socio2.id, plan=plan, fecha_inicio=date.today(),
        renovacion_automatica=True, autor_id=usuario.id,
    )
    pago_ko = pagos_service.generar_cobro_pendiente(db_session, membresia2, plan)
    for _ in range(3):
        pagos_service.intentar_cobro(db_session, pago_ko, exitoso=False)

    inicio, fin = _rango_mes_actual()
    token = _token_admin(db_session)
    response = client.get(
        f"/informes/financiero?fecha_inicio={inicio}&fecha_fin={fin}&sede_id={sede_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total_ingresos"] == 29.99
    assert body["total_impagos"] == 29.99
    assert len(body["detalle"]) == 2


def test_informe_ocupacion(client, db_session, sede_id):
    _, socio = _crear_socio_completo(db_session, sede_id)
    entrenador = _crear_entrenador(db_session, sede_id)
    clase = _crear_clase(db_session, sede_id, entrenador.id, aforo_maximo=10)
    db_session.add(Reserva(clase_id=clase.id, socio_id=socio.id, estado="confirmada"))
    db_session.commit()

    inicio, fin = _rango_mes_actual()
    token = _token_admin(db_session)
    response = client.get(f"/informes/ocupacion?fecha_inicio={inicio}&fecha_fin={fin}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["ocupacion_media_pct"] == 10.0
    assert body["detalle"][0]["nombre"] == "Yoga"


def test_informe_comercial(client, db_session, sede_id):
    db_session.add(Lead(nombre="A", email="a@test.com", telefono="600", sede_interes_id=sede_id, origen="web", estado="convertido"))
    db_session.add(Lead(nombre="B", email="b@test.com", telefono="600", sede_interes_id=sede_id, origen="web", estado="nuevo"))
    db_session.commit()

    inicio, fin = _rango_mes_actual()
    token = _token_admin(db_session)
    response = client.get(f"/informes/comercial?fecha_inicio={inicio}&fecha_fin={fin}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["total_leads"] == 2
    assert body["convertidos"] == 1
    assert body["tasa_conversion_pct"] == 50.0


def test_tipo_de_informe_desconocido_devuelve_404(client, db_session, sede_id):
    inicio, fin = _rango_mes_actual()
    token = _token_admin(db_session)
    response = client.get(f"/informes/inexistente?fecha_inicio={inicio}&fecha_fin={fin}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404


def test_rango_de_fechas_invalido_devuelve_400(client, db_session, sede_id):
    token = _token_admin(db_session)
    response = client.get(
        "/informes/socios?fecha_inicio=2026-02-01&fecha_fin=2026-01-01", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400


def test_gestor_sede_ve_solo_su_sede_por_defecto(client, db_session, sede_id):
    otra_sede = Sede(
        nombre="Otra sede inf", direccion="Otra calle", ciudad="Sevilla", telefono="600999888",
        horario_apertura=time(7, 0), horario_cierre=time(22, 0), aforo_maximo=50,
    )
    db_session.add(otra_sede)
    db_session.commit()
    db_session.refresh(otra_sede)

    _crear_socio_completo(db_session, sede_id, email="socio-a-inf@test.com")
    _crear_socio_completo(db_session, otra_sede.id, email="socio-b-inf@test.com")

    inicio, fin = _rango_mes_actual()
    token = _token_gestor(db_session, sede_id)
    response = client.get(f"/informes/socios?fecha_inicio={inicio}&fecha_fin={fin}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["total_altas"] == 1
    assert response.json()["sede_id"] == str(sede_id)


def test_gestor_sede_no_puede_consultar_otra_sede(client, db_session, sede_id):
    otra_sede = Sede(
        nombre="Otra sede inf 2", direccion="Otra calle", ciudad="Sevilla", telefono="600999887",
        horario_apertura=time(7, 0), horario_cierre=time(22, 0), aforo_maximo=50,
    )
    db_session.add(otra_sede)
    db_session.commit()
    db_session.refresh(otra_sede)

    inicio, fin = _rango_mes_actual()
    token = _token_gestor(db_session, sede_id)
    response = client.get(
        f"/informes/socios?fecha_inicio={inicio}&fecha_fin={fin}&sede_id={otra_sede.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_socio_no_puede_acceder_a_informes(client, db_session, sede_id):
    usuario, _ = _crear_socio_completo(db_session, sede_id)
    token = identidad_service.create_access_token(usuario)

    inicio, fin = _rango_mes_actual()
    response = client.get(f"/informes/socios?fecha_inicio={inicio}&fecha_fin={fin}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_exportar_informe_pdf(client, db_session, sede_id):
    _crear_socio_completo(db_session, sede_id)
    inicio, fin = _rango_mes_actual()
    token = _token_admin(db_session)

    response = client.get(
        f"/informes/socios/exportar?formato=pdf&fecha_inicio={inicio}&fecha_fin={fin}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


def test_exportar_informe_excel(client, db_session, sede_id):
    _crear_socio_completo(db_session, sede_id)
    inicio, fin = _rango_mes_actual()
    token = _token_admin(db_session)

    response = client.get(
        f"/informes/socios/exportar?formato=excel&fecha_inicio={inicio}&fecha_fin={fin}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.content.startswith(b"PK")


def test_resumen_ia_incluye_texto_generado(client, db_session, sede_id, monkeypatch):
    _crear_socio_completo(db_session, sede_id)
    monkeypatch.setattr(informes_router, "generar_resumen", lambda tipo, datos: "Resumen de prueba generado por IA.")

    inicio, fin = _rango_mes_actual()
    token = _token_admin(db_session)
    response = client.post(
        f"/informes/socios/resumen-ia?fecha_inicio={inicio}&fecha_fin={fin}&sede_id={sede_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["resumen_ia"] == "Resumen de prueba generado por IA."
    assert body["total_altas"] == 1


def test_resumen_ia_si_ollama_no_disponible_informe_se_genera_igual(client, db_session, sede_id, monkeypatch):
    _crear_socio_completo(db_session, sede_id)
    monkeypatch.setattr(informes_router, "generar_resumen", lambda tipo, datos: None)

    inicio, fin = _rango_mes_actual()
    token = _token_admin(db_session)
    response = client.post(
        f"/informes/socios/resumen-ia?fecha_inicio={inicio}&fecha_fin={fin}&sede_id={sede_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["resumen_ia"] is None
    assert body["total_altas"] == 1


def test_ollama_client_devuelve_none_si_no_hay_conexion(monkeypatch):
    def _post_falla(*args, **kwargs):
        raise httpx.ConnectError("no se pudo conectar")

    monkeypatch.setattr(httpx, "post", _post_falla)

    datos = {
        "fecha_inicio": date(2026, 1, 1), "fecha_fin": date(2026, 1, 31),
        "total_altas": 1, "total_bajas": 0, "socios_activos_al_cierre": 1,
    }
    assert ollama_client.generar_resumen("socios", datos) is None


def test_resumen_ia_conexion_real_con_ollama(client, db_session, sede_id):
    """Prueba de integración real contra el Ollama local (spec.md: IA local,
    modelo llama3.2:latest). Si el servicio no está arrancado en este
    entorno, se omite (criterio de aceptación: el informe debe poder
    generarse igualmente sin Ollama, ya cubierto por los tests mockeados).
    """
    _crear_socio_completo(db_session, sede_id)
    inicio, fin = _rango_mes_actual()
    token = _token_admin(db_session)

    response = client.post(
        f"/informes/socios/resumen-ia?fecha_inicio={inicio}&fecha_fin={fin}", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    body = response.json()
    if body["resumen_ia"] is None:
        pytest.skip("Ollama no está disponible en este entorno")
    assert isinstance(body["resumen_ia"], str)
    assert len(body["resumen_ia"]) > 0
