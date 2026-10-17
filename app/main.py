from fastapi import FastAPI
from app.database import Base, motor
from app.routes import auth, users

Base.metadata.create_all(bind=motor)

aplicacion = FastAPI(
    title="Sistema de Autenticación con OTP",
    description="Plataforma de inicio de sesion seguro con doble factor",
    version="1.0.0"
)

aplicacion.include_router(auth.enrutador)
aplicacion.include_router(users.enrutador)


@aplicacion.get("/")
def verificar_salud():
    return {"estado": "en linea", "mensaje": "Servicio de autenticacion OTP operativo"}