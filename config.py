import os

basedir = os.path.abspath(os.path.dirname(__file__))

# Your App secret key
SECRET_KEY = os.urandom(64)

# The SQLAlchemy connection string.
SQLALCHEMY_DATABASE_URI = "sqlite:///" + basedir + "shorty.db"
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Celery
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
CELERY_ACCEPT_CONTENT = "pickle,json"

# Flask-WTF flag for CSRF
CSRF_ENABLED = True

# App name
APP_NAME = "Shorty, a URL Shortener"

# Flask Mail
MAIL_USERNAME = ""
MAIL_PASSWORD = ""
MAIL_DEFAULT_SENDER = ""


