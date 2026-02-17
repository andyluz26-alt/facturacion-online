from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional

class ItemBase(BaseModel):
    descripcion: str
    cantidad: float
    precio_con_iva: float

class FacturaCreate(BaseModel):
    cliente: str
    ruc: str
    correo_cliente: EmailStr
    direccion_cliente: str
    telefono_cliente: str
    items: List[ItemBase]

# --- NUEVOS SCHEMAS PARA PRODUCTOS Y CLIENTES ---

class ProductoBase(BaseModel):
    nombre: str
    precio_con_iva: float
    stock: Optional[int] = 0

class ClienteResponse(BaseModel):
    id: int
    nombre: str
    ruc: str
    correo: str
    direccion: str
    telefono: str
    class Config:
        from_attributes = True

class FacturaResponse(BaseModel):
    id: int
    numero_factura: str
    cliente: str
    total: float
    fecha: datetime
    anulada: bool
    class Config:
        from_attributes = True