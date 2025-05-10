# software-team-builder# software-team-builder/app/main.py

import os
import sys
import logging
from typing import Optional

import pandas as pd
from fastapi import FastAPI, Depends, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))

# --- Añadir la raíz del proyecto a sys.path para importar Config ---
PROJECT_ROOT_FOR_CONFIG_IMPORT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT_FOR_CONFIG_IMPORT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_FOR_CONFIG_IMPORT)

try:
    from config import Config # Desde la raíz del proyecto
    # Importaciones relativas para módulos DENTRO del paquete app/
    from .recommendation_engine import SoftwareTeamRecommender # Desde app/recommendation_engine.py
    # from .services.history_manager import FileHistoryManager # Ejemplo si lo tuvieras
    from .routers import teams as teams_router_module # Desde app/routers/teams.py
    from .auth.router import router as auth_router_obj # Desde app/auth/router.py
    # No importamos get_recommendation_engine desde aquí para evitar ciclos.
except ImportError as e:
    print(f"ERROR CRÍTICO AL IMPORTAR MÓDULOS EN MAIN.PY: {e}")
    print(f"  PROJECT_ROOT_FOR_CONFIG_IMPORT: {PROJECT_ROOT_FOR_CONFIG_IMPORT}")
    print(f"  Current sys.path: {sys.path}")
    sys.exit(f"Error crítico de importación: {e}. Revisa la estructura y los __init__.py.")

# --- Configuración de Logging ---
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format='%(levelname)-8s %(asctime)s [%(module)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__) # Logger para este módulo

PROJECT_ROOT_PATH = PROJECT_ROOT_FOR_CONFIG_IMPORT

# --- Evento de Inicio de FastAPI (Startup) ---
# Definido como corutina (async def)
async def startup_event_handler():
    """Inicializa servicios y los guarda en app.state al iniciar FastAPI."""
    logger.info("FastAPI startup event: Initializing services and storing in app.state...")

    data_file_path = os.path.join(PROJECT_ROOT_PATH, Config.DATA_SUBDIR, Config.EMPLOYEE_DATA_FILE_NAME)
    # history_file_path = os.path.join(PROJECT_ROOT_PATH, Config.DATA_SUBDIR, Config.HISTORY_FILE_NAME)

    local_engine_instance: Optional[SoftwareTeamRecommender] = None
    # local_history_manager: Optional[FileHistoryManager] = None

    try:
        logger.info(f"Loading employee data from: {data_file_path}")
        df_employees = pd.read_csv(data_file_path, delimiter=';')

        if df_employees.empty:
            logger.error(f"Employee data file {data_file_path} is empty. Recommendation engine will not be initialized.")
        else:
            logger.info(f"Successfully loaded {len(df_employees)} rows from {Config.EMPLOYEE_DATA_FILE_NAME}.")
            local_engine_instance = SoftwareTeamRecommender(df_employees)
            logger.info("SoftwareTeamRecommender initialized.")

        # Inicializar HistoryManager si se usa
        # local_history_manager = FileHistoryManager(history_file_path)
        # logger.info("FileHistoryManager initialized (if used).")

    except FileNotFoundError:
        logger.error(f"CRITICAL: Data file not found at {data_file_path}. Recommendation engine will be unavailable.")
    except pd.errors.EmptyDataError:
        logger.error(f"CRITICAL: Data file at {data_file_path} is empty. Recommendation engine will be unavailable.")
    except Exception as e:
        logger.exception(f"CRITICAL ERROR during service initialization in startup_event: {e}")
    finally:
        # --- Almacena en app.state ---
        # Accedemos a la instancia 'app' definida más abajo en este módulo
        # Esto es seguro porque el event handler se registra después de crear 'app'
        app.state.recommendation_engine = local_engine_instance
        # app.state.history_manager = local_history_manager # Si usas historial

        if local_engine_instance:
            logger.info("Recommendation engine instance stored in app.state.")
        else:
            logger.warning("Recommendation engine instance is None (due to error or empty data); stored None in app.state.")

    logger.info("FastAPI startup event completed.")

async def shutdown_event_handler():
    """Limpia recursos al cerrar FastAPI."""
    logger.info("FastAPI shutdown event: Cleaning up resources...")
    # Limpiar explícitamente app.state puede ser útil
    if hasattr(app.state, 'recommendation_engine'):
        logger.debug("Clearing recommendation_engine from app.state")
        app.state.recommendation_engine = None
    # if hasattr(app.state, 'history_manager'):
    #     logger.debug("Clearing history_manager from app.state")
    #     app.state.history_manager = None
    logger.info("FastAPI shutdown event completed.")


