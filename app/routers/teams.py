# app/routers/teams.py

# app/routers/teams.py

from fastapi import APIRouter, HTTPException, Depends, Body, status, Request
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
import logging

# Importaciones relativas desde app/ (SE MANTIENEN)
try:
    from ..recommendation_engine import SoftwareTeamRecommender
    from ..dependencies import get_recommendation_engine
except ImportError as e:
    print(f"ERROR CRITICO [app/routers/teams.py]: No se pudieron importar dependencias o el motor: {e}")
    # logger no estará disponible aquí si logging no se ha configurado en main aun
    raise

logger = logging.getLogger(__name__) # Logger para este módulo ('app.routers.teams')

router = APIRouter(
    prefix="/teams", # El prefijo del router es /teams. En main.py se monta bajo /api, entonces la ruta final es /api/teams
    tags=["Teams Management"]
)

# --- Modelos Pydantic (SE MANTIENEN) ---
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

class MemberResponse(BaseModel): # Y los otros modelos de respuesta
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


# --- NUEVO ENDPOINT DE PRUEBA GET ---
@router.get("/generate/ping", summary="[PRUEBA PING] Verifica si el router de teams responde")
async def ping_teams_generate_route():
    logger.info("--- PRUEBA PING GET: Endpoint /api/teams/generate/ping ALCANZADO ---")
    return {"message": "Pong desde /api/teams/generate/ping! El router de teams está activo."}


# --- TU FUNCIÓN ORIGINAL (Coméntala o reNómbrala temporalmente) ---
# (Asegúrate de que la versión original de generate_team_endpoint esté comentada)
"""
@router.post(
    "/generate",
    response_model=TeamGenerationResponse,
    # ... (resto de tu endpoint original)
)
async def generate_team_endpoint(
    # ... (argumentos)
):
    # ... (lógica original)
"""

# --- NUEVO ENDPOINT DE PRUEBA POST (SIMPLIFICADO) ---
@router.post(
    "/generate", # Mantenemos la misma ruta POST /api/teams/generate
    summary="[PRUEBA POST] Endpoint /generate simplificado",
    # No usamos response_model ni Depends(get_recommendation_engine) temporalmente
)
async def generate_team_endpoint_TEST(
    request_data: TeamGenerationRequest # Validamos el cuerpo del request con el modelo
):
    logger.info("--- PRUEBA POST: Endpoint /api/teams/generate (SIMPLIFICADO) FUE LLAMADO ---")
    logger.debug(f"--- PRUEBA POST: Datos de solicitud recibidos (SIMPLIFICADO): {request_data.model_dump_json(indent=2)}")

    # Devolvemos un JSON simple y estático que se parezca un poco a la estructura esperada
    test_json_response = {
        "equipo": [
            # Puedes añadir un miembro de ejemplo si quieres probar el renderizado del frontend
            # {
            #     "id": 1, "nombre": "Tester McTest", "email": "tester@example.com",
            #     "puesto_original": "Test Engineer", "rol_asignado": "qa", "rol_asignado_display": "QA",
            #     "seniority_original": "Senior", "seniority_normalizado": "senior",
            #     "anos_experiencia": 5, "proyectos_completados": 10, "salario": 50000, "score": 0.95,
            #     "tecnologias_conocidas": ["Python", "Selenium"], "nivel_valor_original": 5
            # }
        ],
        "presupuesto": {
            "total": float(request_data.budget), # Usar algo del request
            "utilizado": 0.0,
            "restante": float(request_data.budget),
            "porcentaje_utilizado": 0.0
        },
        "metricas": {
            "promedio_puntaje": 0.0,
            "tecnologias_faltantes": ["prueba_tech_faltante1"],
            "roles_cubiertos": {}, # Puedes simular roles cubiertos
            "roles_solicitados": request_data.team_structure # Usar algo del request
        },
        "analisis_equipo": "Esta es una respuesta de PRUEBA del endpoint /api/teams/generate simplificado.",
        "status_message": "Endpoint de prueba POST alcanzado exitosamente.",
        "inferred_project_technologies": ["prueba_tech_inferida1", "prueba_tech_inferida2"]
    }
    
    logger.info(f"--- PRUEBA POST: Devolviendo respuesta JSON de prueba (SIMPLIFICADO): {test_json_response} ---")
    return test_json_response