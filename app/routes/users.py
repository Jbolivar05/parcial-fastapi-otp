from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import obtener_conexion_db
from app.middleware import encriptar_contrasena, identificar_usuario_logueado
from app.models import Usuario
from app.schemas import RespuestaDatosUsuario, SolicitudModificarUsuario

enrutador = APIRouter(prefix="/users", tags=["Usuarios"])


@enrutador.get("/profile", response_model=RespuestaDatosUsuario)
def consultar_mi_perfil(usuario_conectado: Usuario = Depends(identificar_usuario_logueado)):
    return usuario_conectado


@enrutador.put("/profile", response_model=RespuestaDatosUsuario)
def editar_mi_perfil(
    datos_actualizados: SolicitudModificarUsuario,
    usuario_conectado: Usuario = Depends(identificar_usuario_logueado),
    db: Session = Depends(obtener_conexion_db)
):
    if datos_actualizados.full_name is not None:
        usuario_conectado.full_name = datos_actualizados.full_name

    if datos_actualizados.password is not None:
        usuario_conectado.password_hash = encriptar_contrasena(datos_actualizados.password)

    db.commit()
    db.refresh(usuario_conectado)
    return usuario_conectado