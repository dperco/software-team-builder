# app/main.py
import os
import sys
import logging

# --- Configuración de Logging PRIMERO ---
# Esto asegura que los logs iniciales (como el de PORT) se capturen con el formato deseado.
LOG_LEVEL_ENV = os.getenv("LOG_LEVEL", "INFO").upper() # Asegúrate de poner LOG_LEVEL=DEBUG en Render
logging.basicConfig(
    level=LOG_LEVEL_ENV,
    format='%(levelname)-8s %(asctime)s [%(name)s] [%(module)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
# Logger inicial para mensajes ANTES de que se defina la app FastAPI y otros módulos
# Esto es útil para depurar el entorno de inicio.
initial_logger = logging.getLogger("app.initial_setup")

# Loguear el puerto de Render INMEDIATAMENTE
render_port = os.getenv("PORT")
initial_logger.info(f"--- MAIN.PY INICIO --- Variable de entorno PORT de Render: {render_port}")
if not render_port:
    initial_logger.warning("--- MAIN.PY INICIO --- ¡ALERTA! La variable de entorno PORT NO ESTÁ DEFINIDA. Gunicorn no podrá bindear correctamente y la aplicación fallará al iniciar o no será accesible como Render espera.")
else:
    try:
        # Verificar si el puerto es un número válido, aunque Gunicorn lo maneja como string
        int(render_port)
        initial_logger.info(f"--- MAIN.PY INICIO --- Puerto de Render ({render_port}) parece válido.")
    except ValueError:
        initial_logger.error(f"--- MAIN.PY INICIO --- ¡ERROR! El valor de PORT ('{render_port}') no es un número válido.")


# --- Resto de tus imports ---
from typing import Optional
import pandas as pd
from fastapi import FastAPI, Depends, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

# --- Añadir la raíz del proyecto a sys.path para importar Config ---
PROJECT_ROOT_FOR_CONFIG_IMPORT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT_FOR_CONFIG_IMPORT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_FOR_CONFIG_IMPORT)
initial_logger.info(f"Añadido al sys.path para imports: {PROJECT_ROOT_FOR_CONFIG_IMPORT}")

try:
    from config import Config
    from .recommendation_engine import SoftwareTeamRecommender
    from .routers import teams as teams_router_module
    from .auth.router import router as auth_router_obj
    from .dependencies import get_recommendation_engine
    initial_logger.info("Importaciones principales de la aplicación completadas exitosamente.")
except ImportError as e:
    initial_logger.critical(f"ERROR CRÍTICO AL IMPORTAR MÓDULOS EN MAIN.PY: {e}", exc_info=True)
    initial_logger.critical(f"  PROJECT_ROOT_FOR_CONFIG_IMPORT: {PROJECT_ROOT_FOR_CONFIG_IMPORT}")
    initial_logger.critical(f"  Current sys.path: {sys.path}")
    sys.exit(f"Error crítico de importación: {e}. La aplicación no puede continuar.")

# Logger principal para el resto de la aplicación (ahora que los imports están hechos)
logger = logging.getLogger(__name__) # Esto será 'app.main'
logger.info(f"Nivel de logging para el logger '{__name__}' configurado a: {LOG_LEVEL_ENV}")

PROJECT_ROOT_PATH = PROJECT_ROOT_FOR_CONFIG_IMPORT

async def startup_event_handler():
    logger.info(">>> INICIO FastAPI startup_event_handler: Intentando inicializar servicios...")
    data_file_path = os.path.join(PROJECT_ROOT_PATH, Config.DATA_SUBDIR, Config.EMPLOYEE_DATA_FILE_NAME)
    local_engine_instance: Optional[SoftwareTeamRecommender] = None
    df_employees = pd.DataFrame()

    try:
        logger.info(f"Intentando cargar datos de empleados desde: {data_file_path}")
        if not os.path.exists(data_file_path):
            logger.error(f"CRITICAL: Archivo de datos NO ENCONTRADO en {data_file_path}. El motor se inicializará con un DataFrame vacío.")
        else:
            df_employees = pd.read_csv(data_file_path, delimiter=';')
            if df_employees.empty:
                logger.warning(f"Archivo de datos {data_file_path} encontrado pero está VACÍO. El motor se inicializará con un DataFrame vacío.")
            else:
                logger.info(f"Datos de empleados cargados exitosamente desde {Config.EMPLOYEE_DATA_FILE_NAME} ({len(df_employees)} filas).")

        logger.info(f"Intentando crear instancia de SoftwareTeamRecommender con DataFrame de {len(df_employees)} filas.")
        local_engine_instance = SoftwareTeamRecommender(df_employees)
        logger.info("Instancia de SoftwareTeamRecommender creada.")

    except FileNotFoundError:
        logger.error(f"CRITICAL (FileNotFoundError en try catch): Archivo de datos no encontrado en {data_file_path}.")
    except pd.errors.EmptyDataError:
        logger.error(f"CRITICAL (pd.errors.EmptyDataError en try catch): El archivo de datos en {data_file_path} está esencialmente vacío o malformado.")
    except Exception as e:
        logger.exception(f"CRITICAL ERROR INESPERADO durante la carga de datos o inicialización del motor en startup_event.")
    finally:
        app.state.recommendation_engine = local_engine_instance # Puede ser None si hubo excepción ANTES de la asignación
        if local_engine_instance is not None:
            # Chequeo si el df_employees dentro del motor tiene datos
            if hasattr(local_engine_instance, 'df_employees') and not local_engine_instance.df_employees.empty:
                logger.info(">>> SoftwareTeamRecommender inicializado y almacenado en app.state CON DATOS.")
            else: # El motor se instanció, pero su df_employees interno está vacío
                logger.warning(">>> SoftwareTeamRecommender instanciado PERO su DataFrame de empleados está VACÍO. Almacenado en app.state.")
        else: # local_engine_instance es None, la instanciación falló
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
logger.info(f"Instancia de FastAPI creada para '{Config.API_TITLE}' v{Config.API_VERSION}.")

