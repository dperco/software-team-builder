import faiss
import pandas as pd
from typing import Tuple

def get_embeddings() -> Tuple[faiss.Index, pd.DataFrame]:
    """Carga los embeddings y datos de empleados"""
    embeddings_path = "models/employees.faiss"
    data_path = "data/empleados_software.csv"
    
    try:
        index = faiss.read_index(embeddings_path)
        df = pd.read_csv(data_path)
        return index, df
    except Exception as e:
        raise RuntimeError(f"Error cargando embeddings: {str(e)}")