from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import os
import qrcode

def generar_pdf_profesional(factura, empresa):
    nombre_archivo = f"pdfs/RIDE_{factura.numero_factura}.pdf"
    if not os.path.exists("pdfs"): os.makedirs("pdfs")
        
    doc = SimpleDocTemplate(nombre_archivo, pagesize=letter, leftMargin=40, rightMargin=40, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    
    # Estilos mejorados
    style_label = ParagraphStyle('Label', parent=styles['Normal'], fontSize=8, fontName='Helvetica-Bold')
    style_value = ParagraphStyle('Value', parent=styles['Normal'], fontSize=8, leftIndent=5)
    style_title = ParagraphStyle('Title', parent=styles['Normal'], fontSize=11, fontName='Helvetica-Bold')

    # Marca de Agua
    def add_watermark(canvas, doc):
        if factura.anulada:
            canvas.saveState()
            canvas.setFont('Helvetica-Bold', 70)
            canvas.setFillColor(colors.lightgrey, alpha=0.3)
            canvas.translate(300, 440); canvas.rotate(45)
            canvas.drawCentredString(0, 0, "ANULADA")
            canvas.restoreState()

    # QR
    clave_acceso = f"{factura.fecha.strftime('%d%m%Y')}01{empresa.ruc}1001001{factura.id:09d}123456781"
    qr_path = f"pdfs/qr_{factura.id}.png"
    qr = qrcode.QRCode(box_size=10, border=1)
    qr.add_data(clave_acceso); qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white")
    img_qr.save(qr_path)

    # --- ENCABEZADO (Logo + Info Empresa / Info SRI) ---
    logo = Image(empresa.logo_path, width=1.6*inch, height=0.8*inch) if empresa.logo_path and os.path.exists(empresa.logo_path) else ""
    
    col_izq = [
        [logo],
        [Paragraph(f"<b>{empresa.nombre}</b>", style_title)],
        [Paragraph(f"Matriz: {empresa.direccion}", style_value)],
        [Paragraph(f"Teléfono: {empresa.telefono}", style_value)]
    ]
    
    col_der = [
        [Paragraph(f"R.U.C.: {empresa.ruc}", style_title)],
        [Paragraph("<b>FACTURA</b>", style_title)],
        [Paragraph(f"No. {factura.numero_factura}", style_value)],
        [Image(qr_path, width=1*inch, height=1*inch)],
        [Paragraph(f"<font size=6>{clave_acceso}</font>", style_value)]
    ]

    t_header = Table([[Table(col_izq, colWidths=[3.2*inch]), Table(col_der, colWidths=[3.2*inch])]], colWidths=[3.4*inch, 3.4*inch])
    t_header.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    elements.append(t_header)
    elements.append(Spacer(1, 15))

    # --- SECCIÓN CLIENTE (DISEÑO MEJORADO) ---
    # Ficha con etiquetas en gris y datos a la derecha
    data_cliente = [
        [Paragraph("Razón Social / Nombres:", style_label), Paragraph(factura.cliente, style_value), Paragraph("RUC / CI:", style_label), Paragraph(factura.ruc, style_value)],
        [Paragraph("Fecha Emisión:", style_label), Paragraph(factura.fecha.strftime('%d/%m/%Y'), style_value), Paragraph("Teléfono:", style_label), Paragraph(factura.telefono_cliente or "S/N", style_value)],
        [Paragraph("Dirección:", style_label), Paragraph(factura.direccion_cliente or "S/D", style_value), Paragraph("Email:", style_label), Paragraph(factura.correo_cliente, style_value)]
    ]
    
    t_cliente = Table(data_cliente, colWidths=[1.3*inch, 2.3*inch, 0.8*inch, 2.4*inch])
    t_cliente.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, colors.black),
        ('LINEBELOW', (0,0), (-1, -2), 0.2, colors.lightgrey), # Líneas internas sutiles
        ('BACKGROUND', (0,0), (0,-1), colors.whitesmoke),      # Fondo gris para etiquetas 1
        ('BACKGROUND', (2,0), (2,-1), colors.whitesmoke),      # Fondo gris para etiquetas 2
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_cliente)
    elements.append(Spacer(1, 15))

    # --- TABLA DE ITEMS ---
    data_items = [["Cant.", "Descripción", "P. Unitario", "Total"]]
    for item in factura.items:
        p_u = item.precio_con_iva / 1.15
        data_items.append([
            str(item.cantidad),
            item.descripcion,
            f"{p_u:.2f}",
            f"{(item.cantidad * p_u):.2f}"
        ])
    
    t_items = Table(data_items, colWidths=[0.7*inch, 4.1*inch, 1*inch, 1*inch])
    t_items.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.black),           # Cabecera negra para contraste
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (2,0), (-1,-1), 'RIGHT'),
        ('ALIGN', (0,0), (0,-1), 'CENTER'),
    ]))
    elements.append(t_items)
    elements.append(Spacer(1, 15))

    # --- TOTALES ---
    # Creamos una tabla pequeña para los totales
    resumen_totales = [
        ["SUBTOTAL 15%", f"{factura.subtotal:.2f}"],
        ["IVA 15%", f"{factura.iva:.2f}"],
        ["VALOR TOTAL", f"{factura.total:.2f}"]
    ]
    
    t_tot = Table(resumen_totales, colWidths=[1.2*inch, 0.8*inch])
    t_tot.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
        ('BACKGROUND', (0,2), (0,2), colors.whitesmoke), # Fondo en el "TOTAL"
        ('FONTNAME', (0,2), (-1,2), 'Helvetica-Bold'),
    ]))

    # Tabla contenedora para alinear totales a la derecha
    t_final = Table([[Spacer(1,1), t_tot]], colWidths=[4.8*inch, 2*inch])
    elements.append(t_final)

    doc.build(elements, onFirstPage=add_watermark)
    if os.path.exists(qr_path): os.remove(qr_path)
    return nombre_archivo