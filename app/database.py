import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

URL_BASE_DATOS = "sqlite:///./sql_app.db"

motor = create_engine(
    URL_BASE_DATOS, connect_args={"check_same_thread": False}
)
SesionLocal = sessionmaker(autocommit=False, autoflush=False, bind=motor)

Base = declarative_base()


def obtener_conexion_db():
    db = SesionLocal()
    try:
        yield db
    finally:
        db.close()