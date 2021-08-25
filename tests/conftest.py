import pytest
import os

from app.blueprint import create_app
from app.model import db as _db
from app.app_config import AppConfig


class TestConfig(AppConfig):
    # get rid of pytest warnings
    __test__ = False

    TESTING = True
    DEBUG = True
    ENV = "development"
    SQLALCHEMY_DATABASE_URI = None
    LOGIN_DISABLED = True
    SECRET_KEY = "supersecret"

    def __init__(self, db_connection):
        self.SQLALCHEMY_DATABASE_URI = db_connection


def successful(resp):
    leading = resp.status_code // 100
    return leading == 2 or leading == 3


@pytest.fixture(scope='session')
def app():
    connection = os.getenv('DATABASE_URL')

    if connection is None:
        host = os.getenv('POSTGRES_HOST', 'localhost')
        user = 'runner'
        password = os.getenv('POSTGRES_PASSWORD')
        database = 'test_db'

        connection = f'postgresql+psycopg2://{user}:{password}@{host}/{database}'

    print(f"Using connection URL {connection}")

    try:
        _app = create_app(TestConfig(connection))
    except:
        connection = connection.replace('@postgres/', '@localhost/')
        print(f"OperationalError caught, trying to use connection URL {connection} instead")
        _app = create_app(TestConfig(connection))

    print("app created")

    with _app.app_context():
        yield _app


@pytest.fixture(scope='session')
def testapp(app):
    return app.test_client()


@pytest.fixture(scope='session')
def db(app):
    _db.app = app
    _db.create_all()

    yield _db

    _db.drop_all()


@pytest.fixture(scope='function', autouse=True)
def session(db):
    connection = db.engine.connect()
    transaction = connection.begin()

    options = dict(bind=connection, binds={})
    session_ = db.create_scoped_session(options=options)

    db.session = session_

    yield session_

    transaction.rollback()
    connection.close()
    session_.remove()
