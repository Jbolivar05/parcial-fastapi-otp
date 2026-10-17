import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
import bcrypt
from sqlalchemy.orm import Session
from app.database import obtener_conexion_db
from app.models import SesionUsuario, Usuario

load_dotenv()

CLAVE_SECRETA_JWT = os.getenv("CLAVE_SECRETA", "clave_super_secreta_parcial_latam_12345")
ALGORITMO_FIRMA = os.getenv("ALGORITMO", "HS256")
DURACION_TOKEN_MINUTOS = int(os.getenv("MINUTOS_EXPIRACION_TOKEN", 60))

control_portador = HTTPBearer()


def encriptar_contrasena(contrasena_plana: str) -> str:
    bytes_contrasena = contrasena_plana.encode("utf-8")
    sal = bcrypt.gensalt()
    hash_bytes = bcrypt.hashpw(bytes_contrasena, sal)
    return hash_bytes.decode("utf-8")


def validar_contrasena(contrasena_plana: str, contrasena_encriptada: str) -> bool:
    bytes_contrasena = contrasena_plana.encode("utf-8")
    bytes_hash = contrasena_encriptada.encode("utf-8")
    return bcrypt.checkpw(bytes_contrasena, bytes_hash)


def emitir_credencial_jwt(datos_usuario: dict, plazo_vigencia: timedelta = None) -> str:
    contenido = datos_usuario.copy()
    tiempo_vencimiento = datetime.utcnow() + (plazo_vigencia if plazo_vigencia else timedelta(minutes=DURACION_TOKEN_MINUTOS))
    contenido.update({"exp": tiempo_vencimiento})
    return jwt.encode(contenido, CLAVE_SECRETA_JWT, algorithm=ALGORITMO_FIRMA)


def identificar_usuario_logueado(
    credencial: HTTPAuthorizationCredentials = Security(control_portador),
    db: Session = Depends(obtener_conexion_db)
) -> Usuario:
    token_texto = credencial.credentials
    falla_autenticacion = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales invalidas o su sesion ha finalizado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    sesion_encontrada = db.query(SesionUsuario).filter(SesionUsuario.token == token_texto).first()
    if not sesion_encontrada:
        raise falla_autenticacion

    try:
        carga_util = jwt.decode(token_texto, CLAVE_SECRETA_JWT, algorithms=[ALGORITMO_FIRMA])
        identificador = carga_util.get("sub")
        if identificador is None:
            raise falla_autenticacion
    except JWTError:
        raise falla_autenticacion

    persona = db.query(Usuario).filter(Usuario.id == int(identificador)).first()
    if persona is None:
        raise falla_autenticacion

    return persona


def extraer_token_portador(credencial: HTTPAuthorizationCredentials = Security(control_portador)) -> str:
    return credencial.credentials