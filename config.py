# config.py
import os
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv() # Carga variables de .env si existe (principalmente para desarrollo local)

class Config:
    API_TITLE = os.getenv("API_TITLE", "Software Team Builder API (MindFactory)")
    API_VERSION = os.getenv("API_VERSION", "1.2.1")
    API_DESCRIPTION = os.getenv("API_DESCRIPTION", "API para generar equipos técnicos de MindFactory con datos actualizados.")
    API_DOCS_URL = "/docs"
    API_REDOC_URL = "/redoc"

    # Estas variables SERVER_HOST y SERVER_PORT son más relevantes si ejecutas
    # uvicorn app.main:app directamente, no tanto cuando Gunicorn usa --bind 0.0.0.0:$PORT.
    # Asegúrate de que SERVER_PORT no sea 3306 por alguna confusión.
    SERVER_HOST: str = os.getenv("SERVER_HOST", "0.0.0.0") # 0.0.0.0 es mejor para que escuche en todas las interfaces
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000")) # Un puerto como 8000 o 10000 es típico para apps web

    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_USER: str = os.getenv("DB_USER", "default_user")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "default_password")
    DB_NAME: str = os.getenv("DB_NAME", "team_builder_auth")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306")) # Este SÍ es el puerto de la DB

    DATA_SUBDIR: str = "data"
    MODELS_SUBDIR: str = "models"
    EMPLOYEE_DATA_FILE_NAME: str = "users_mindfactory.csv"
    HISTORY_FILE_NAME: str = "recommendation_history.json"

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

    DEFAULT_DEBUG_MODE: bool = os.getenv("RECOMMENDER_DEBUG_MODE", "False").lower() == 'true'
    DEFAULT_STRICT_FILTER_MODE: str = os.getenv("RECOMMENDER_STRICT_FILTER", "principal")
    DEFAULT_MIN_EXP_THRESHOLD: float = float(os.getenv("RECOMMENDER_MIN_EXP", "0.3"))

# (El if __name__ == "__main__": que tenías aquí no es necesario si este archivo solo define la clase Config)