# backend/Dockerfile

# app/Dockerfile

# 1. Imagen base
FROM python:3.10-slim-bookworm

# 2. Establecer directorio de trabajo DENTRO del contenedor
WORKDIR /app

# 3. Copiar archivos de configuración y dependencias PRIMERO
# Copia desde la raíz del contexto de build (definido en docker-compose.yml como '.')
COPY requirements.txt .
COPY config.py .

# 4. Instalar dependencias de Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 5. Copiar el CÓDIGO FUENTE y otros directorios
# Copia el CONTENIDO de la carpeta './app' del host (donde está este Dockerfile, main.py, etc.)
# al WORKDIR (/app) del contenedor.
# Resultado: /app/main.py, /app/routers/, /app/auth/, etc.
# ¡Importante! Asegúrate que .dockerignore excluya app/Dockerfile para este paso.
COPY ./app .

# Copia las carpetas de datos y modelos desde la raíz del contexto
COPY ./data ./data
COPY ./models ./models

# 6. Exponer el puerto
EXPOSE 8000

# 7. Comando para ejecutar la aplicación
# WORKDIR es /app. main.py está en /app/main.py (porque copiamos el contenido de ./app a .)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]