# software-team-builder/app/initialize.py
import pandas as pd
import os
import logging
import sys

# --- Añadir la raíz del proyecto a sys.path ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from config import Config # Importar Config desde la raíz del proyecto
    from app.recommendation_engine import SoftwareTeamRecommender # Desde app/recommendation_engine.py
    # from app.services.data_processing import DataProcessor # Ejemplo si lo usaras
    # from app.services.embeddings import FAISSEmbedding     # Ejemplo si lo usaras
except ImportError as e:
    print(f"ERROR [initialize.py]: Failed to import necessary modules: {e}")
    print(f"  PROJECT_ROOT: {PROJECT_ROOT}")
    print(f"  sys.path: {sys.path}")
    print(f"  Asegúrate que 'config.py' está en la raíz '{PROJECT_ROOT}'")
    print(f"  y 'recommendation_engine.py' está en '{os.path.join(PROJECT_ROOT, 'app')}'")
    sys.exit(1)

# Configuración de Logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

def main():
    logger.info(f"--- Starting Initialization Script (PROJECT_ROOT: {PROJECT_ROOT}) ---")

    # Usar rutas desde Config y PROJECT_ROOT
    models_dir_path = os.path.join(PROJECT_ROOT, Config.MODELS_SUBDIR)
    data_dir_path = os.path.join(PROJECT_ROOT, Config.DATA_SUBDIR)
    data_file_full_path = os.path.join(data_dir_path, Config.EMPLOYEE_DATA_FILE_NAME)

    os.makedirs(models_dir_path, exist_ok=True) # Crear 'models/' si no existe
    os.makedirs(data_dir_path, exist_ok=True)   # Crear 'data/' si no existe

    logger.info(f"Attempting to load data from: {data_file_full_path}")
    try:
        df_employees = pd.read_csv(data_file_full_path, delimiter=';')
        logger.info(f"Successfully loaded {len(df_employees)} rows from {Config.EMPLOYEE_DATA_FILE_NAME}")
        if df_employees.empty:
            logger.error(f"Employee data file {Config.EMPLOYEE_DATA_FILE_NAME} is empty. Cannot proceed.")
            return
    except FileNotFoundError:
        logger.error(f"Employee data file not found at: {data_file_full_path}. "
                     f"Please ensure '{Config.EMPLOYEE_DATA_FILE_NAME}' is in the '{Config.DATA_SUBDIR}' directory.")
        return
    except pd.errors.EmptyDataError:
        logger.error(f"Employee data file at {data_file_full_path} is empty or not a valid CSV.")
        return
    except Exception as e:
        logger.exception(f"An unexpected error occurred while loading data from {data_file_full_path}: {e}")
        return

    logger.info("Initializing SoftwareTeamRecommender for data preprocessing test...")
    try:
        # Esta instancia es solo para probar que el motor se puede inicializar
        # y que el preprocesamiento de datos funciona sin errores.
        test_engine = SoftwareTeamRecommender(df_employees.copy())
        logger.info("SoftwareTeamRecommender initialized and data preprocessed successfully (test).")
    except Exception as e:
        logger.exception(f"Failed to initialize or preprocess data with SoftwareTeamRecommender during test: {e}")
        # No retornar aquí necesariamente, para poder ver la sección FAISS si existe
        pass # Continuar aunque falle la inicialización del motor en el test

    # --- Sección FAISS (Si la necesitas y la tienes implementada) ---
    logger.info("--- FAISS Embeddings Section (Adapt or remove if not used) ---")
    # if 'DataProcessor' in globals() and 'FAISSEmbedding' in globals() \
    #    and hasattr(Config, 'EMBEDDINGS_FILE_NAME'): # Chequear si está en Config
    #     try:
    #         embeddings_file_name = getattr(Config, 'EMBEDDINGS_FILE_NAME', 'default_embeddings.faiss')
    #         embeddings_file_full_path = os.path.join(models_dir_path, embeddings_file_name)
    #         # ... tu lógica de DataProcessor y FAISSEmbedding ...
    #         # Asegúrate que DataProcessor también se inicialice correctamente aquí
    #         # data_processor_instance = DataProcessor(...)
    #         # faiss_instance = FAISSEmbedding(data_processor_instance, ...)
    #         # faiss_instance.create_and_save_index_if_not_exists() # Ejemplo
    #         logger.info(f"FAISS section processed (hypothetically) for: {embeddings_file_full_path}")
    #     except Exception as e:
    #         logger.exception(f"Error during FAISS embeddings processing in initialize script: {e}")
    # else:
    #     logger.info("FAISS prerequisites not met or section commented out. Skipping FAISS embeddings generation.")
    # --- Fin Sección FAISS ---

    logger.info("--- Initialization Script Completed ---")

if __name__ == "__main__":
    main()