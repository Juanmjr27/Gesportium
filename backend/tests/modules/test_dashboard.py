from datetime import date, datetime, time

from app.modules.clases.models import Clase, Reserva
from app.modules.crm.models import Lead
from app.modules.entrenadores.models import Entrenador
from app.modules.identidad import service as identidad_service
from app.modules.membresias import service as membresias_service
from app.modules.membresias.models import PlanMembresia
from app.modules.pagos import service as pagos_service
from app.modules.sedes.models import Sede
from app.modules.socios import service as socios_service
from app.modules.socios.schemas import SocioCreate


def _token_admin(db_session):
    admin = identidad_service.crear_usuario(db_session, "admin-dash@test.com", "password123", "admin", None)
    return identidad_service.create_access_token(admin)


def _token_gestor(db_session, sede_id, email="gestor-dash@test.com"):
    gestor = identidad_service.crear_usuario(db_session, email, "password123", "gestor_sede", sede_id)
    return identidad_service.create_access_token(gestor)


def _crear_socio_completo(db_session, sede_id, email="socio-dash@test.com") -> tuple:
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


def _crear_entrenador(db_session, sede_id, email="entrenador-dash@test.com") -> Entrenador:
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


def test_admin_ve_socios_activos_y_altas_del_mes(client, db_session, sede_id):
    _crear_socio_completo(db_session, sede_id)

    token = _token_admin(db_session)
    response = client.get(f"/dashboard/kpis?sede_id={sede_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["socios_activos"]["valor"] == 1
    assert body["altas_mes"]["valor"] == 1


def test_ingresos_del_mes_suma_solo_pagos_exitosos(client, db_session, sede_id):
    usuario, socio = _crear_socio_completo(db_session, sede_id)
    plan = _crear_plan(db_session)
    membresia = membresias_service.crear_membresia(
        db_session, socio_id=socio.id, plan=plan, fecha_inicio=date.today(),
        renovacion_automatica=True, autor_id=usuario.id,
    )
    pago_exitoso = pagos_service.generar_cobro_pendiente(db_session, membresia, plan)
    pagos_service.intentar_cobro(db_session, pago_exitoso, exitoso=True)

    token = _token_admin(db_session)
    response = client.get(f"/dashboard/kpis?sede_id={sede_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.json()["ingresos_mes"]["valor"] == 29.99


def test_ocupacion_media_de_clases_del_mes(client, db_session, sede_id):
    _, socio = _crear_socio_completo(db_session, sede_id)
    entrenador = _crear_entrenador(db_session, sede_id)
    clase = _crear_clase(db_session, sede_id, entrenador.id, aforo_maximo=10)
    db_session.add(Reserva(clase_id=clase.id, socio_id=socio.id, estado="confirmada"))
    db_session.commit()

    token = _token_admin(db_session)
    response = client.get(f"/dashboard/kpis?sede_id={sede_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.json()["ocupacion_media_clases"]["valor"] == 10.0


def test_tasa_conversion_leads_del_mes(client, db_session, sede_id):
    db_session.add(Lead(nombre="A", email="a@test.com", telefono="600", sede_interes_id=sede_id, origen="web", estado="convertido"))
    db_session.add(Lead(nombre="B", email="b@test.com", telefono="600", sede_interes_id=sede_id, origen="web", estado="nuevo"))
    db_session.commit()

    token = _token_admin(db_session)
    response = client.get(f"/dashboard/kpis?sede_id={sede_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.json()["tasa_conversion_leads"]["valor"] == 50.0


def test_gestor_sede_ve_solo_su_sede_por_defecto(client, db_session, sede_id):
    otra_sede = Sede(
        nombre="Otra sede dash", direccion="Otra calle", ciudad="Sevilla", telefono="600999888",
        horario_apertura=time(7, 0), horario_cierre=time(22, 0), aforo_maximo=50,
    )
    db_session.add(otra_sede)
    db_session.commit()
    db_session.refresh(otra_sede)

    _crear_socio_completo(db_session, sede_id, email="socio-sede-a@test.com")
    _crear_socio_completo(db_session, otra_sede.id, email="socio-sede-b@test.com")

    token = _token_gestor(db_session, sede_id)
    response = client.get("/dashboard/kpis", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["socios_activos"]["valor"] == 1
    assert response.json()["sede_id"] == str(sede_id)


def test_gestor_sede_no_puede_consultar_otra_sede(client, db_session, sede_id):
    otra_sede = Sede(
        nombre="Otra sede dash 2", direccion="Otra calle", ciudad="Sevilla", telefono="600999887",
        horario_apertura=time(7, 0), horario_cierre=time(22, 0), aforo_maximo=50,
    )
    db_session.add(otra_sede)
    db_session.commit()
    db_session.refresh(otra_sede)

    token = _token_gestor(db_session, sede_id)
    response = client.get(f"/dashboard/kpis?sede_id={otra_sede.id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_admin_puede_ver_kpis_globales_o_filtrados_por_sede(client, db_session, sede_id):
    _crear_socio_completo(db_session, sede_id)

    token = _token_admin(db_session)
    global_response = client.get("/dashboard/kpis", headers={"Authorization": f"Bearer {token}"})
    filtrado_response = client.get(f"/dashboard/kpis?sede_id={sede_id}", headers={"Authorization": f"Bearer {token}"})

    assert global_response.json()["sede_id"] is None
    assert filtrado_response.json()["sede_id"] == str(sede_id)


def test_socio_no_puede_acceder_al_dashboard(client, db_session, sede_id):
    usuario, _ = _crear_socio_completo(db_session, sede_id)
    token = identidad_service.create_access_token(usuario)

    response = client.get("/dashboard/kpis", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
