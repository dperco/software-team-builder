# app/routers/teams.py

from fastapi import APIRouter, HTTPException, Depends, Body, status, Request
from pydantic import BaseModel, Field, validator # BaseModel ya está en FastAPI
from typing import Optional, Dict, Any, List
import logging

# Importaciones relativas desde app/ (SE MANTIENEN por si quieres volver a la original rápidamente)
try:
    from ..recommendation_engine import SoftwareTeamRecommender
    from ..dependencies import get_recommendation_engine
except ImportError as e:
    print(f"ERROR CRITICO [app/routers/teams.py]: No se pudieron importar dependencias o el motor: {e}")
    raise

logger = logging.getLogger(__name__) # Logger para este módulo

router = APIRouter(
    prefix="/teams",
    tags=["Teams Management"]
)

# --- Modelos Pydantic (SE MANTIENEN INTACTOS POR AHORA) ---
# Necesitas TeamGenerationRequest para que la firma del endpoint de prueba siga validando el cuerpo del request.
class TeamGenerationRequest(BaseModel):
    project_description: str = Field(
        ...,
        min_length=10,
        example="Desarrollo de aplicación web con React y Node.js para gestión de inventario."
    )
    team_structure: Dict[str, int] = Field(
        ...,
        example={"backend": 2, "frontend": 1, "devops": 0}
    )
    budget: float = Field(..., gt=0, example=250000.0)
    explicit_technologies_by_role: Optional[Dict[str, List[str]]] = Field(
        None,
        example={"backend": ["Python", "Django"], "frontend": ["React"]}
    )

    @validator('team_structure')
    def check_team_structure_values(cls, structure_dict):
        if not structure_dict:
             raise ValueError('team_structure no puede ser un diccionario vacío si se proporciona.')
        if any(count < 0 for count in structure_dict.values()):
            raise ValueError('El número de miembros para un rol en team_structure no puede ser negativo.')
        if not any(count > 0 for count in structure_dict.values()):
            raise ValueError('Si se define team_structure, al menos un rol debe tener un conteo mayor a cero.')
        return structure_dict

# Los otros modelos de respuesta (MemberResponse, BudgetResponse, MetricsResponse, TeamGenerationResponse)
# no son estrictamente necesarios para ESTA PRUEBA del endpoint, pero no hace daño dejarlos.
class MemberResponse(BaseModel):
    id: int
    nombre: str
    email: Optional[str] = None
    puesto_original: Optional[str] = None
    rol_asignado: str
    rol_asignado_display: str
    seniority_original: Optional[str] = None
    seniority_normalizado: Optional[str] = None
    anos_experiencia: int
    proyectos_completados: int
    salario: int
    score: float
    tecnologias_conocidas: List[str] = []
    nivel_valor_original: Optional[int] = None

class BudgetResponse(BaseModel):
    total: float
    utilizado: float
    restante: float
    porcentaje_utilizado: float = Field(ge=0, le=1)

class MetricsResponse(BaseModel):
    promedio_puntaje: Optional[float] = None
    tecnologias_faltantes: List[str] = []
    roles_cubiertos: Dict[str, int] = {}
    roles_solicitados: Dict[str, int] = {}

class TeamGenerationResponse(BaseModel):
    equipo: List[MemberResponse]
    presupuesto: BudgetResponse
    metricas: MetricsResponse
    analisis_equipo: Optional[str] = None
    status_message: Optional[str] = None
    inferred_project_technologies: List[str] = []
# --- FIN Modelos Pydantic ---


