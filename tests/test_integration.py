import pytest
from fastapi.testclient import TestClient
from app.database import Base, SesionLocal, motor
from app.main import aplicacion
from app.models import ClaveOTP, Usuario

cliente_servidor = TestClient(aplicacion)


@pytest.fixture(autouse=True)
def base_de_datos_limpia():
    Base.metadata.create_all(bind=motor)
    yield
    Base.metadata.drop_all(bind=motor)


def test_flujo_creacion_cuenta_e_ingreso():
    registro = cliente_servidor.post("/auth/register", json={
        "email": "estudiante@ejemplo.lat",
        "password": "PasswordLatino123",
        "full_name": "Estudiante Parcial"
    })
    assert registro.status_code == 201

    ingreso = cliente_servidor.post("/auth/login", json={
        "email": "estudiante@ejemplo.lat",
        "password": "PasswordLatino123"
    })
    assert ingreso.status_code == 200


def test_validacion_otp_y_consulta_perfil():
    cliente_servidor.post("/auth/register", json={
        "email": "verificar@ejemplo.lat",
        "password": "PasswordLatino123",
        "full_name": "Usuario Verificado"
    })
    cliente_servidor.post("/auth/login", json={
        "email": "verificar@ejemplo.lat",
        "password": "PasswordLatino123"
    })

    db = SesionLocal()
    cuenta = db.query(Usuario).filter(Usuario.email == "verificar@ejemplo.lat").first()
    registro_otp = db.query(ClaveOTP).filter(ClaveOTP.user_id == cuenta.id).first()
    codigo_verificacion = registro_otp.code
    db.close()

    confirmacion = cliente_servidor.post("/auth/verify-otp", json={
        "email": "verificar@ejemplo.lat",
        "code": codigo_verificacion
    })
    assert confirmacion.status_code == 200
    credencial = confirmacion.json()["access_token"]

    perfil = cliente_servidor.get("/users/profile", headers={"Authorization": f"Bearer {credencial}"})
    assert perfil.status_code == 200
    assert perfil.json()["email"] == "verificar@ejemplo.lat"


def test_bloqueo_acceso_tras_cerrar_sesion():
    cliente_servidor.post("/auth/register", json={
        "email": "salida@ejemplo.lat",
        "password": "PasswordLatino123",
        "full_name": "Usuario Salida"
    })
    cliente_servidor.post("/auth/login", json={
        "email": "salida@ejemplo.lat",
        "password": "PasswordLatino123"
    })

    db = SesionLocal()
    cuenta = db.query(Usuario).filter(Usuario.email == "salida@ejemplo.lat").first()
    registro_otp = db.query(ClaveOTP).filter(ClaveOTP.user_id == cuenta.id).first()
    codigo_verificacion = registro_otp.code
    db.close()

    credencial = cliente_servidor.post("/auth/verify-otp", json={
        "email": "salida@ejemplo.lat",
        "code": codigo_verificacion
    }).json()["access_token"]

    peticion_salida = cliente_servidor.post("/auth/logout", headers={"Authorization": f"Bearer {credencial}"})
    assert peticion_salida.status_code == 200

    consulta_posterior = cliente_servidor.get("/users/profile", headers={"Authorization": f"Bearer {credencial}"})
    assert consulta_posterior.status_code == 401