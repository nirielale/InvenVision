# InvenVision - imagen para producción (Railway u otro).
# Se construye desde la raíz del repositorio:  docker build -t invenvision .
FROM python:3.11-slim-bookworm

# Tesseract con español e inglés (paquetes de Debian) y la librería que necesita OpenCV.
# El build falla si falta alguno de los dos idiomas.
RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-spa tesseract-ocr-eng libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    && tesseract --list-langs | grep -qx spa \
    && tesseract --list-langs | grep -qx eng

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    ENVIRONMENT=production

WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install -r backend/requirements.txt

# Solo lo necesario para ejecutar: sin .env, pruebas, respaldos, ml/ ni documentos personales
COPY backend/app backend/app
COPY backend/scripts backend/scripts
COPY frontend frontend

# Usuario sin privilegios. UPLOAD_DIR apunta a /data/uploads (monte ahí un volumen persistente)
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /data/uploads \
    && chown -R appuser:appuser /data
USER appuser
ENV UPLOAD_DIR=/data/uploads

# Las credenciales (DB_*, JWT_SECRET...) se definen como variables del servicio, nunca en la imagen.
WORKDIR /app/backend
EXPOSE 8000
# Railway define PORT; en local usa 8000
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
