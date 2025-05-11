# /app/main.py
import os
import sys
import logging
from typing import Optional

import pandas as pd
from fastapi import FastAPI, Depends, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

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
    from .dependencies import get_recommendation_engine # Importante para tus routers
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
async def startup_event_handler():
    logger.info("FastAPI startup event: Initializing services and storing in app.state...")
    data_file_path = os.path.join(PROJECT_ROOT_PATH, Config.DATA_SUBDIR, Config.EMPLOYEE_DATA_FILE_NAME)
    local_engine_instance: Optional[SoftwareTeamRecommender] = None
    try:
        logger.info(f"Loading employee data from: {data_file_path}")
        df_employees = pd.read_csv(data_file_path, delimiter=';')
        if df_employees.empty:
            logger.error(f"Employee data file {data_file_path} is empty. Recommendation engine will not be initialized.")
        else:
            logger.info(f"Successfully loaded {len(df_employees)} rows from {Config.EMPLOYEE_DATA_FILE_NAME}.")
            local_engine_instance = SoftwareTeamRecommender(df_employees) # Asumiendo que df_employees es el único argumento necesario
            logger.info("SoftwareTeamRecommender initialized.")
    except FileNotFoundError:
        logger.error(f"CRITICAL: Data file not found at {data_file_path}. Recommendation engine will be unavailable.")
    except pd.errors.EmptyDataError:
        logger.error(f"CRITICAL: Data file at {data_file_path} is empty. Recommendation engine will be unavailable.")
    except Exception as e:
        logger.exception(f"CRITICAL ERROR during service initialization in startup_event: {e}")
    finally:
        app.state.recommendation_engine = local_engine_instance
        if local_engine_instance:
            logger.info("Recommendation engine instance stored in app.state.")
        else:
            logger.warning("Recommendation engine instance is None; stored None in app.state.")
    logger.info("FastAPI startup event completed.")

async def shutdown_event_handler():
    logger.info("FastAPI shutdown event: Cleaning up resources...")
    if hasattr(app.state, 'recommendation_engine'):
        logger.debug("Clearing recommendation_engine from app.state")
        app.state.recommendation_engine = None
    logger.info("FastAPI shutdown event completed.")

# --- Crear la Instancia Principal de FastAPI ---
app = FastAPI(
    title=Config.API_TITLE,
    version=Config.API_VERSION,
    description=Config.API_DESCRIPTION,
    docs_url=Config.API_DOCS_URL,
    redoc_url=Config.API_REDOC_URL
)

app.add_event_handler("startup", startup_event_handler)
app.add_event_handler("shutdown", shutdown_event_handler)

# Endpoint para el health check de Render
@app.get("/healthz")
def health_check():
    return {"status": "ok"}

logger.info(f"FastAPI application '{Config.API_TITLE}' v{Config.API_VERSION} created and event handlers registered.")


# --- Configuración de CORS ---
# Define los orígenes permitidos directamente o desde variables de entorno
# Asegúrate de que tu URL de frontend de Render esté aquí.
FRONTEND_URL_RENDER = "https://team-builder-front.onrender.com"

# Lee orígenes adicionales de una variable de entorno si existe
ADDITIONAL_ALLOWED_ORIGINS_STR = os.getenv("ALLOWED_ORIGINS", "")
additional_origins_list = [origin.strip() for origin in ADDITIONAL_ALLOWED_ORIGINS_STR.split(',') if origin.strip()]

# Combina la URL de Render con los orígenes adicionales (evitando duplicados)
origins = list(set([FRONTEND_URL_RENDER] + additional_origins_list + [
    "http://localhost:5173", # Para desarrollo local frontend Vite (común)
    "http://127.0.0.1:5173", # Alternativa para localhost
    # "http://localhost:PUERTO_VITE_SI_ES_DIFERENTE", # Añade otros si los usas
]))

if not origins: # Fallback muy básico si todo falla (no debería ocurrir con FRONTEND_URL_RENDER)
    origins = [FRONTEND_URL_RENDER]
    logger.warning(f"No valid origins configured, using default: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True, # Importante para cookies o Authorization headers
    allow_methods=["*"],    # Permite todos los métodos: GET, POST, OPTIONS, PUT, DELETE, etc.
    allow_headers=["*"],    # Permite todas las cabeceras.
)
logger.info(f"CORSMiddleware added. Allowed origins: {origins}")
# --- FIN DE CONFIGURACIÓN DE CORS ---


# --- Incluir (Montar) los Routers en la Aplicación Principal ---
try:
    # teams_router_module es el módulo importado (app/routers/teams.py)
    # Asumimos que dentro de ese módulo hay un objeto APIRouter llamado 'router'
    app.include_router(teams_router_module.router, prefix="/api", tags=["Teams Management"])

    # auth_router_obj ya es la instancia del router importada (desde app/auth/router.py)
    app.include_router(auth_router_obj, prefix="/api/auth", tags=["Authentication"])

    # Ejemplo si tuvieras un router de chat:
    # from .routers import chat as chat_router_module
    # app.include_router(chat_router_module.router, prefix="/api/chat", tags=["AI Assistant Chat"])

    logger.info("Routers included successfully.")
except AttributeError as e:
    logger.exception(f"ERROR CRÍTICO AL INCLUIR ROUTERS: Un módulo de router no tiene un atributo 'router' o el objeto router importado es incorrecto. Error: {e}")
    sys.exit("Error crítico: Fallo al incluir routers.")
except Exception as e:
    logger.exception(f"ERROR INESPERADO AL INCLUIR ROUTERS: {e}")
    sys.exit("Error crítico inesperado al incluir routers.")


# --- Endpoint Raíz (Opcional) ---
@app.get("/", tags=["Root"], summary="API Status Endpoint")
async def read_root(request: Request):
    logger.debug("GET / root endpoint accessed")
    engine_status = "Not Initialized (app.state missing engine attribute)"
    if hasattr(request.app.state, 'recommendation_engine'):
        engine_status = "Operational" if request.app.state.recommendation_engine else "Not Initialized (app.state engine is None)"
    return {
        "message": f"Welcome to {Config.API_TITLE} v{Config.API_VERSION}",
        "status": "API is running",
        "recommendation_engine_status": engine_status
    }

logger.info(f"FastAPI application setup complete. Target host: {Config.SERVER_HOST}, port: {Config.SERVER_PORT} (when run with uvicorn).")

# El bloque if __name__ == "__main__": que tenías al inicio
# para uvicorn.run(app, ...) no es necesario aquí si Render invoca
# uvicorn con el comando de inicio (ej. uvicorn app.main:app --host 0.0.0.0 --port $PORT)
# Si lo mantienes, asegúrate de que la instancia `app` esté definida ANTES de que se llame.
# Lo he movido conceptualmente al final y comentado porque Render se encarga de esto.

# if __name__ == "__main__":
#     import uvicorn
#     # Asegúrate que app esté completamente configurada ANTES de esta línea
#     logger.info(f"Starting Uvicorn server directly for development at http://{Config.SERVER_HOST}:{Config.SERVER_PORT}")
#     uvicorn.run(
#         "app.main:app",
#         host=Config.SERVER_HOST,
#         port=Config.SERVER_PORT,
#         reload=True,
#         reload_dirs=[os.path.join(PROJECT_ROOT_PATH, "app")]
#     )