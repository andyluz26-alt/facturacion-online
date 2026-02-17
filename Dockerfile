FROM python:3.10-slim

WORKDIR /app

# Instalamos dependencias para PDFs y QR
RUN apt-get update && apt-get install -y \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiamos los archivos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Creamos las carpetas que necesita el programa
RUN mkdir -p pdfs static/uploads

# Exponemos el puerto
EXPOSE 8000

# Comando para arrancar: CARPETA app, ARCHIVO main, OBJETO app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
