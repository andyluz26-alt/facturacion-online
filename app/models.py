from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .database import Base
import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_admin = Column(Boolean, default=True)

class Empresa(Base):
    __tablename__ = "empresa"
    id = Column(Integer, primary_key=True)
    nombre = Column(String, default="Mi Negocio")
    ruc = Column(String, default="0000000000001")
    direccion = Column(String, default="Dirección de la Empresa")
    telefono = Column(String, default="0999999999")
    logo_path = Column(String, nullable=True)

# --- NUEVA TABLA: CLIENTES ---
class Cliente(Base):
    __tablename__ = "clientes"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String)
    ruc = Column(String, unique=True, index=True)
    correo = Column(String)
    direccion = Column(String)
    telefono = Column(String)

class Producto(Base):
    __tablename__ = "productos"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    precio_con_iva = Column(Float)
    stock = Column(Integer, default=0)

class Factura(Base):
    __tablename__ = "facturas"
    id = Column(Integer, primary_key=True, index=True)
    numero_factura = Column(String, unique=True)
    cliente = Column(String)
    ruc = Column(String)
    correo_cliente = Column(String)
    direccion_cliente = Column(String)
    telefono_cliente = Column(String)
    subtotal = Column(Float)
    iva = Column(Float)
    total = Column(Float)
    fecha = Column(DateTime, default=datetime.datetime.now)
    anulada = Column(Boolean, default=False) 
    
    items = relationship("DetalleFactura", back_populates="factura", cascade="all, delete-orphan")

class DetalleFactura(Base):
    __tablename__ = "detalles_factura"
    id = Column(Integer, primary_key=True, index=True)
    factura_id = Column(Integer, ForeignKey("facturas.id"))
    descripcion = Column(String)
    cantidad = Column(Float)
    precio_con_iva = Column(Float)
    factura = relationship("Factura", back_populates="items")