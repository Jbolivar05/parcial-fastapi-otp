# Sistema de Autenticación con OTP - FastAPI

Sistema de autenticación con SQLite, SQLAlchemy y códigos OTP por correo.

## Instalación

python -m pip install -r requirements.txt

## Ejecución

python -m uvicorn app.main:app --reload

Swagger UI: http://127.0.0.1:8000/docs

## Pruebas

python -m pytest tests/