# --- Crear la Instancia Principal de FastAPI ---
# Definir 'app' ANTES de registrar los event handlers que puedan necesitarla
app = FastAPI(
    title=Config.API_TITLE,
    version=Config.API_VERSION,
    description=Config.API_DESCRIPTION,
    docs_url=Config.API_DOCS_URL,
    redoc_url=Config.API_REDOC_URL
    # Los eventos on_startup/on_shutdown se añaden DESPUÉS usando app.add_event_handler
)

# Registrar los eventos directamente usando el nombre de la función (corutina)
app.add_event_handler("startup", startup_event_handler) # <--- CORRECTO
app.add_event_handler("shutdown", shutdown_event_handler) # <--- CORRECTO

logger.info(f"FastAPI application '{Config.API_TITLE}' v{Config.API_VERSION} created and event handlers registered.")


# --- Configuración de CORS ---
ALLOWED_ORIGINS_STR = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174")
origins = [origin.strip() for origin in ALLOWED_ORIGINS_STR.split(',') if origin.strip()]
if not origins:
    origins = ["http://localhost:5173"] # Fallback mínimo
    logger.warning(f"ALLOWED_ORIGINS environment variable not set or empty, using default: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Permite GET, POST, PUT, DELETE, OPTIONS, etc.
    allow_headers=["*"], # Permite todas las cabeceras estándar y personalizadas.
)
logger.info(f"CORSMiddleware added. Allowed origins: {origins}")


# --- Incluir (Montar) los Routers en la Aplicación Principal ---
try:
    # El router de `teams_router_module` (ej. app/routers/teams.py) debe llamarse `router`
    app.include_router(teams_router_module.router, prefix="/api", tags=["Teams Management"])
    # `auth_router_obj` ya es el objeto router importado desde app/auth/router.py
    app.include_router(auth_router_obj, prefix="/api/auth", tags=["Authentication"])

    # Si tienes un router para el chat en app/routers/chat.py que exporta un 'router':
    # from .routers import chat as chat_router_module
    # app.include_router(chat_router_module.router, prefix="/api/chat", tags=["AI Assistant Chat"])

    logger.info("Routers included successfully.")
except AttributeError as e:
    # Este error ocurre si, por ejemplo, teams_router_module no tiene un atributo 'router'
    logger.exception(f"ERROR CRÍTICO AL INCLUIR ROUTERS: Un módulo de router no tiene un atributo 'router'. Error: {e}")
    sys.exit("Error crítico: Fallo al incluir routers.")
except Exception as e:
    logger.exception(f"ERROR INESPERADO AL INCLUIR ROUTERS: {e}")
    sys.exit("Error crítico inesperado al incluir routers.")


# --- Endpoint Raíz (Opcional) ---
@app.get("/", tags=["Root"], summary="API Status Endpoint")
async def read_root(request: Request): # Necesita `Request` para acceder a `request.app.state`
    """
    Endpoint raíz. Devuelve un mensaje de bienvenida y el estado de la API,
    incluyendo el estado del motor de recomendación.
    """
    logger.debug("GET / root endpoint accessed")
    # Verificar de forma segura si recommendation_engine existe y no es None en app.state
    engine_status = "Not Initialized (app.state missing engine attribute)"
    if hasattr(request.app.state, 'recommendation_engine'):
        engine_status = "Operational" if request.app.state.recommendation_engine else "Not Initialized (app.state engine is None)"

    return {
        "message": f"Welcome to {Config.API_TITLE} v{Config.API_VERSION}",
        "status": "API is running",
        "recommendation_engine_status": engine_status
    }

logger.info(f"FastAPI application setup complete. Target host: {Config.SERVER_HOST}, port: {Config.SERVER_PORT} (when run with uvicorn).")

# --- Punto de entrada para ejecución directa (SOLO para desarrollo local) ---
# (Generalmente no se incluye aquí, se usa el comando uvicorn directamente)
# if __name__ == "__main__":
#     import uvicorn
#     logger.info(f"Starting Uvicorn server directly for development at http://{Config.SERVER_HOST}:{Config.SERVER_PORT}")
#     uvicorn.run(
#         "app.main:app", # Ruta al objeto app de FastAPI
#         host=Config.SERVER_HOST,
#         port=Config.SERVER_PORT,
#         reload=True,
#         reload_dirs=[os.path.join(PROJECT_ROOT_PATH, "app")] # Vigilar cambios en app/
#     )