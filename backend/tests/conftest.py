from datetime import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, engine, get_db
from app.main import app
from app.modules.sedes.models import Sede

Base.metadata.create_all(bind=engine)


@pytest.fixture()
def db_session():
    connection = engine.connect()
    outer_transaction = connection.begin()
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = TestSessionLocal()
    session.begin_nested()

    # service.py calls session.commit(); intercept it so it only closes the
    # SAVEPOINT, keeping the outer transaction open until rollback below.
    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(sess, transaction):
        if transaction.nested and not transaction._parent.nested:
            sess.begin_nested()

    yield session

    session.close()
    outer_transaction.rollback()
    connection.close()


@pytest.fixture()
def sede_id(db_session):
    sede = Sede(
        nombre="Sede Test",
        direccion="Calle Test 1",
        ciudad="Madrid",
        telefono="600000000",
        horario_apertura=time(7, 0),
        horario_cierre=time(22, 0),
        aforo_maximo=100,
    )
    db_session.add(sede)
    db_session.commit()
    db_session.refresh(sede)
    return sede.id


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
