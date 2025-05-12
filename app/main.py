# app/main.py
import os
import sys
import logging

# --- Configuración de Logging PRIMERO ---
LOG_LEVEL_ENV = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL_ENV,
    format='%(levelname)-8s %(asctime)s [%(name)s] [%(module)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
initial_logger = logging.getLogger("app.initial_setup")
render_port = os.getenv("PORT")
initial_logger.info(f"--- MAIN.PY INICIO --- Variable de entorno PORT de Render: {render_port}")
if not render_port: initial_logger.warning("--- MAIN.PY INICIO --- ¡ALERTA! La variable de entorno PORT NO ESTÁ DEFINIDA.")
# --- Resto de tus imports ---
from typing import Optional; import pandas as pd
from fastapi import FastAPI, Depends, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
# --- Añadir la raíz del proyecto a sys.path ---
PROJECT_ROOT_FOR_CONFIG_IMPORT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT_FOR_CONFIG_IMPORT not in sys.path: sys.path.insert(0, PROJECT_ROOT_FOR_CONFIG_IMPORT)
initial_logger.info(f"Añadido al sys.path para imports: {PROJECT_ROOT_FOR_CONFIG_IMPORT}")
try:
    from config import Config; from .recommendation_engine import SoftwareTeamRecommender
    from .routers import teams as teams_router_module; from .auth.router import router as auth_router_obj
    from .dependencies import get_recommendation_engine
    initial_logger.info("Importaciones principales de la aplicación completadas.")
except ImportError as e: initial_logger.critical(f"ERROR CRÍTICO AL IMPORTAR MÓDULOS: {e}", exc_info=True); sys.exit(f"Error de importación: {e}.")
logger = logging.getLogger(__name__)
logger.info(f"Nivel de logging para '{__name__}' configurado a: {LOG_LEVEL_ENV}")
PROJECT_ROOT_PATH = PROJECT_ROOT_FOR_CONFIG_IMPORT

async def startup_event_handler():
    logger.info(">>> INICIO FastAPI startup_event_handler: Intentando inicializar servicios...")
    data_file_path = os.path.join(PROJECT_ROOT_PATH, Config.DATA_SUBDIR, Config.EMPLOYEE_DATA_FILE_NAME)
    local_engine_instance: Optional[SoftwareTeamRecommender] = None
    df_employees = pd.DataFrame()
    try:
        logger.info(f"Intentando cargar datos de empleados desde: {data_file_path}")
        if not os.path.exists(data_file_path): logger.error(f"CRITICAL: Archivo de datos NO ENCONTRADO: {data_file_path}.")
        else:
            df_employees = pd.read_csv(data_file_path, delimiter=';')
            if df_employees.empty: logger.warning(f"Archivo {data_file_path} VACÍO.")
            else: logger.info(f"Datos cargados ({len(df_employees)} filas) desde {Config.EMPLOYEE_DATA_FILE_NAME}.")
        logger.info(f"Intentando crear instancia de SoftwareTeamRecommender con DataFrame de {len(df_employees)} filas.")
        local_engine_instance = SoftwareTeamRecommender(df_employees)
        logger.info("Instancia de SoftwareTeamRecommender creada.")
    except Exception as e: logger.exception(f"CRITICAL ERROR INESPERADO en startup_event.")
    finally:
        app.state.recommendation_engine = local_engine_instance
        if local_engine_instance:
            if hasattr(local_engine_instance, 'df_employees') and not local_engine_instance.df_employees.empty:
                logger.info(">>> SoftwareTeamRecommender inicializado y almacenado en app.state CON DATOS.")
            else: logger.warning(">>> SoftwareTeamRecommender instanciado PERO con DataFrame VACÍO. Almacenado en app.state.")
        else: logger.error(">>> SoftwareTeamRecommender NO PUDO ser instanciado. app.state.recommendation_engine es None.")
    logger.info(">>> FIN FastAPI startup_event_handler.")

app = FastAPI(title=Config.API_TITLE, version=Config.API_VERSION, description=Config.API_DESCRIPTION, docs_url=Config.API_DOCS_URL, redoc_url=Config.API_REDOC_URL)
logger.info(f"Instancia de FastAPI creada para '{Config.API_TITLE}' v{Config.API_VERSION}.")
app.add_event_handler("startup", startup_event_handler)
@app.get("/healthz", tags=["Health Check"])
def health_check(): return {"status": "ok"}
logger.info("Event handlers (startup, healthz) registrados.")
# --- Configuración de CORS ---
FRONTEND_URL_RENDER = "https://team-builder-front.onrender.com"
ADDITIONAL_ALLOWED_ORIGINS_STR = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
additional_origins_list = [origin.strip() for origin in ADDITIONAL_ALLOWED_ORIGINS_STR.split(',') if origin.strip()]
origins = list(set([FRONTEND_URL_RENDER] + additional_origins_list))
if not origins: origins = [FRONTEND_URL_RENDER]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
logger.info(f"CORSMiddleware añadido. Orígenes permitidos: {origins}")
# --- Incluir Routers ---
try:
    logger.info(f"Incluyendo router desde teams_router_module (prefix='/api')...")
    app.include_router(teams_router_module.router, prefix="/api", tags=["Teams Management"])
    logger.info(f"Router de 'teams' incluido.")
    logger.info(f"Incluyendo router desde auth_router_obj (prefix='/api/auth')...")
    app.include_router(auth_router_obj, prefix="/api/auth", tags=["Authentication"])
    logger.info(f"Router de 'auth' incluido.")
    logger.info("Todos los routers incluidos exitosamente.")
except Exception as e: logger.critical(f"ERROR CRÍTICO AL INCLUIR ROUTERS.", exc_info=True); sys.exit("Error al incluir routers.")
# --- Endpoint Raíz ---
@app.get("/", tags=["Root"], summary="API Status Endpoint")
async def read_root(request: Request):
    logger.debug("GET / root endpoint accessed")
    engine_status_message = "No disponible (app.state no tiene 'recommendation_engine')"
    if hasattr(request.app.state, 'recommendation_engine'):
        engine = request.app.state.recommendation_engine
        if engine:
            if hasattr(engine, 'df_employees') and not engine.df_employees.empty: engine_status_message = f"Operacional ({len(engine.df_employees)} empleados)"
            else: engine_status_message = "Inicializado pero con DataFrame interno vacío"
        else: engine_status_message = "No inicializado (engine es None en app.state)"
    return {"message": f"Bienvenido a {Config.API_TITLE} v{Config.API_VERSION}", "status": "API corriendo", "recommendation_engine_status": engine_status_message, "current_log_level": LOG_LEVEL_ENV, "render_port_detected_at_start": render_port}
logger.info(f"Configuración completa de FastAPI. Servidor escuchará en $PORT={render_port}.")