# app/routers/teams.py

# app/routers/teams.py

from fastapi import APIRouter, HTTPException, Depends, Body, status, Request
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
import logging

# Importaciones relativas desde app/
try:
    from ..recommendation_engine import SoftwareTeamRecommender
    from ..dependencies import get_recommendation_engine
except ImportError as e:
    print(f"ERROR CRITICO [app/routers/teams.py]: No se pudieron importar dependencias o el motor: {e}")
    raise

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/teams",
    tags=["Teams Management"]
)

# --- Modelos Pydantic (LOS MISMOS QUE TENÍAS) ---
class TeamGenerationRequest(BaseModel):
    project_description: str = Field(..., min_length=10)
    team_structure: Dict[str, int] = Field(...)
    budget: float = Field(..., gt=0)
    explicit_technologies_by_role: Optional[Dict[str, List[str]]] = Field(None)
    @validator('team_structure')
    def check_team_structure_values(cls, structure_dict):
        if not structure_dict: raise ValueError('team_structure no puede ser un diccionario vacío.')
        if any(count < 0 for count in structure_dict.values()): raise ValueError('El número de miembros no puede ser negativo.')
        if not any(count > 0 for count in structure_dict.values()): raise ValueError('Al menos un rol debe tener un conteo > 0.')
        return structure_dict

class MemberResponse(BaseModel):
    id: int; nombre: str; email: Optional[str] = None; puesto_original: Optional[str] = None; rol_asignado: str;
    rol_asignado_display: str; seniority_original: Optional[str] = None; seniority_normalizado: Optional[str] = None;
    anos_experiencia: int; proyectos_completados: int; salario: int; score: float;
    tecnologias_conocidas: List[str] = []; nivel_valor_original: Optional[int] = None

class BudgetResponse(BaseModel):
    total: float; utilizado: float; restante: float; porcentaje_utilizado: float = Field(ge=0, le=1)

class MetricsResponse(BaseModel):
    promedio_puntaje: Optional[float] = None; tecnologias_faltantes: List[str] = [];
    roles_cubiertos: Dict[str, int] = {}; roles_solicitados: Dict[str, int] = {}

class TeamGenerationResponse(BaseModel):
    equipo: List[MemberResponse]; presupuesto: BudgetResponse; metricas: MetricsResponse;
    analisis_equipo: Optional[str] = None; status_message: Optional[str] = None;
    inferred_project_technologies: List[str] = []
# --- FIN Modelos Pydantic ---


# --- ENDPOINT DE PRUEBA GET (SE MANTIENE PARA VERIFICAR EL ROUTER) ---
@router.get("/generate/ping", summary="[PRUEBA PING] Verifica si el router de teams responde")
async def ping_teams_generate_route():
    logger.info("--- PRUEBA PING GET: Endpoint /api/teams/generate/ping ALCANZADO ---")
    return {"message": "Pong desde /api/teams/generate/ping! El router de teams está activo."}


# --- ENDPOINT ORIGINAL (AHORA ACTIVO) ---
@router.post(
    "/generate",
    response_model=TeamGenerationResponse, # Se vuelve a activar el response_model
    summary="Generar Equipo Técnico Recomendado",
    description="Recibe detalles del proyecto, estructura, presupuesto y tecnologías; devuelve una recomendación de equipo."
)
async def generate_team_endpoint( # Nombre original
    request_data: TeamGenerationRequest,
    engine: SoftwareTeamRecommender = Depends(get_recommendation_engine) # Se vuelve a activar la dependencia
):
    logger.info("--- INICIO Endpoint /api/teams/generate (ORIGINAL) ---")
    logger.debug(f"Datos de solicitud recibidos (ORIGINAL): {request_data.model_dump_json(indent=2)}")

    try:
        logger.info("Llamando a engine.recommend_team (ORIGINAL)...")
        result_from_engine: Dict[str, Any] = engine.recommend_team(
            project_description=request_data.project_description,
            team_structure=request_data.team_structure,
            budget=request_data.budget,
            explicit_technologies_by_role=request_data.explicit_technologies_by_role or {}
        )

        logger.info(f"Resultado obtenido de engine.recommend_team (ORIGINAL). Tipo: {type(result_from_engine)}")
        if isinstance(result_from_engine, dict):
            logger.debug(f"Claves principales en result_from_engine (ORIGINAL): {list(result_from_engine.keys())}")
            logger.debug(f"Número de miembros en 'equipo' (si existe - ORIGINAL): {len(result_from_engine.get('equipo', [])) if 'equipo' in result_from_engine else 'No presente'}")
            logger.debug(f"Status message (si existe - ORIGINAL): {result_from_engine.get('status_message', 'No presente')}")
        else:
            logger.error(f"¡ALERTA! engine.recommend_team NO devolvió un diccionario (ORIGINAL). Tipo: {type(result_from_engine)}. Contenido (primeros 500 chars): {str(result_from_engine)[:500]}")

        if result_from_engine is None:
            logger.error("engine.recommend_team devolvió None (ORIGINAL).")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="El motor de recomendación devolvió un resultado nulo (None), lo cual es inesperado."
            )
        if not isinstance(result_from_engine, dict):
            logger.error(f"engine.recommend_team devolvió un tipo inesperado (ORIGINAL): {type(result_from_engine)}. Se esperaba un dict.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"El motor de recomendación devolvió un tipo de dato inesperado: {type(result_from_engine)}."
            )

        logger.info("--- FIN Endpoint /api/teams/generate (ORIGINAL) - Intentando devolver result_from_engine ---")
        return result_from_engine

    except HTTPException as http_exc:
        logger.error(f"HTTPException (ya manejada) capturada en /api/teams/generate (ORIGINAL): Status={http_exc.status_code}, Detail='{http_exc.detail}'")
        raise http_exc
    except ValueError as ve: # Errores de validación de Pydantic o del motor
        logger.warning(f"ValueError en la lógica de /api/teams/generate (ORIGINAL) o validación: {ve}", exc_info=True) # Añadido exc_info
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Error de validación o datos: {str(ve)}"
        )
    except Exception as e: # Cualquier otra excepción
        logger.exception("Error GENÉRICO e INESPERADO en /api/teams/generate (ORIGINAL). Revisar traceback.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error interno crítico en el servidor al generar la recomendación."
        )

# --- ENDPOINT DE PRUEBA POST (SIMPLIFICADO - AHORA COMENTADO O ELIMINADO) ---
"""
@router.post(
    "/generate", # Mantenemos la misma ruta POST /api/teams/generate
    summary="[PRUEBA POST] Endpoint /generate simplificado",
)
async def generate_team_endpoint_TEST(
    request_data: TeamGenerationRequest
):
    # ... (código del endpoint de prueba)
"""