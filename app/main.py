# app/main.py
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
    from .recommendation_engine import SoftwareTeamRecommender # Desde app/recommendation_engine.py
    from .routers import teams as teams_router_module # Desde app/routers/teams.py
    from .auth.router import router as auth_router_obj # Desde app/auth/router.py
    from .dependencies import get_recommendation_engine # Importante para tus routers
except ImportError as e:
    print(f"ERROR CRÍTICO AL IMPORTAR MÓDULOS EN MAIN.PY: {e}")
    print(f"  PROJECT_ROOT_FOR_CONFIG_IMPORT: {PROJECT_ROOT_FOR_CONFIG_IMPORT}")
    print(f"  Current sys.path: {sys.path}")
    sys.exit(f"Error crítico de importación: {e}. Revisa la estructura y los __init__.py.")

# --- Configuración de Logging ---
LOG_LEVEL_ENV = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL_ENV,
    format='%(levelname)-8s %(asctime)s [%(name)s] [%(module)s:%(lineno)d] %(message)s', # %(name)s ayuda a identificar el logger
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__) # Logger para este módulo (será 'app.main')
logger.info(f"Nivel de logging para la aplicación configurado a: {LOG_LEVEL_ENV}")

PROJECT_ROOT_PATH = PROJECT_ROOT_FOR_CONFIG_IMPORT

async def startup_event_handler():
    logger.info(">>> INICIO FastAPI startup_event_handler: Intentando inicializar servicios...")
    data_file_path = os.path.join(PROJECT_ROOT_PATH, Config.DATA_SUBDIR, Config.EMPLOYEE_DATA_FILE_NAME)
    local_engine_instance: Optional[SoftwareTeamRecommender] = None
    df_employees = pd.DataFrame() # Inicializar como DataFrame vacío

    try:
        logger.info(f"Intentando cargar datos de empleados desde: {data_file_path}")
        if not os.path.exists(data_file_path):
            logger.error(f"CRITICAL: Archivo de datos NO ENCONTRADO en {data_file_path}. El motor se inicializará sin datos.")
            # df_employees ya es un DataFrame vacío
        else:
            df_employees = pd.read_csv(data_file_path, delimiter=';')
            if df_employees.empty:
                logger.warning(f"Archivo de datos {data_file_path} encontrado pero está VACÍO. El motor se inicializará con un DataFrame vacío.")
            else:
                logger.info(f"Datos de empleados cargados exitosamente desde {Config.EMPLOYEE_DATA_FILE_NAME} ({len(df_employees)} filas).")

        # Intentar inicializar el motor incluso si df_employees está vacío.
        # El constructor de SoftwareTeamRecommender debe ser capaz de manejar un DataFrame vacío.
        logger.info("Intentando crear instancia de SoftwareTeamRecommender...")
        local_engine_instance = SoftwareTeamRecommender(df_employees) # Pasa df_employees (podría estar vacío)
        logger.info("Instancia de SoftwareTeamRecommender creada (podría estar con datos vacíos).")

    except FileNotFoundError: # Aunque ya se verifica con os.path.exists, es una buena práctica tenerlo
        logger.error(f"CRITICAL (FileNotFoundError en try catch): Archivo de datos no encontrado en {data_file_path}.")
    except pd.errors.EmptyDataError: # Si read_csv falla porque el archivo no tiene datos ni cabeceras
        logger.error(f"CRITICAL (pd.errors.EmptyDataError en try catch): El archivo de datos en {data_file_path} está esencialmente vacío o malformado.")
    except Exception as e:
        logger.exception(f"CRITICAL ERROR INESPERADO durante la carga de datos o inicialización del motor en startup_event: {e}")
    finally:
        # Almacenar en app.state
        app.state.recommendation_engine = local_engine_instance # Puede ser None si la inicialización falló gravemente antes

        if local_engine_instance is not None:
            if hasattr(local_engine_instance, 'df_employees') and not local_engine_instance.df_employees.empty:
                logger.info(">>> SoftwareTeamRecommender inicializado y almacenado en app.state CON DATOS.")
            else:
                logger.warning(">>> SoftwareTeamRecommender inicializado pero CON DATAFRAME DE EMPLEADOS VACÍO. Almacenado en app.state.")
        else:
            logger.error(">>> SoftwareTeamRecommender NO PUDO ser instanciado (local_engine_instance es None). app.state.recommendation_engine es None.")

    logger.info(">>> FIN FastAPI startup_event_handler.")


