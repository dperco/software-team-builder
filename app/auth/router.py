# app/auth/router.py
import mysql.connector
import os
import re # Importar regex para validación de contraseña si se usa
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv
from passlib.context import CryptContext
import logging # Usar logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:     %(asctime)s - %(message)s')

# Cargar variables de entorno
# Busca .env en directorios superiores (debería encontrar el de la raíz al correr desde /app)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
logging.info("auth/router.py: .env cargado (si existe)")


# --- Configuración Hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Funciones de Utilidad Contraseña ---
def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password: return False
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logging.error(f"Error verificando contraseña: {e}")
        return False

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# --- Router ---
router = APIRouter(
    tags=["Authentication"]
)

# --- Configuración Base de Datos ---
def get_db_connection():
    conn = None
    db_host = os.getenv("DB_HOST")
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME")
    db_port = os.getenv("DB_PORT", 3306) # Default a 3306 si no está en .env

    # Log para depurar variables de entorno
    # logging.debug(f"DB Connect Params: Host={db_host}, User={db_user}, DB={db_name}, Port={db_port}, Pass Provided: {'Yes' if db_pass else 'No'}")

    if not all([db_host, db_user, db_pass, db_name]):
         logging.error("Faltan variables de entorno requeridas para la conexión a la BD (DB_HOST, DB_USER, DB_PASSWORD, DB_NAME)")
         raise HTTPException(
              status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
              detail="Configuración de base de datos incompleta."
         )

    try:
        conn = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_pass,
            database=db_name,
            port=int(db_port) # Convertir puerto a entero
        )
        if not conn.is_connected():
             logging.error("MySQL connection established but not connected.")
             raise mysql.connector.Error("Fallo al obtener conexión DB.")
        # logging.info("Conexión a DB establecida exitosamente.")
        yield conn
    except mysql.connector.Error as err:
        logging.error(f"Error conectando a la DB: {err}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"No se pudo conectar a la base de datos: {err}"
        )
    except ValueError:
         logging.error(f"Error: DB_PORT ('{db_port}') no es un número válido.")
         raise HTTPException(
              status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
              detail="Puerto de base de datos inválido en la configuración."
         )
    finally:
        if conn and conn.is_connected():
            # logging.info("Cerrando conexión a DB.")
            conn.close()

# --- Modelos Pydantic ---

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    message: str
    username: str

class RegisterRequest(BaseModel):
    # Ajusta las validaciones según lo discutido previamente
    username: str = Field(..., min_length=5, max_length=50)
    password: str = Field(..., min_length=8)

    @validator('username')
    def username_validation(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
             raise ValueError('Usuario: Solo letras (a-z, A-Z), números (0-9) y guión bajo (_).')
        return v

    @validator('password')
    def password_complexity(cls, v):
        errors = []
        if len(v) < 8: errors.append("Mínimo 8 caracteres.")
        if not re.search(r"[A-Z]", v): errors.append("Incluir mayúscula.")
        if not re.search(r"[a-z]", v): errors.append("Incluir minúscula.")
        if not re.search(r"\d", v): errors.append("Incluir número.")
        if errors:
            raise ValueError(f"Contraseña inválida: {', '.join(errors)}")
        return v

class RegisterResponse(BaseModel):
    message: str
    username: str

# --- Endpoints ---

# --- Endpoint de Prueba NUEVO ---
@router.get("/testauth", status_code=status.HTTP_200_OK, summary="Probar si el router Auth responde")
async def test_auth_route():
    """ Endpoint GET simple para verificar que este router está activo y responde."""
    logging.info("GET /api/auth/testauth -> Endpoint de prueba del router alcanzado!")
    return {"message": "Auth router test endpoint OK"}
# --- FIN Endpoint de Prueba ---


@router.post("/login", response_model=LoginResponse, summary="Iniciar sesión de usuario")
async def login_user(request: LoginRequest, db: mysql.connector.MySQLConnection = Depends(get_db_connection)):
    """ Valida credenciales y devuelve confirmación si son correctas."""
    cursor = None
    logging.info(f"Intento de login para usuario: {request.username}")
    try:
        cursor = db.cursor(dictionary=True)
        query = "SELECT username, password FROM users WHERE username = %s"
        cursor.execute(query, (request.username,))
        user = cursor.fetchone()

        if not user:
            logging.warning(f"Login fallido: Usuario '{request.username}' no encontrado.")
            raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

        if not verify_password(request.password, user.get('password')):
            logging.warning(f"Login fallido: Contraseña incorrecta para '{request.username}'.")
            raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

        logging.info(f"Login exitoso para usuario: {user['username']}")
        return LoginResponse(message="Login exitoso", username=user['username'])

    except mysql.connector.Error as err:
        logging.exception(f"Error de DB durante login para '{request.username}'") # Log con traceback
        raise HTTPException(status_code=500, detail="Error de base de datos al iniciar sesión.")
    except HTTPException as http_exc: # Re-lanzar excepciones HTTP para que FastAPI las maneje
         raise http_exc
    except Exception as e: # Capturar cualquier otro error inesperado
         logging.exception(f"Error inesperado durante login para '{request.username}'")
         raise HTTPException(status_code=500, detail="Error interno del servidor.")
    finally:
        if cursor: cursor.close()


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED, summary="Registrar nuevo usuario")
async def register_user(request: RegisterRequest, db: mysql.connector.MySQLConnection = Depends(get_db_connection)):
    """ Registra un nuevo usuario si el nombre no existe y la contraseña es válida."""
    cursor = None
    logging.info(f"Intento de registro para usuario: {request.username}")
    # La validación Pydantic (longitud, complejidad) ya ocurrió si llegamos aquí
    try:
        cursor = db.cursor(dictionary=True)
        check_query = "SELECT username FROM users WHERE username = %s"
        cursor.execute(check_query, (request.username,))
        if cursor.fetchone():
            logging.warning(f"Registro fallido: Usuario '{request.username}' ya existe.")
            raise HTTPException(status_code=409, detail=f"El nombre de usuario '{request.username}' ya está registrado.")

        hashed_password = get_password_hash(request.password)
        insert_query = "INSERT INTO users (username, password) VALUES (%s, %s)"
        cursor.execute(insert_query, (request.username, hashed_password))
        db.commit()
        new_user_id = cursor.lastrowid
        logging.info(f"Usuario registrado exitosamente: {request.username} (ID: {new_user_id})")
        return RegisterResponse(message="Usuario registrado exitosamente", username=request.username)

    except mysql.connector.Error as err:
        db.rollback()
        logging.exception(f"Error de DB durante registro para '{request.username}'")
        raise HTTPException(status_code=500, detail="Error interno al registrar usuario (DB).")
    except HTTPException as http_exc: # Re-lanzar excepciones HTTP (ej. 409)
         raise http_exc
    except Exception as e: # Capturar cualquier otro error inesperado
         db.rollback()
         logging.exception(f"Error inesperado durante registro para '{request.username}'")
         raise HTTPException(status_code=500, detail="Error interno del servidor.")
    finally:
        if cursor: cursor.close()