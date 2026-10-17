import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

HOST_CORREO = os.getenv("SERVIDOR_SMTP", "smtp.gmail.com")
PUERTO_CORREO = int(os.getenv("PUERTO_SMTP", 587))
CUENTA_REMITENTE = os.getenv("USUARIO_SMTP", "")
CONTRASENA_CORREO = os.getenv("PASSWORD_SMTP", "")
DIRECCION_ORIGEN = os.getenv("CORREO_REMITENTE", "")


def despachar_correo_otp(cuenta_destino: str, codigo_generado: str):
    if not CUENTA_REMITENTE or not CONTRASENA_CORREO:
        return True

    correo = MIMEMultipart()
    correo["From"] = DIRECCION_ORIGEN
    correo["To"] = cuenta_destino
    correo["Subject"] = "Tu clave de acceso OTP"

    cuerpo_texto = f"Tu codigo temporal de acceso es: {codigo_generado}. Tienes 15 minutos para utilizarlo."
    correo.attach(MIMEText(cuerpo_texto, "plain"))

    try:
        conexion_smtp = smtplib.SMTP(HOST_CORREO, PUERTO_CORREO)
        conexion_smtp.starttls()
        conexion_smtp.login(CUENTA_REMITENTE, CONTRASENA_CORREO)
        conexion_smtp.sendmail(DIRECCION_ORIGEN, cuenta_destino, correo.as_string())
        conexion_smtp.quit()
        return True
    except Exception:
        return False