# --- Crear la Instancia Principal de FastAPI ---
app = FastAPI(
    title=Config.API_TITLE,
    version=Config.API_VERSION,
    description=Config.API_DESCRIPTION,
    docs_url=Config.API_DOCS_URL,
    redoc_url=Config.API_REDOC_URL
)

app.add_event_handler("startup", startup_event_handler)
# app.add_event_handler("shutdown", shutdown_event_handler) # Si tienes un shutdown_event_handler definido

# Endpoint para el health check de Render
@app.get("/healthz", tags=["Health Check"])
def health_check():
    return {"status": "ok"}

logger.info(f"FastAPI application '{Config.API_TITLE}' v{Config.API_VERSION} creada y event handlers básicos registrados.")


# --- Configuración de CORS ---
FRONTEND_URL_RENDER = "https://team-builder-front.onrender.com"
# Permite URLs separadas por comas desde la variable de entorno, además de la de Render
ADDITIONAL_ALLOWED_ORIGINS_STR = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
additional_origins_list = [origin.strip() for origin in ADDITIONAL_ALLOWED_ORIGINS_STR.split(',') if origin.strip()]
origins = list(set([FRONTEND_URL_RENDER] + additional_origins_list)) # Usar set para evitar duplicados

if not origins: # Fallback si todo lo demás está vacío (poco probable con FRONTEND_URL_RENDER)
    origins = [FRONTEND_URL_RENDER]
    logger.warning(f"Lista de orígenes para CORS estaba vacía, usando fallback: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info(f"CORSMiddleware añadido. Orígenes permitidos: {origins}")


# --- Incluir (Montar) los Routers en la Aplicación Principal ---
try:
    app.include_router(teams_router_module.router, prefix="/api", tags=["Teams Management"])
    app.include_router(auth_router_obj, prefix="/api/auth", tags=["Authentication"])
    logger.info("Routers incluidos exitosamente.")
except AttributeError as e:
    logger.exception(f"ERROR CRÍTICO AL INCLUIR ROUTERS: Un módulo de router no tiene un atributo 'router' o el objeto importado es incorrecto. Error: {e}")
    sys.exit("Error crítico: Fallo al incluir routers.")
except Exception as e:
    logger.exception(f"ERROR INESPERADO AL INCLUIR ROUTERS: {e}")
    sys.exit("Error crítico inesperado al incluir routers.")


# --- Endpoint Raíz (Opcional) ---
@app.get("/", tags=["Root"], summary="API Status Endpoint")
async def read_root(request: Request): # Necesita `Request` para acceder a `request.app.state`
    logger.debug("GET / root endpoint accessed")
    engine_status_message = "No disponible (app.state no tiene el atributo 'recommendation_engine')"
    if hasattr(request.app.state, 'recommendation_engine'):
        engine_instance = request.app.state.recommendation_engine
        if engine_instance is not None:
            # Verifica si el motor tiene el DataFrame y si no está vacío
            if hasattr(engine_instance, 'df_employees') and not engine_instance.df_employees.empty:
                engine_status_message = f"Operacional (con {len(engine_instance.df_employees)} empleados)"
            else:
                engine_status_message = "Inicializado pero con DataFrame de empleados vacío"
        else:
            engine_status_message = "No inicializado (el motor es None en app.state)"

    return {
        "message": f"Bienvenido a {Config.API_TITLE} v{Config.API_VERSION}",
        "status": "API está corriendo",
        "recommendation_engine_status": engine_status_message,
        "current_log_level": LOG_LEVEL_ENV
    }

logger.info(f"Configuración completa de la aplicación FastAPI. Lista para recibir solicitudes en el host y puerto definidos por el servidor (ej. Gunicorn/Uvicorn).")