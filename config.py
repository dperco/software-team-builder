# software-team-builder/config.py
import os
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv()

class Config:
    API_TITLE = os.getenv("API_TITLE", "Software Team Builder API (MindFactory)")
    API_VERSION = os.getenv("API_VERSION", "1.2.1") # Incrementada versión
    API_DESCRIPTION = os.getenv("API_DESCRIPTION", "API para generar equipos técnicos de MindFactory con datos actualizados.")
    API_DOCS_URL = "/docs"
    API_REDOC_URL = "/redoc"

    SERVER_HOST: str = os.getenv("SERVER_HOST", "127.0.0.1")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))

    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_USER: str = os.getenv("DB_USER", "default_user")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "default_password")
    DB_NAME: str = os.getenv("DB_NAME", "team_builder_auth")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))

    DATA_SUBDIR: str = "data"
    MODELS_SUBDIR: str = "models"
    EMPLOYEE_DATA_FILE_NAME: str = "users_mindfactory.csv" # <--- Archivo CSV Correcto
    HISTORY_FILE_NAME: str = "recommendation_history.json"

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

    DEFAULT_DEBUG_MODE: bool = os.getenv("RECOMMENDER_DEBUG_MODE", "False").lower() == 'true'
    DEFAULT_STRICT_FILTER_MODE: str = os.getenv("RECOMMENDER_STRICT_FILTER", "principal")
    DEFAULT_MIN_EXP_THRESHOLD: float = float(os.getenv("RECOMMENDER_MIN_EXP", "0.3"))

if __name__ == "__main__":
    print(f"API_TITLE: {Config.API_TITLE}")
    print(f"Employee Data File: {os.path.join(Config.DATA_SUBDIR, Config.EMPLOYEE_DATA_FILE_NAME)}")