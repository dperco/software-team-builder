# software-team-builder/app/routers/teams.py
from fastapi import APIRouter, HTTPException, Depends, Body, status, Request
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
import logging

# Importaciones relativas desde app/
try:
    from ..recommendation_engine import SoftwareTeamRecommender # Para el type hint
    from ..dependencies import get_recommendation_engine # Importa la dependencia correcta
except ImportError as e:
    print(f"ERROR CRITICO [app/routers/teams.py]: No se pudieron importar dependencias o el motor: {e}")
    raise

logger = logging.getLogger(__name__) # Logger para este módulo

router = APIRouter(
    prefix="/teams", # Prefijo para todos los endpoints en este router (/api/teams/...)
    tags=["Teams Management"] # Agrupación en la documentación OpenAPI/Swagger
)

# --- Modelos Pydantic para Validación y Documentación ---

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

# Modelo para un miembro individual en la respuesta
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

# Modelo para la información de presupuesto en la respuesta
class BudgetResponse(BaseModel):
    total: float
    utilizado: float
    restante: float
    porcentaje_utilizado: float = Field(ge=0, le=1)

# Modelo para métricas adicionales en la respuesta
class MetricsResponse(BaseModel):
    promedio_puntaje: Optional[float] = None
    tecnologias_faltantes: List[str] = []
    roles_cubiertos: Dict[str, int] = {}
    roles_solicitados: Dict[str, int] = {}

# Modelo principal para la respuesta completa del endpoint /generate
class TeamGenerationResponse(BaseModel):
    equipo: List[MemberResponse]
    presupuesto: BudgetResponse
    metricas: MetricsResponse
    analisis_equipo: Optional[str] = None
    status_message: Optional[str] = None
    inferred_project_technologies: List[str] = []


# --- Endpoint para Generar Equipo ---
@router.post(
    "/generate",
    response_model=TeamGenerationResponse, # Valida la estructura de la respuesta
    summary="Generar Equipo Técnico Recomendado",
    description="Recibe detalles del proyecto, estructura, presupuesto y tecnologías; devuelve una recomendación de equipo."
)
async def generate_team_endpoint(
    request_data: TeamGenerationRequest, # Valida el cuerpo del request
    # Inyecta la instancia del motor usando la dependencia definida en app/dependencies.py
    engine: SoftwareTeamRecommender = Depends(get_recommendation_engine)
):
    """
    Endpoint principal para la generación de equipos.
    Utiliza el motor de recomendación inyectado para procesar la solicitud.
    """
    logger.info(f"Endpoint /teams/generate: Solicitud recibida.")
    # Descomentar para ver los datos recibidos en logs DEBUG
    # logger.debug(f"Request data: {request_data.model_dump_json(indent=2)}")

    # La dependencia `get_recommendation_engine` ya maneja el caso donde engine es None lanzando HTTPException 503.
    # Por lo tanto, si llegamos aquí, 'engine' es una instancia válida.

    try:
        # Llamada al método principal del motor de recomendación
        result_from_engine: Dict[str, Any] = engine.recommend_team(
            project_description=request_data.project_description,
            team_structure=request_data.team_structure,
            budget=request_data.budget,
            explicit_technologies_by_role=request_data.explicit_technologies_by_role or {} # Pasa dict vacío si es None
        )

        # Loguear un resumen del resultado del motor (evitar loguear datos sensibles si los hubiera)
        logger.info(f"Endpoint /teams/generate: Recomendación generada: {len(result_from_engine.get('equipo',[]))} miembros, "
                    f"Presupuesto usado: {result_from_engine.get('presupuesto',{}).get('utilizado',0):.2f}")
        # logger.debug(f"Engine result (raw dictionary): {result_from_engine}") # Log completo si es necesario

        # FastAPI validará automáticamente que 'result_from_engine' coincida con el
        # modelo 'TeamGenerationResponse' antes de enviarlo al cliente.
        return result_from_engine

    except ValueError as ve:
        # Capturar errores de validación o lógicos específicos del motor
        logger.warning(f"Endpoint /teams/generate: Error de valor durante la recomendación: {ve}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, # Error semántico con la solicitud
            detail=str(ve)
        )
    except Exception as e:
        # Capturar cualquier otra excepción inesperada
        logger.exception(f"Endpoint /teams/generate: Error inesperado durante la recomendación.") # Log con stack trace
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error interno en el servidor al generar la recomendación."
        )

# Aquí puedes añadir los otros endpoints (/history, /last-team)
# si implementas el HistoryManager y su dependencia correspondiente.