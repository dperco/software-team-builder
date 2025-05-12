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
    raise

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/teams",
    tags=["Teams Management"]
)

# --- Modelos Pydantic (SE MANTIENEN INTACTOS) ---
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


# --- ENDPOINT DE PRUEBA GET (para verificar que el router está activo) ---
@router.get("/generate/ping", summary="[PRUEBA PING] Verifica si el router de teams responde")
async def ping_teams_generate_route():
    logger.info("--- PRUEBA PING GET: Endpoint /api/teams/generate/ping ALCANZADO ---")
    return {"message": "Pong desde /api/teams/generate/ping! El router de teams está activo."}


# --- TU FUNCIÓN ORIGINAL (DEBE ESTAR COMENTADA O RENOMBRADA) ---
"""
@router.post("/generate", response_model=TeamGenerationResponse, ...)
async def generate_team_endpoint_ORIGINAL( ... ):
    ...
"""

# --- ENDPOINT DE PRUEBA POST (SIMPLIFICADO - EL QUE SE USARÁ AHORA) ---
@router.post(
    "/generate", # Mantenemos la misma ruta POST /api/teams/generate
    summary="[PRUEBA POST] Endpoint /generate simplificado",
)
async def generate_team_endpoint_TEST( # Renombrado para evitar colisión si descomentas el original
    request_data: TeamGenerationRequest
):
    logger.info("--- PRUEBA POST: Endpoint /api/teams/generate (SIMPLIFICADO) FUE LLAMADO ---")
    logger.debug(f"--- PRUEBA POST: Datos de solicitud recibidos (SIMPLIFICADO): {request_data.model_dump_json(indent=2)}")

    test_json_response = {
        "equipo": [],
        "presupuesto": {
            "total": float(request_data.budget),
            "utilizado": 0.0,
            "restante": float(request_data.budget),
            "porcentaje_utilizado": 0.0
        },
        "metricas": {
            "promedio_puntaje": 0.0,
            "tecnologias_faltantes": ["tecnologia_prueba_1", "tecnologia_prueba_2"],
            "roles_cubiertos": {"backend_test": 0},
            "roles_solicitados": request_data.team_structure
        },
        "analisis_equipo": "Esta es una respuesta de PRUEBA del endpoint /api/teams/generate simplificado.",
        "status_message": "Endpoint de prueba POST alcanzado exitosamente.",
        "inferred_project_technologies": ["inferida_prueba_A", "inferida_prueba_B"]
    }
    
    logger.info(f"--- PRUEBA POST: Devolviendo respuesta JSON de prueba (SIMPLIFICADO): {test_json_response} ---")
    return test_json_response