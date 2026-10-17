from datetime import datetime, timedelta
import pytest
from app.database import Base, SesionLocal, motor
from app.middleware import encriptar_contrasena, validar_contrasena
from app.models import ClaveOTP, Usuario
from app.services.otp_service import autenticar_codigo_otp, producir_codigo_aleatorio


@pytest.fixture
def sesion_prueba():
    Base.metadata.create_all(bind=motor)
    sesion = SesionLocal()
    yield sesion
    sesion.close()
    Base.metadata.drop_all(bind=motor)


def test_encriptacion_correcta():
    contrasena_base = "ClaveLatinoamerica2026"
    resultado_hash = encriptar_contrasena(contrasena_base)
    assert resultado_hash != contrasena_base
    assert validar_contrasena(contrasena_base, resultado_hash) is True
    assert validar_contrasena("ClaveErrada", resultado_hash) is False


def test_creacion_otp_numerico(sesion_prueba):
    usuario_nuevo = Usuario(email="persona1@dominio.lat", password_hash="hash_secreto", full_name="Persona Uno")
    sesion_prueba.add(usuario_nuevo)
    sesion_prueba.commit()

    clave = producir_codigo_aleatorio(usuario_nuevo.id, sesion_prueba)
    assert len(clave) == 6
    assert clave.isdigit()


def test_aprobacion_clave_otp_activa(sesion_prueba):
    usuario_nuevo = Usuario(email="persona2@dominio.lat", password_hash="hash_secreto", full_name="Persona Dos")
    sesion_prueba.add(usuario_nuevo)
    sesion_prueba.commit()

    clave = producir_codigo_aleatorio(usuario_nuevo.id, sesion_prueba)
    assert autenticar_codigo_otp(usuario_nuevo.id, clave, sesion_prueba) is True
    assert autenticar_codigo_otp(usuario_nuevo.id, clave, sesion_prueba) is False


def test_rechazo_clave_otp_caducada(sesion_prueba):
    usuario_nuevo = Usuario(email="persona3@dominio.lat", password_hash="hash_secreto", full_name="Persona Tres")
    sesion_prueba.add(usuario_nuevo)
    sesion_prueba.commit()

    otp_vencido = ClaveOTP(
        user_id=usuario_nuevo.id,
        code="654321",
        expires_at=datetime.utcnow() - timedelta(minutes=2),
        used=False
    )
    sesion_prueba.add(otp_vencido)
    sesion_prueba.commit()

    assert autenticar_codigo_otp(usuario_nuevo.id, "654321", sesion_prueba) is False


def test_rechazo_codigo_invalido(sesion_prueba):
    usuario_nuevo = Usuario(email="persona4@dominio.lat", password_hash="hash_secreto", full_name="Persona Cuatro")
    sesion_prueba.add(usuario_nuevo)
    sesion_prueba.commit()

    producir_codigo_aleatorio(usuario_nuevo.id, sesion_prueba)
    assert autenticar_codigo_otp(usuario_nuevo.id, "000000", sesion_prueba) is False