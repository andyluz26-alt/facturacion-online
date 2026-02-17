from fastapi import FastAPI, Depends, Request, HTTPException, BackgroundTasks, UploadFile, File, Form, Cookie, Response
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from passlib.context import CryptContext 
import os, smtplib, shutil
import pandas as pd
from email.message import EmailMessage
from datetime import datetime, date, timedelta

from . import models, schemas, database, pdf_generator

app = FastAPI()

# --- SEGURIDAD ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Crear carpetas necesarias
for d in ["pdfs", "static/uploads"]:
    if not os.path.exists(d): os.makedirs(d)

app.mount("/descargas", StaticFiles(directory="pdfs"), name="descargas")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
models.Base.metadata.create_all(bind=database.engine)

EMAIL_REMITENTE = "andy.luz26@gmail.com"
EMAIL_PASSWORD = "udfg lkmy xibw gqrw"

def enviar_email_async(dest, num, ruta):
    try:
        msg = EmailMessage()
        msg['Subject'] = f"Factura {num}"; msg['From'] = EMAIL_REMITENTE; msg['To'] = dest
        msg.set_content("Adjuntamos su comprobante electrónico."); 
        with open(ruta, 'rb') as f:
            msg.add_attachment(f.read(), maintype='application', subtype='pdf', filename=os.path.basename(ruta))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(EMAIL_REMITENTE, EMAIL_PASSWORD); s.send_message(msg)
    except Exception as e: print(f"Error Email: {e}")

