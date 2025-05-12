## app/routers/teams.py

from fastapi import APIRouter, HTTPException, Depends, Body, status, Request
from pydantic import BaseModel, Field, validator # BaseModel ya está en FastAPI, no necesitas importarlo de pydantic directamente si usas FastAPI >= 0.100
from typing import Optional, Dict, Any, List
import logging

# Importaciones relativas desde app/
try:
    from ..recommendation_engine import SoftwareTeamRecommender # Para el type hint
    from ..dependencies import get_recommendation_engine # Importa la dependencia correcta
except ImportError as e:
    # Este print es para el inicio, el logger podría no estar configurado aún
    print(f"ERROR CRITICO [app/routers/teams.py]: No se pudieron importar dependencias o el motor: {e}")
    # Una vez que el logger está configurado, también podría loguear, pero el print asegura visibilidad temprana.
    # logger.critical(f"No se pudieron importar dependencias o el motor: {e}") # Descomentar si el logger ya está activo
    raise # Levanta la excepción para detener la aplicación si es un error crítico de importación

logger = logging.getLogger(__name__) # Logger para este módulo

router = APIRouter(
    prefix="/teams", # Prefijo para todos los endpoints en este router (/api/teams/...)
    tags=["Teams Management"] # Agrupación en la documentación OpenAPI/Swagger
)

# --- Modelos Pydantic (LOS MISMOS QUE TENÍAS) ---
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


# --- Endpoint para Generar Equipo ---
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
    logger.info("--- INICIO Endpoint /api/teams/generate ---")
    logger.debug(f"Datos de solicitud recibidos: {request_data.model_dump_json(indent=2)}")

    # La dependencia get_recommendation_engine ya maneja el caso donde engine es None
    # (debería lanzar un HTTPException 503 si app.state.recommendation_engine es None).

    try:
        logger.info("Llamando a engine.recommend_team...")
        result_from_engine: Dict[str, Any] = engine.recommend_team(
            project_description=request_data.project_description,
            team_structure=request_data.team_structure,
            budget=request_data.budget,
            explicit_technologies_by_role=request_data.explicit_technologies_by_role or {}
        )

        # Logs detallados SOBRE el resultado ANTES de devolverlo
        logger.info(f"Resultado obtenido de engine.recommend_team. Tipo: {type(result_from_engine)}")
        if isinstance(result_from_engine, dict):
            # Loguear solo un resumen para no inundar los logs si el diccionario es muy grande
            logger.debug(f"Claves principales en result_from_engine: {list(result_from_engine.keys())}")
            logger.debug(f"Número de miembros en 'equipo' (si existe): {len(result_from_engine.get('equipo', [])) if 'equipo' in result_from_engine else 'No presente'}")
            logger.debug(f"Status message (si existe): {result_from_engine.get('status_message', 'No presente')}")
        else:
            # Esto sería un problema, ya que esperamos un dict para el response_model
            logger.error(f"¡ALERTA! engine.recommend_team NO devolvió un diccionario. Tipo: {type(result_from_engine)}. Contenido (primeros 500 chars): {str(result_from_engine)[:500]}")

        # Verificaciones cruciales antes de devolver
        if result_from_engine is None:
            logger.error("engine.recommend_team devolvió None. Esto no es un JSON válido y causará un error de parseo en el frontend si se devuelve un 200 OK con cuerpo vacío.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="El motor de recomendación devolvió un resultado nulo (None), lo cual es inesperado."
            )
        if not isinstance(result_from_engine, dict):
            logger.error(f"engine.recommend_team devolvió un tipo inesperado: {type(result_from_engine)}. Se esperaba un dict para que Pydantic lo valide contra TeamGenerationResponse.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"El motor de recomendación devolvió un tipo de dato inesperado: {type(result_from_engine)}."
            )

        # Si llegamos aquí, result_from_engine es un diccionario.
        # FastAPI/Pydantic intentará validarlo contra `TeamGenerationResponse`.
        # Si la validación falla, se lanzará un error interno (generalmente un 500 con detalles de validación)
        # que debería aparecer en los logs de Render si el nivel de log es adecuado (INFO o DEBUG).
        logger.info("--- FIN Endpoint /api/teams/generate - Intentando devolver result_from_engine ---")
        return result_from_engine

    except HTTPException as http_exc:
        # Re-lanzar excepciones HTTP que ya fueron manejadas (ej., desde la dependencia o validadores Pydantic)
        logger.error(f"HTTPException (ya manejada) capturada en /api/teams/generate: Status={http_exc.status_code}, Detail='{http_exc.detail}'")
        raise http_exc # FastAPI la manejará
    except ValueError as ve:
        # Errores de valor, a menudo de validaciones Pydantic del request_data
        # o errores lógicos dentro de recommend_team que lanzan ValueError
        logger.warning(f"ValueError en la lógica de /api/teams/generate o validación de request: {ve}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, # Unprocessable Entity
            detail=f"Error de validación o datos: {str(ve)}"
        )
    except Exception as e:
        # Capturar cualquier otra excepción inesperada que no sea HTTPException o ValueError
        logger.exception("Error GENÉRICO e INESPERADO en /api/teams/generate. Revisar traceback.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error interno crítico en el servidor al generar la recomendación."
        )