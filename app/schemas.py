from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr


class SolicitudRegistro(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class SolicitudIngreso(BaseModel):
    email: EmailStr
    password: str


class SolicitudVerificarOTP(BaseModel):
    email: EmailStr
    code: str


class SolicitudReenviarOTP(BaseModel):
    email: EmailStr


class RespuestaDatosUsuario(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    created_at: datetime
    updated_at: datetime


class SolicitudModificarUsuario(BaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = None


class RespuestaTokenAcceso(BaseModel):
    access_token: str
    token_type: str = "bearer"


class NotificacionMensaje(BaseModel):
    mensaje: str