from app.modules.configuracion.models import ConfiguracionGlobal, HistorialConfiguracion
from app.modules.identidad import service as identidad_service


def _token_admin(db_session):
    admin = identidad_service.crear_usuario(db_session, "admin-config@test.com", "password123", "admin", None)
    return identidad_service.create_access_token(admin), admin


def _token_gestor(db_session, sede_id):
    gestor = identidad_service.crear_usuario(db_session, "gestor-config@test.com", "password123", "gestor_sede", sede_id)
    return identidad_service.create_access_token(gestor)


def _crear_parametro(db_session, clave="parametro_test", valor="valor_inicial", tipo="texto") -> ConfiguracionGlobal:
    config = ConfiguracionGlobal(clave=clave, valor=valor, tipo=tipo)
    db_session.add(config)
    db_session.commit()
    db_session.refresh(config)
    return config


def test_admin_lista_configuracion_incluye_parametros_sembrados(client, db_session):
    token, _ = _token_admin(db_session)
    response = client.get("/configuracion", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    claves = {item["clave"] for item in response.json()}
    assert {"moneda", "zona_horaria", "texto_politica_privacidad", "texto_condiciones"} <= claves


def test_gestor_sede_no_puede_listar_configuracion(client, db_session, sede_id):
    token = _token_gestor(db_session, sede_id)
    response = client.get("/configuracion", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_admin_edita_parametro_de_texto(client, db_session):
    _crear_parametro(db_session, clave="moneda_test", valor="EUR", tipo="texto")
    token, _ = _token_admin(db_session)

    response = client.put(
        "/configuracion/moneda_test", json={"valor": "USD"}, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["valor"] == "USD"


def test_editar_parametro_desconocido_devuelve_404(client, db_session):
    token, _ = _token_admin(db_session)
    response = client.put(
        "/configuracion/no_existe", json={"valor": "x"}, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


def test_editar_parametro_numero_con_valor_invalido_devuelve_400(client, db_session):
    _crear_parametro(db_session, clave="preaviso_dias", valor="7", tipo="numero")
    token, _ = _token_admin(db_session)

    response = client.put(
        "/configuracion/preaviso_dias", json={"valor": "no-es-numero"}, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400


def test_editar_parametro_numero_con_valor_valido(client, db_session):
    _crear_parametro(db_session, clave="preaviso_dias", valor="7", tipo="numero")
    token, _ = _token_admin(db_session)

    response = client.put(
        "/configuracion/preaviso_dias", json={"valor": "14"}, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["valor"] == "14"


def test_editar_parametro_booleano_con_valor_invalido_devuelve_400(client, db_session):
    _crear_parametro(db_session, clave="permite_lista_espera", valor="true", tipo="booleano")
    token, _ = _token_admin(db_session)

    response = client.put(
        "/configuracion/permite_lista_espera",
        json={"valor": "quizas"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400


def test_gestor_sede_no_puede_editar_configuracion(client, db_session, sede_id):
    _crear_parametro(db_session, clave="moneda_test2", valor="EUR", tipo="texto")
    token = _token_gestor(db_session, sede_id)

    response = client.put(
        "/configuracion/moneda_test2", json={"valor": "USD"}, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


def test_editar_configuracion_registra_historial(client, db_session):
    _crear_parametro(db_session, clave="moneda_test3", valor="EUR", tipo="texto")
    token, admin = _token_admin(db_session)

    response = client.put(
        "/configuracion/moneda_test3", json={"valor": "USD"}, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

    historial = (
        db_session.query(HistorialConfiguracion).filter(HistorialConfiguracion.clave == "moneda_test3").one()
    )
    assert historial.valor_anterior == "EUR"
    assert historial.valor_nuevo == "USD"
    assert historial.autor_id == admin.id