# --- TU FUNCIÓN ORIGINAL (Coméntala o reNómbrala temporalmente) ---
"""
@router.post(
    "/generate",
    response_model=TeamGenerationResponse,
    summary="Generar Equipo Técnico Recomendado",
    description="Recibe detalles del proyecto, estructura, presupuesto y tecnologías; devuelve una recomendación de equipo."
)
async def generate_team_endpoint(
    request_data: TeamGenerationRequest,
    engine: SoftwareTeamRecommender = Depends(get_recommendation_engine)
):
    logger.info("--- INICIO Endpoint /api/teams/generate (ORIGINAL) ---")
    logger.debug(f"Datos de solicitud recibidos: {request_data.model_dump_json(indent=2)}")
    try:
        logger.info("Llamando a engine.recommend_team...")
        result_from_engine: Dict[str, Any] = engine.recommend_team(
            project_description=request_data.project_description,
            team_structure=request_data.team_structure,
            budget=request_data.budget,
            explicit_technologies_by_role=request_data.explicit_technologies_by_role or {}
        )
        logger.info(f"Resultado obtenido de engine.recommend_team. Tipo: {type(result_from_engine)}")
        if isinstance(result_from_engine, dict):
            logger.debug(f"Claves principales en result_from_engine: {list(result_from_engine.keys())}")
            logger.debug(f"Número de miembros en 'equipo' (si existe): {len(result_from_engine.get('equipo', [])) if 'equipo' in result_from_engine else 'No presente'}")
        else:
            logger.error(f"¡ALERTA! engine.recommend_team NO devolvió un diccionario. Tipo: {type(result_from_engine)}.")
        if result_from_engine is None:
            logger.error("engine.recommend_team devolvió None.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="El motor de recomendación devolvió un resultado nulo."
            )
        if not isinstance(result_from_engine, dict):
            logger.error(f"engine.recommend_team devolvió un tipo inesperado: {type(result_from_engine)}.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"El motor de recomendación devolvió un tipo de dato inesperado: {type(result_from_engine)}."
            )
        logger.info("--- FIN Endpoint /api/teams/generate (ORIGINAL) - Intentando devolver resultado ---")
        return result_from_engine
    except HTTPException as http_exc:
        logger.error(f"HTTPException capturada en /api/teams/generate (ORIGINAL): Status={http_exc.status_code}, Detail='{http_exc.detail}'")
        raise http_exc
    except ValueError as ve:
        logger.warning(f"ValueError en /api/teams/generate (ORIGINAL): {ve}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ve))
    except Exception as e:
        logger.exception("Error GENÉRICO e inesperado en /api/teams/generate (ORIGINAL).")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno crítico.")
"""

# --- NUEVO ENDPOINT DE PRUEBA (SIMPLIFICADO) ---
@router.post(
    "/generate", # Mantenemos la misma ruta para que el frontend la llame
    summary="[PRUEBA] Generar Equipo Técnico Recomendado (Simplificado)",
    # Quitamos response_model y Depends temporalmente para aislar el problema
)
async def generate_team_endpoint_TEST(
    request_data: TeamGenerationRequest # Mantenemos esto para que el cuerpo del request aún se valide
):
    logger.info("--- PRUEBA: Endpoint /api/teams/generate (SIMPLIFICADO) FUE LLAMADO ---")
    logger.debug(f"--- PRUEBA: Datos de solicitud recibidos (SIMPLIFICADO): {request_data.model_dump_json(indent=2)}")

    # Devolvemos un JSON simple y estático
    test_json_response = {
        "equipo": [], # Lista vacía para cumplir parcialmente con la estructura esperada por el frontend
        "presupuesto": {
            "total": request_data.budget, # Usamos algo del request para ver que llega
            "utilizado": 0.0,
            "restante": request_data.budget,
            "porcentaje_utilizado": 0.0
        },
        "metricas": {
            "promedio_puntaje": 0.0,
            "tecnologias_faltantes": ["prueba_tech1", "prueba_tech2"],
            "roles_cubiertos": {},
            "roles_solicitados": request_data.team_structure
        },
        "analisis_equipo": "Respuesta de PRUEBA del endpoint simplificado.",
        "status_message": "Endpoint de prueba alcanzado exitosamente.",
        "inferred_project_technologies": ["prueba_inferida1"]
    }
    
    logger.info(f"--- PRUEBA: Devolviendo respuesta JSON de prueba (SIMPLIFICADO): {test_json_response} ---")
    return test_json_response

# Aquí puedes añadir los otros endpoints (/history, /last-team) si los tienes.