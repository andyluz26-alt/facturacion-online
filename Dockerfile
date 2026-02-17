FROM python:3.10-slim

WORKDIR /app

# Instalamos dependencias del sistema para ReportLab
RUN apt-get update && apt-get install -y \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Creamos las carpetas necesarias
RUN mkdir -p pdfs static/uploads

# Comando para iniciar la app en la nube
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]