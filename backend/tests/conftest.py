import os
from datetime import time
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import get_db
from app.main import app
from app.modules.sedes.models import Sede

BACKEND_DIR = Path(__file__).resolve().parent.parent


def _test_database_url() -> str:
    """BD de test, separada de la de desarrollo (DATABASE_URL) para que pytest
    nunca vea filas comprometidas por el servidor real corriendo en paralelo
    (verificaciones manuales/Playwright contra localhost:8000) ni al revés.
    Antes ambos apuntaban a la misma BD y eso hacía la suite no determinista
    según qué se hubiera probado a mano (ver specs/018)."""
    if settings.test_database_url:
        return settings.test_database_url
    prefix, _, dbname = settings.database_url.rpartition("/")
    return f"{prefix}/{dbname}_test"


def _ensure_database_exists(database_url: str) -> None:
    prefix, _, dbname = database_url.rpartition("/")
    admin_engine = create_engine(f"{prefix}/postgres", isolation_level="AUTOCOMMIT")
    try:
        with admin_engine.connect() as conn:
            exists = conn.execute(text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": dbname}).first()
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{dbname}"'))
    finally:
        admin_engine.dispose()


def _upgrade_to_head(database_url: str) -> None:
    """Corre las migraciones reales (alembic upgrade head) contra la BD de
    test, en vez de Base.metadata.create_all(), para que los datos sembrados
    por migraciones (p. ej. configuracion_global en deb0740ca027) también
    existan en test — create_all solo crea el esquema, no ejecuta los
    op.bulk_insert()/op.execute() de las migraciones de datos."""
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    previous = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = database_url
    try:
        command.upgrade(cfg, "head")
    finally:
        if previous is not None:
            os.environ["DATABASE_URL"] = previous
        else:
            os.environ.pop("DATABASE_URL", None)


_test_db_url = _test_database_url()
_ensure_database_exists(_test_db_url)
_upgrade_to_head(_test_db_url)
test_engine = create_engine(_test_db_url)


@pytest.fixture()
def db_session():
    connection = test_engine.connect()
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