app.add_event_handler("startup", startup_event_handler)
# app.add_event_handler("shutdown", shutdown_event_handler) # Descomenta si tienes una función shutdown_event_handler

# Endpoint para el health check de Render
@app.get("/healthz", tags=["Health Check"])
def health_check():
    # No añadir logs aquí a menos que sea DEBUG, ya que se llama muy frecuentemente
    return {"status": "ok"}

logger.info("Event handlers (startup, healthz) registrados.")

# --- Configuración de CORS ---
FRONTEND_URL_RENDER = "https://team-builder-front.onrender.com"
ADDITIONAL_ALLOWED_ORIGINS_STR = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
additional_origins_list = [origin.strip() for origin in ADDITIONAL_ALLOWED_ORIGINS_STR.split(',') if origin.strip()]
origins = list(set([FRONTEND_URL_RENDER] + additional_origins_list))
if not origins: origins = [FRONTEND_URL_RENDER]

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
    logger.info(f"Intentando incluir router desde teams_router_module (prefix='/api')...")
    app.include_router(teams_router_module.router, prefix="/api", tags=["Teams Management"])
    logger.info(f"Router de 'teams' incluido.")

    logger.info(f"Intentando incluir router desde auth_router_obj (prefix='/api/auth')...")
    app.include_router(auth_router_obj, prefix="/api/auth", tags=["Authentication"])
    logger.info(f"Router de 'auth' incluido.")
    logger.info("Todos los routers incluidos exitosamente.")
except AttributeError as e:
    logger.critical(f"ERROR CRÍTICO AL INCLUIR ROUTERS: Un módulo de router no tiene un atributo 'router' o el objeto importado es incorrecto.", exc_info=True)
    sys.exit("Error crítico: Fallo al incluir routers.")
except Exception as e:
    logger.critical(f"ERROR INESPERADO AL INCLUIR ROUTERS.", exc_info=True)
    sys.exit("Error crítico inesperado al incluir routers.")

# --- Endpoint Raíz (Opcional) ---
@app.get("/", tags=["Root"], summary="API Status Endpoint")
async def read_root(request: Request):
    logger.debug("GET / root endpoint accessed") # Cambiado a DEBUG para reducir verbosidad si LOG_LEVEL es INFO
    engine_status_message = "No disponible (app.state no tiene el atributo 'recommendation_engine')"
    if hasattr(request.app.state, 'recommendation_engine'):
        engine_instance = request.app.state.recommendation_engine
        if engine_instance is not None:
            if hasattr(engine_instance, 'df_employees') and not engine_instance.df_employees.empty:
                engine_status_message = f"Operacional (con {len(engine_instance.df_employees)} empleados)"
            else:
                engine_status_message = "Inicializado pero con DataFrame de empleados interno vacío"
        else:
            engine_status_message = "No inicializado (el motor es None en app.state)"
    return {
        "message": f"Bienvenido a {Config.API_TITLE} v{Config.API_VERSION}",
        "status": "API está corriendo",
        "recommendation_engine_status": engine_status_message,
        "current_log_level": LOG_LEVEL_ENV,
        "render_port_detected_at_start": render_port # Muestra el puerto detectado al inicio
    }

logger.info(f"Configuración completa de la aplicación FastAPI. Lista para que el servidor (Gunicorn/Uvicorn) la sirva en el puerto definido por Render ($PORT={render_port}).")