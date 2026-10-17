from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import obtener_conexion_db
from app.middleware import (
    DURACION_TOKEN_MINUTOS,
    emitir_credencial_jwt,
    encriptar_contrasena,
    extraer_token_portador,
    identificar_usuario_logueado,
    validar_contrasena,
)
from app.models import SesionUsuario, Usuario
from app.schemas import (
    NotificacionMensaje,
    RespuestaTokenAcceso,
    SolicitudIngreso,
    SolicitudReenviarOTP,
    SolicitudRegistro,
    SolicitudVerificarOTP,
)
from app.services.otp_service import autenticar_codigo_otp, generar_y_notificar_otp

enrutador = APIRouter(prefix="/auth", tags=["Autenticacion"])


@enrutador.post("/register", response_model=NotificacionMensaje, status_code=status.HTTP_201_CREATED)
def registrar_cuenta(datos: SolicitudRegistro, db: Session = Depends(obtener_conexion_db)):
    cuenta_existente = db.query(Usuario).filter(Usuario.email == datos.email).first()
    if cuenta_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una cuenta registrada con este correo"
        )

    nueva_cuenta = Usuario(
        email=datos.email,
        full_name=datos.full_name,
        password_hash=encriptar_contrasena(datos.password)
    )
    db.add(nueva_cuenta)
    db.commit()
    db.refresh(nueva_cuenta)
    return {"mensaje": "Cuenta de usuario creada con exito"}


@enrutador.post("/login", response_model=NotificacionMensaje)
def autenticar_usuario(datos_acceso: SolicitudIngreso, db: Session = Depends(obtener_conexion_db)):
    cuenta = db.query(Usuario).filter(Usuario.email == datos_acceso.email).first()
    if not cuenta or not validar_contrasena(datos_acceso.password, cuenta.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El correo o la contrasena son incorrectos"
        )

    generar_y_notificar_otp(cuenta, db)
    return {"mensaje": "Hemos enviado un codigo de confirmacion a tu correo"}


@enrutador.post("/verify-otp", response_model=RespuestaTokenAcceso)
def confirmar_clave_otp(datos_confirmacion: SolicitudVerificarOTP, db: Session = Depends(obtener_conexion_db)):
    cuenta = db.query(Usuario).filter(Usuario.email == datos_confirmacion.email).first()
    if not cuenta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No encontramos ninguna cuenta con ese correo"
        )

    if not autenticar_codigo_otp(cuenta.id, datos_confirmacion.code, db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El codigo es invalido o ya vencio"
        )

    lapso_expiracion = timedelta(minutes=DURACION_TOKEN_MINUTOS)
    credencial_jwt = emitir_credencial_jwt(datos_usuario={"sub": str(cuenta.id)}, plazo_vigencia=lapso_expiracion)

    sesion_nueva = SesionUsuario(
        user_id=cuenta.id,
        token=credencial_jwt,
        expires_at=datetime.utcnow() + lapso_expiracion
    )
    db.add(sesion_nueva)
    db.commit()

    return {"access_token": credencial_jwt, "token_type": "bearer"}


@enrutador.post("/resend-otp", response_model=NotificacionMensaje)
def solicitar_nuevo_codigo(datos: SolicitudReenviarOTP, db: Session = Depends(obtener_conexion_db)):
    cuenta = db.query(Usuario).filter(Usuario.email == datos.email).first()
    if not cuenta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No encontramos ninguna cuenta con ese correo"
        )

    generar_y_notificar_otp(cuenta, db)
    return {"mensaje": "Te hemos reenviado un nuevo codigo de seguridad"}


@enrutador.post("/refresh", response_model=RespuestaTokenAcceso)
def renovar_credencial_acceso(
    usuario_autenticado: Usuario = Depends(identificar_usuario_logueado),
    token_anterior: str = Depends(extraer_token_portador),
    db: Session = Depends(obtener_conexion_db)
):
    db.query(SesionUsuario).filter(SesionUsuario.token == token_anterior).delete()

    lapso_expiracion = timedelta(minutes=DURACION_TOKEN_MINUTOS)
    token_renovado = emitir_credencial_jwt(datos_usuario={"sub": str(usuario_autenticado.id)}, plazo_vigencia=lapso_expiracion)

    sesion_renovada = SesionUsuario(
        user_id=usuario_autenticado.id,
        token=token_renovado,
        expires_at=datetime.utcnow() + lapso_expiracion
    )
    db.add(sesion_renovada)
    db.commit()

    return {"access_token": token_renovado, "token_type": "bearer"}


@enrutador.post("/logout", response_model=NotificacionMensaje)
def desconectar_usuario(
    usuario_autenticado: Usuario = Depends(identificar_usuario_logueado),
    token_actual: str = Depends(extraer_token_portador),
    db: Session = Depends(obtener_conexion_db)
):
    db.query(SesionUsuario).filter(SesionUsuario.token == token_actual).delete()
    db.commit()
    return {"mensaje": "Has cerrado sesion satisfactoriamente"}