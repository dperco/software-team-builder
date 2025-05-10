import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

class DataProcessor:
    def __init__(self, data_path: str):
        self.data_path = data_path
        self.df = None
        self.embedder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        
    def load_data(self) -> pd.DataFrame:
        """Carga y limpia los datos de empleados"""
        self.df = pd.read_csv(self.data_path)
        
        # Limpieza básica
        self.df.fillna(0, inplace=True)
        
        # Convertir booleanos
        bool_cols = ['ingles_avanzado', 'lider_equipo', 'teletrabajo'] + \
                   [c for c in self.df.columns if '_principal' in c]
        for col in bool_cols:
            self.df[col] = self.df[col].astype(int)
            
        return self.df
    
    def generate_embeddings(self, save_path: str):
        """Genera embeddings para las descripciones de perfil"""
        if self.df is None:
            self.load_data()
            
        # Crear descripción combinada para cada empleado
        self.df['descripcion'] = self.df.apply(self._create_description, axis=1)
        
        # Generar embeddings
        descriptions = self.df['descripcion'].tolist()
        embeddings = self.embedder.encode(descriptions, show_progress_bar=True)
        
        # Crear índice FAISS
        index = faiss.IndexFlatIP(embeddings.shape[1])
        index.add(embeddings)
        
        # Guardar
        faiss.write_index(index, save_path)
        return index
    
    def _create_description(self, row) -> str:
        """Crea una descripción textual del perfil del empleado"""
        tech_skills = []
        for tech in ['Python', 'Java', 'JavaScript', 'React', 'Node.js']:
            if row[f"{tech}_exp"] > 0.5:
                tech_skills.append(f"{tech} (exp: {row[f'{tech}_exp']:.1f}, proyectos: {row[f'{tech}_proyectos']})")
        
        description_parts = [
            f"Perfil: {row['perfil']}",
            f"Nivel: {row['nivel']}",
            f"Experiencia: {row['anos_experiencia']} años",
            f"Tecnologías principales: {', '.join(tech_skills)}",
            f"Certificaciones: {row['certificaciones']}",
            f"Líder de equipo: {'Sí' if row['lider_equipo'] else 'No'}",
            f"Teletrabajo: {'Sí' if row['teletrabajo'] else 'No'}"
        ]
        
        return ". ".join(description_parts)