web: gunicorn --worker-class eventlet -w 1 app.index:app --log-file -
release: FLASK_APP=app.index:app flask db upgrade