# --- RUTAS DE AUTENTICACIÓN ---
@app.get("/login-page", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(response: Response, username: str = Form(...), password: str = Form(...), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user and username == "admin":
        hashed_pw = pwd_context.hash(str(password))
        user = models.User(username="admin", hashed_password=hashed_pw)
        db.add(user); db.commit(); db.refresh(user)
    
    try:
        es_valido = user and pwd_context.verify(str(password), user.hashed_password)
    except Exception: es_valido = False
    
    if not es_valido:
        return HTMLResponse(content="<h2>Usuario o clave incorrecta</h2><a href='/login-page'>Volver</a>", status_code=401)
    
    res = RedirectResponse(url="/", status_code=303)
    res.set_cookie(key="user_id", value=str(user.id), httponly=True)
    return res

@app.get("/logout")
async def logout():
    res = RedirectResponse(url="/login-page")
    res.delete_cookie("user_id")
    return res

# --- INVENTARIO ---
@app.get("/api/productos")
def listar_productos(db: Session = Depends(database.get_db), user_id: str = Cookie(None)):
    if not user_id: raise HTTPException(status_code=401)
    return db.query(models.Producto).all()

@app.post("/productos/")
def crear_producto(nombre: str = Form(...), precio: float = Form(...), stock: int = Form(0), db: Session = Depends(database.get_db), user_id: str = Cookie(None)):
    if not user_id: raise HTTPException(status_code=401)
    nuevo = models.Producto(nombre=nombre, precio_con_iva=precio, stock=stock)
    db.add(nuevo); db.commit()
    return {"status": "ok"}

@app.post("/productos/editar/{prod_id}")
def editar_producto(prod_id: int, nombre: str = Form(...), precio: float = Form(...), stock: int = Form(0), db: Session = Depends(database.get_db), user_id: str = Cookie(None)):
    if not user_id: raise HTTPException(status_code=401)
    prod = db.query(models.Producto).filter(models.Producto.id == prod_id).first()
    if prod:
        prod.nombre, prod.precio_con_iva, prod.stock = nombre, precio, stock
        db.commit()
    return {"status": "ok"}

@app.delete("/productos/{prod_id}")
def eliminar_producto(prod_id: int, db: Session = Depends(database.get_db), user_id: str = Cookie(None)):
    if not user_id: raise HTTPException(status_code=401)
    prod = db.query(models.Producto).filter(models.Producto.id == prod_id).first()
    if prod:
        db.delete(prod); db.commit()
    return {"status": "ok"}

# --- CLIENTES ---
@app.get("/api/clientes/{ruc}")
def obtener_cliente(ruc: str, db: Session = Depends(database.get_db), user_id: str = Cookie(None)):
    if not user_id: raise HTTPException(status_code=401)
    return db.query(models.Cliente).filter(models.Cliente.ruc == ruc).first()

# --- FACTURACIÓN Y REPORTES ---
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(database.get_db), user_id: str = Cookie(None)):
    if not user_id: return RedirectResponse(url="/login-page", status_code=303)
    empresa = db.query(models.Empresa).first()
    if not empresa:
        empresa = models.Empresa(); db.add(empresa); db.commit()
    return templates.TemplateResponse("index.html", {"request": request, "empresa": empresa})

@app.get("/stats/")
def get_stats(db: Session = Depends(database.get_db), user_id: str = Cookie(None)):
    if not user_id: raise HTTPException(status_code=401)
    hoy = date.today()
    ventas = db.query(func.sum(models.Factura.total)).filter(
        func.date(models.Factura.fecha) == hoy, models.Factura.anulada == False
    ).scalar() or 0
    iva = db.query(func.sum(models.Factura.iva)).filter(
        func.date(models.Factura.fecha) == hoy, models.Factura.anulada == False
    ).scalar() or 0
    return {"ventas_hoy": round(ventas, 2), "iva_hoy": round(iva, 2)}

@app.get("/api/stats-grafico")
def stats_grafico(db: Session = Depends(database.get_db), user_id: str = Cookie(None)):
    if not user_id: raise HTTPException(status_code=401)
    hoy = date.today()
    datos = []
    for i in range(6, -1, -1):
        dia = hoy - timedelta(days=i)
        total = db.query(func.sum(models.Factura.total)).filter(
            func.date(models.Factura.fecha) == dia, models.Factura.anulada == False
        ).scalar() or 0
        datos.append({"fecha": dia.strftime("%d/%m"), "total": float(total)})
    return datos

@app.get("/buscar/")
def buscar(termino: str = "", desde: str = "", hasta: str = "", db: Session = Depends(database.get_db), user_id: str = Cookie(None)):
    if not user_id: raise HTTPException(status_code=401)
    query = db.query(models.Factura)
    if termino:
        query = query.filter(or_(models.Factura.cliente.ilike(f"%{termino}%"), models.Factura.ruc.ilike(f"%{termino}%"), models.Factura.numero_factura.ilike(f"%{termino}%")))
    if desde and hasta:
        query = query.filter(models.Factura.fecha.between(desde, hasta + " 23:59:59"))
    return query.order_by(models.Factura.id.desc()).all()

@app.get("/exportar-excel/")
def exportar_excel(termino: str = "", desde: str = "", hasta: str = "", db: Session = Depends(database.get_db), user_id: str = Cookie(None)):
    if not user_id: raise HTTPException(status_code=401)
    query = db.query(models.Factura)
    if termino:
        query = query.filter(or_(models.Factura.cliente.ilike(f"%{termino}%"), models.Factura.ruc.ilike(f"%{termino}%"), models.Factura.numero_factura.ilike(f"%{termino}%")))
    if desde and hasta:
        query = query.filter(models.Factura.fecha.between(desde, hasta + " 23:59:59"))
    
    facturas = query.all()
    df_data = [{"Fecha": f.fecha.strftime("%d/%m/%Y"), "Factura": f.numero_factura, "Cliente": f.cliente, "RUC": f.ruc, "Total": f.total, "Estado": "ANULADA" if f.anulada else "ACTIVA"} for f in facturas]
    
    df = pd.DataFrame(df_data)
    ruta = "static/reporte_ventas.xlsx"
    df.to_excel(ruta, index=False)
    return FileResponse(ruta, filename=f"Reporte_Ventas_{date.today()}.xlsx")

@app.post("/emitir-factura/")
def emitir(f_in: schemas.FacturaCreate, bg: BackgroundTasks, db: Session = Depends(database.get_db), user_id: str = Cookie(None)):
    if not user_id: raise HTTPException(status_code=401)
    
    # Registro automático de cliente
    cliente_db = db.query(models.Cliente).filter(models.Cliente.ruc == f_in.ruc).first()
    if not cliente_db:
        nuevo_cliente = models.Cliente(nombre=f_in.cliente, ruc=f_in.ruc, correo=str(f_in.correo_cliente), direccion=f_in.direccion_cliente, telefono=f_in.telefono_cliente)
        db.add(nuevo_cliente)

    num_fact = f"001-001-{db.query(models.Factura).count() + 1:09d}"
    nueva = models.Factura(cliente=f_in.cliente, ruc=f_in.ruc, correo_cliente=str(f_in.correo_cliente), direccion_cliente=f_in.direccion_cliente, telefono_cliente=f_in.telefono_cliente, numero_factura=num_fact, subtotal=0, iva=0, total=0, anulada=False)
    db.add(nueva); db.commit()
    
    total_acum = 0
    for i in f_in.items:
        # Descuento de Stock
        prod = db.query(models.Producto).filter(models.Producto.nombre == i.descripcion).first()
        if prod: prod.stock -= i.cantidad
            
        db.add(models.DetalleFactura(factura_id=nueva.id, descripcion=i.descripcion, cantidad=i.cantidad, precio_con_iva=i.precio_con_iva))
        total_acum += (i.cantidad * i.precio_con_iva)
    
    sub = total_acum / 1.15
    nueva.subtotal, nueva.iva, nueva.total = round(sub, 2), round(total_acum - sub, 2), round(total_acum, 2)
    db.commit()
    
    emp = db.query(models.Empresa).first()
    ruta = pdf_generator.generar_pdf_profesional(nueva, emp)
    bg.add_task(enviar_email_async, str(f_in.correo_cliente), num_fact, ruta)
    return {"status": "ok"}

@app.post("/anular-factura/{fact_id}")
def anular_factura(fact_id: int, db: Session = Depends(database.get_db), user_id: str = Cookie(None)):
    if not user_id: raise HTTPException(status_code=401)
    fact = db.query(models.Factura).filter(models.Factura.id == fact_id).first()
    if fact:
        for item in fact.items:
            p = db.query(models.Producto).filter(models.Producto.nombre == item.descripcion).first()
            if p: p.stock += item.cantidad
        fact.anulada = True
        db.commit()
        emp = db.query(models.Empresa).first()
        pdf_generator.generar_pdf_profesional(fact, emp)
    return {"status": "ok"}

@app.post("/config-empresa/")
async def config_empresa(nombre: str = Form(...), ruc: str = Form(...), direccion: str = Form(...), telefono: str = Form(...), logo: UploadFile = File(None), db: Session = Depends(database.get_db), user_id: str = Cookie(None)):
    if not user_id: raise HTTPException(status_code=401)
    emp = db.query(models.Empresa).first()
    emp.nombre, emp.ruc, emp.direccion, emp.telefono = nombre, ruc, direccion, telefono
    if logo:
        path = f"static/uploads/{logo.filename}"
        with open(path, "wb") as b: shutil.copyfileobj(logo.file, b)
        emp.logo_path = path
    db.commit()
    return {"status": "ok"}