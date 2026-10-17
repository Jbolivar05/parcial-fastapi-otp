import secrets
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import ClaveOTP, Usuario
from app.services.email_service import despachar_correo_otp


def producir_codigo_aleatorio(id_usuario: int, db: Session) -> str:
    codigo_secreto = f"{secrets.randbelow(900000) + 100000}"
    tiempo_limite = datetime.utcnow() + timedelta(minutes=15)

    nuevo_registro_otp = ClaveOTP(
        user_id=id_usuario,
        code=codigo_secreto,
        expires_at=tiempo_limite,
        used=False
    )
    db.add(nuevo_registro_otp)
    db.commit()
    return codigo_secreto


def generar_y_notificar_otp(usuario: Usuario, db: Session) -> bool:
    clave_creada = producir_codigo_aleatorio(usuario.id, db)
    despachar_correo_otp(usuario.email, clave_creada)
    return True


def autenticar_codigo_otp(id_usuario: int, clave_ingresada: str, db: Session) -> bool:
    fecha_actual = datetime.utcnow()
    registro = (
        db.query(ClaveOTP)
        .filter(
            ClaveOTP.user_id == id_usuario,
            ClaveOTP.code == clave_ingresada,
            ClaveOTP.used == False,
            ClaveOTP.expires_at > fecha_actual
        )
        .order_by(ClaveOTP.created_at.desc())
        .first()
    )

    if not registro:
        return False

    registro.used = True
    db.commit()
    return True