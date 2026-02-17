import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# --- CONFIGURACIÓN PARA LA NUBE ---
# Buscamos la ruta absoluta de la carpeta donde está este archivo (app/)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Definimos que la base de datos se guarde un nivel arriba (en la raíz del proyecto)
# y la llamaremos 'facturacion.db' para que coincida con tus otros archivos
db_path = os.path.join(BASE_DIR, "..", "facturacion.db")

# Usamos la ruta absoluta (Esto evita errores de "Database not found" en Render)
SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"
# ----------------------------------

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()