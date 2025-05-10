# software-team-builder/app/dependencies.py
# software-team-builder/app/dependencies.py
from fastapi import Request, HTTPException, status
from typing import Optional
import logging

# Importa la CLASE del motor, no el módulo main o algo que cree un ciclo.
# Asumiendo que recommendation_engine.py está directamente en app/
try:
    from .recommendation_engine import SoftwareTeamRecommender
    # from .services.history_manager import FileHistoryManager # Ejemplo si tuvieras otro
except ImportError as e:
    print(f"WARN [dependencies.py]: Could not import SoftwareTeamRecommender (o otras dependencias): {e}. "
          "Esto podría ser un problema si no se resuelve en el contexto de la app FastAPI.")
    SoftwareTeamRecommender = None # Define como None para que el type hint funcione
    # FileHistoryManager = None

logger = logging.getLogger(__name__) # Obtener logger

async def get_recommendation_engine(request: Request) -> SoftwareTeamRecommender:
    """
    Dependencia de FastAPI para obtener la instancia del motor de recomendación
    desde request.app.state.
    Lanza HTTPException si el motor no está disponible (no inicializado o error).
    """
    if not hasattr(request.app.state, 'recommendation_engine') or request.app.state.recommendation_engine is None:
        # Loguear el error ANTES de lanzar la excepción
        logger.error("Dependency get_recommendation_engine: 'recommendation_engine' not found or is None in app.state. "
                     "Esto usualmente indica un problema durante el evento de inicio de la aplicación.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El servicio de recomendación no está disponible en este momento (error de inicialización)."
        )

    # Si llegamos aquí, el atributo existe y no es None.
    engine = request.app.state.recommendation_engine

    # Verificación adicional de tipo (por si acaso algo más asignó a app.state)
    # Solo si SoftwareTeamRecommender no es None (es decir, la importación inicial funcionó)
    if SoftwareTeamRecommender is not None and not isinstance(engine, SoftwareTeamRecommender):
         logger.error(f"Dependency get_recommendation_engine: Object in app.state.recommendation_engine is not a SoftwareTeamRecommender instance. Type: {type(engine)}")
         raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno: Tipo incorrecto para el servicio de recomendación."
        )
    return engine

# (Opcional) Dependencia para HistoryManager
# async def get_history_manager(request: Request) -> FileHistoryManager:
#     if not hasattr(request.app.state, 'history_manager') or request.app.state.history_manager is None:
#         logger.error("Dependency get_history_manager: 'history_manager' not found or is None in app.state.")
#         raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Servicio de historial no disponible.")
#     hm = request.app.state.history_manager
#     if FileHistoryManager is not None and not isinstance(hm, FileHistoryManager):
#          logger.error(f"Dependency get_history_manager: Object in app.state.history_manager is not a FileHistoryManager. Type: {type(hm)}")
#          raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno: Tipo incorrecto para el servicio de historial.")
#     return hm