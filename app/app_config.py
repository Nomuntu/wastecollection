import os


class AppConfig:
    TESTING = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_TYPE = 'sqlalchemy'
    SESSION_USE_SIGNER = True


class ProductionConfig(AppConfig):
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL'].replace("postgres://", "postgresql://",
                                                                 1) if 'DATABASE_URL' in os.environ else None
    SECRET_KEY = os.environ['FLASK_SECRET']
