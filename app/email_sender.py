import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def enviar_por_email(destinatario, archivo_path):
    # CONFIGURACIÓN (Aquí usarás tu correo de empresa)
    remitente = "tu_correo@gmail.com"
    password = "tu_contraseña_de_aplicacion" # No es tu clave normal

    msg = MIMEMultipart()
    msg['From'] = remitente
    msg['To'] = destinatario
    msg['Subject'] = "Tu Factura Digital está lista"

    cuerpo = "Estimado cliente, adjuntamos su factura electrónica en formato PDF."
    msg.attach(MIMEText(cuerpo, 'plain'))

    # Adjuntar PDF
    with open(archivo_path, "rb") as adjunto:
        parte = MIMEBase('application', 'octet-stream')
        parte.set_payload(adjunto.read())
        encoders.encode_base64(parte)
        parte.add_header('Content-Disposition', f"attachment; filename= {archivo_path}")
        msg.attach(parte)

    # Envío real
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remitente, password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error enviando correo: {e}")
        return False