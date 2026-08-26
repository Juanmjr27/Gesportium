from app.modules.crm.models import InteraccionLead, Lead
from app.modules.identidad import service as identidad_service
from app.modules.identidad.models import Usuario
from app.modules.socios.models import Socio


def _token_admin(db_session):
    admin = identidad_service.crear_usuario(db_session, "admin-crm@test.com", "password123", "admin", None)
    return identidad_service.create_access_token(admin)


def _token_gestor(db_session, sede_id, email="gestor-crm@test.com"):
    gestor = identidad_service.crear_usuario(db_session, email, "password123", "gestor_sede", sede_id)
    return identidad_service.create_access_token(gestor)


def _crear_comercial(db_session, sede_id, email="comercial-crm@test.com") -> Usuario:
    return identidad_service.crear_usuario(db_session, email, "password123", "comercial", sede_id)


def _crear_lead(db_session, sede_id, email="lead@test.com", comercial_id=None, estado="nuevo") -> Lead:
    lead = Lead(
        nombre="Lead Test",
        email=email,
        telefono="600555666",
        sede_interes_id=sede_id,
        origen="web",
        estado=estado,
        comercial_id=comercial_id,
    )
    db_session.add(lead)
    db_session.commit()
    db_session.refresh(lead)
    return lead


def test_alta_lead_publica_sin_autenticacion(client, sede_id):
    response = client.post(
        "/leads",
        json={
            "nombre": "Nuevo Lead",
            "email": "nuevolead@test.com",
            "telefono": "600111222",
            "sede_interes_id": str(sede_id),
            "origen": "web",
        },
    )
    assert response.status_code == 201
    assert response.json()["estado"] == "nuevo"


def test_gestor_asigna_lead_a_comercial(client, db_session, sede_id):
    comercial = _crear_comercial(db_session, sede_id)
    lead = _crear_lead(db_session, sede_id)

    token = _token_gestor(db_session, sede_id)
    response = client.put(
        f"/leads/{lead.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"comercial_id": str(comercial.id)},
    )
    assert response.status_code == 200
    assert response.json()["comercial_id"] == str(comercial.id)


def test_comercial_no_puede_reasignar_lead(client, db_session, sede_id):
    comercial = _crear_comercial(db_session, sede_id)
    otro_comercial = _crear_comercial(db_session, sede_id, email="otro-comercial-crm@test.com")
    lead = _crear_lead(db_session, sede_id, comercial_id=comercial.id)

    token = identidad_service.create_access_token(comercial)
    response = client.put(
        f"/leads/{lead.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"comercial_id": str(otro_comercial.id)},
    )
    assert response.status_code == 403


def test_comercial_ve_solo_sus_leads_asignados(client, db_session, sede_id):
    comercial = _crear_comercial(db_session, sede_id)
    _crear_lead(db_session, sede_id, email="lead-propio@test.com", comercial_id=comercial.id)
    _crear_lead(db_session, sede_id, email="lead-ajeno@test.com")

    token = identidad_service.create_access_token(comercial)
    response = client.get("/leads", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["email"] == "lead-propio@test.com"


def test_gestor_ve_leads_de_su_sede(client, db_session, sede_id):
    _crear_lead(db_session, sede_id, email="lead-sede@test.com")

    token = _token_gestor(db_session, sede_id)
    response = client.get("/leads", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_comercial_registra_interaccion(client, db_session, sede_id):
    comercial = _crear_comercial(db_session, sede_id)
    lead = _crear_lead(db_session, sede_id, comercial_id=comercial.id)

    token = identidad_service.create_access_token(comercial)
    response = client.post(
        f"/leads/{lead.id}/interacciones",
        headers={"Authorization": f"Bearer {token}"},
        json={"tipo": "llamada", "notas": "Primer contacto telefónico"},
    )
    assert response.status_code == 201
    assert response.json()["tipo"] == "llamada"

    interaccion = db_session.query(InteraccionLead).filter(InteraccionLead.lead_id == lead.id).first()
    assert interaccion is not None
    assert interaccion.autor_id == comercial.id


def test_comercial_no_asignado_no_puede_registrar_interaccion(client, db_session, sede_id):
    comercial = _crear_comercial(db_session, sede_id)
    lead = _crear_lead(db_session, sede_id)

    token = identidad_service.create_access_token(comercial)
    response = client.post(
        f"/leads/{lead.id}/interacciones",
        headers={"Authorization": f"Bearer {token}"},
        json={"tipo": "llamada", "notas": "No debería poder"},
    )
    assert response.status_code == 403


def test_lead_descartado_puede_reabrirse(client, db_session, sede_id):
    lead = _crear_lead(db_session, sede_id, estado="descartado")

    token = _token_admin(db_session)
    response = client.put(
        f"/leads/{lead.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"estado": "contactado"},
    )
    assert response.status_code == 200
    assert response.json()["estado"] == "contactado"


def test_convertir_lead_crea_usuario_y_socio(client, db_session, sede_id):
    lead = _crear_lead(db_session, sede_id, email="convertir@test.com")

    token = _token_admin(db_session)
    response = client.post(
        f"/leads/{lead.id}/convertir",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "fecha_nacimiento": "1990-01-01",
            "direccion": "Calle Falsa 1",
            "contacto_emergencia_nombre": "Familiar",
            "contacto_emergencia_telefono": "600333444",
        },
    )
    assert response.status_code == 201

    usuario = db_session.query(Usuario).filter(Usuario.email == "convertir@test.com").first()
    assert usuario is not None
    socio = db_session.query(Socio).filter(Socio.usuario_id == usuario.id).first()
    assert socio is not None

    db_session.refresh(lead)
    assert lead.estado == "convertido"


def test_convertir_lead_no_duplica_usuario_si_email_ya_existe(client, db_session, sede_id):
    usuario_existente = identidad_service.crear_usuario(
        db_session, "yaexiste@test.com", "password123", "socio", sede_id
    )
    lead = _crear_lead(db_session, sede_id, email="yaexiste@test.com")

    token = _token_admin(db_session)
    response = client.post(
        f"/leads/{lead.id}/convertir",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "fecha_nacimiento": "1990-01-01",
            "direccion": "Calle Falsa 1",
            "contacto_emergencia_nombre": "Familiar",
            "contacto_emergencia_telefono": "600333444",
        },
    )
    assert response.status_code == 201

    usuarios_con_ese_email = db_session.query(Usuario).filter(Usuario.email == "yaexiste@test.com").count()
    assert usuarios_con_ese_email == 1
    assert response.json()["usuario_id"] == str(usuario_existente.id)


def test_put_lead_no_puede_marcar_convertido_directamente(client, db_session, sede_id):
    lead = _crear_lead(db_session, sede_id, email="bypass-conversion@test.com")

    token = _token_admin(db_session)
    response = client.put(
        f"/leads/{lead.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"estado": "convertido"},
    )
    assert response.status_code == 422

    db_session.refresh(lead)
    assert lead.estado == "nuevo"

    usuario = db_session.query(Usuario).filter(Usuario.email == "bypass-conversion@test.com").first()
    assert usuario is None


def test_convertir_lead_ya_convertido_es_rechazado(client, db_session, sede_id):
    lead = _crear_lead(db_session, sede_id, email="doble-conversion@test.com", estado="convertido")

    token = _token_admin(db_session)
    response = client.post(
        f"/leads/{lead.id}/convertir",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "fecha_nacimiento": "1990-01-01",
            "direccion": "Calle Falsa 1",
            "contacto_emergencia_nombre": "Familiar",
            "contacto_emergencia_telefono": "600333444",
        },
    )
    assert response.status_code == 409
