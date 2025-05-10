
# # software-team-builder/app/recommendation_engine.py

# import pandas as pd
# import numpy as np
# from sklearn.preprocessing import MinMaxScaler
# import spacy
# import logging
# import re
# from collections import defaultdict
# from typing import Dict, List, Any, Set, Optional

# # --- Variables de Configuración (Puedes leerlas desde app.config si lo refactorizas) ---
# DEBUG_MODE = True
# STRICT_FILTER_MODE = 'principal'  # Opciones: 'principal', 'exp', 'none'
# MIN_EXP_THRESHOLD = 0.3          # Umbral para STRICT_FILTER_MODE = 'exp' (normalizado 0-1)
# NLP_MODEL_NAME = "es_core_news_sm" # Modelo de lenguaje spaCy

# # Configuración básica de Logging
# # Es mejor que la configuración global se haga en main.py o en un módulo de logging dedicado,
# # pero para asegurar que el logger funcione si este módulo se importa antes:
# logging.basicConfig(level=logging.INFO if not DEBUG_MODE else logging.DEBUG,
#                     format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
#                     datefmt='%Y-%m-%d %H:%M:%S')
# logger = logging.getLogger(__name__) # Logger específico para este módulo

# # --- Cargar Modelo spaCy (Globalmente al importar el módulo) ---
# nlp_spacy = None # Inicializar como None
# try:
#     nlp_spacy = spacy.load(NLP_MODEL_NAME)
#     logger.info(f"Modelo spaCy '{NLP_MODEL_NAME}' cargado globalmente.")
# except OSError:
#     logger.error(f"Modelo spaCy '{NLP_MODEL_NAME}' no encontrado. Descárgalo ejecutando: python -m spacy download {NLP_MODEL_NAME}")
#     logger.warning("La inferencia de tecnologías desde la descripción del proyecto estará desactivada.")
# except Exception as e:
#      logger.exception(f"Error inesperado al cargar el modelo spaCy '{NLP_MODEL_NAME}': {e}")


# class SoftwareTeamRecommender:
#     """
#     Clase principal para recomendar equipos de software basados en datos de empleados,
#     requisitos del proyecto y presupuesto. Adaptado para 'users_mindfactory.csv'.
#     """
#     def __init__(self, df_employees: pd.DataFrame):
#         """
#         Inicializa el motor de recomendación.

#         Args:
#             df_employees (pd.DataFrame): DataFrame de pandas cargado desde el CSV.
#         """
#         logger.info("Initializing SoftwareTeamRecommender...")
#         if df_employees is None or df_employees.empty:
#              logger.error("Se recibió un DataFrame vacío o None al inicializar el motor.")
#              # Levantar un error podría ser mejor para detener el proceso si los datos son esenciales.
#              raise ValueError("El DataFrame de empleados no puede estar vacío para inicializar el motor.")

#         self.nlp = nlp_spacy # Asignar el modelo global cargado a la instancia

#         # --- Definiciones y Mapeos ---
#         # Estos deben definirse ANTES de llamar a _preprocess_data si este los usa.
#         self.tech_mapping = self._initialize_tech_mapping()
#         self.reverse_tech_mapping = self._create_reverse_tech_mapping()

#         # Mapeo de Seniority (ajusta valores según sea necesario)
#         self.seniority_map = {
#             'trainee': {'anos_experiencia': 0.5, 'tech_exp_factor': 0.2, 'level_value': 1},
#             'junior': {'anos_experiencia': 1, 'tech_exp_factor': 0.4, 'level_value': 2},
#             'junior advanced': {'anos_experiencia': 2, 'tech_exp_factor': 0.5, 'level_value': 3},
#             'semi senior': {'anos_experiencia': 3, 'tech_exp_factor': 0.7, 'level_value': 4},
#             'ssr': {'anos_experiencia': 3, 'tech_exp_factor': 0.7, 'level_value': 4}, # Alias
#             'senior': {'anos_experiencia': 5, 'tech_exp_factor': 0.9, 'level_value': 5},
#             'sr': {'anos_experiencia': 5, 'tech_exp_factor': 0.9, 'level_value': 5}, # Alias
#             'expert': {'anos_experiencia': 7, 'tech_exp_factor': 0.95, 'level_value': 6}, # Si tuvieras
#             'lead': {'anos_experiencia': 6, 'tech_exp_factor': 0.9, 'level_value': 6}, # Si tuvieras
#             'project manager': {'anos_experiencia': 5, 'tech_exp_factor': 0.5, 'level_value': 5},
#             'manager': {'anos_experiencia': 7, 'tech_exp_factor': 0.4, 'level_value': 6},
#             'desconocido': {'anos_experiencia': 0, 'tech_exp_factor': 0.1, 'level_value': 0} # Valor por defecto
#         }
#         # Mapeo de Roles (ampliado basado en tu CSV)
#         self.role_keywords_map = {
#             'backend': ['backend', 'back end', 'dev. back end', 'desarrollador back', 'programador back'],
#             'frontend': ['frontend', 'front end', 'dev. font end', 'dev. front end', 'desarrollador front', 'maquetador', 'ui dev'],
#             'fullstack': ['fullstack', 'full stack', 'dev. full stack', 'desarrollador fullstack', 'desarrollador'], # "Desarrollador" genérico
#             'devops': ['devops', 'dev ops', 'sre', 'cloud engineer', 'ingeniero de infraestructura'],
#             'qa': ['qa', 'analista de calidad', 'tester', 'quality assurance', 'automation engineer', 'analista calidad (qa)'],
#             'project manager': ['project manager', 'pm', 'lider de proyecto', 'coordinador de proyecto'],
#             'analista funcional': ['analista funcional', 'functional analyst', 'analista de requerimientos'],
#             'diseñador ux/ui': ['diseñador ux/ui', 'ux designer', 'ui designer', 'diseñador ui', 'diseñador ux', 'product designer', 'ux/ui'],
#             'arquitecto': ['arquitecto', 'architect'],
#             'data scientist': ['data scientist', 'cientifico de datos', 'machine learning engineer'], # Si tuvieras
#             'scrum master': ['scrum master', 'agile coach'],
#             'rrhh': ['rrhh', 'recursos humanos', 'human resources', 'talent acquisition', 'analista rrhh', 'manager de rrhh'],
#             'marketing': ['marketing', 'comunicacion', 'community manager', 'analista de marketing'],
#             'administrativo': ['administracion', 'administrativo', 'finanzas', 'contable', 'manager administración y finananzas', 'analista administración'],
#             'ceo': ['ceo', 'director', 'gerente general'],
#             'otro': [] # Rol por defecto si no se encuentra match
#         }

#         # DataFrames para almacenar valores originales y procesados
#         self.df_employees_original_numeric_values = pd.DataFrame()
#         # Preprocesar los datos (la parte más compleja)
#         self.df_employees = self._preprocess_data(df_employees.copy()) # Trabajar con una copia

#         # Normalizar valores numéricos después del preprocesamiento
#         if not self.df_employees.empty:
#             self._normalize_numeric_values()
#             logger.info("Motor de recomendación inicializado y datos procesados.")
#             if DEBUG_MODE:
#                 logger.debug(f"Columnas finales en df_employees: {self.df_employees.columns.tolist()}")
#                 logger.debug(f"Columnas finales en df_employees_original_numeric_values: {self.df_employees_original_numeric_values.columns.tolist()}")
#         else:
#             logger.warning("El DataFrame de empleados está vacío después del preprocesamiento. El motor no funcionará correctamente.")


#     def _initialize_tech_mapping(self) -> Dict[str, List[str]]:
#         """Define el mapeo de variantes de nombres de tecnología a un nombre estándar (clave)."""
#         logger.debug("Initializing technology mapping.")
#         # Clave: nombre estándar (minúsculas, sin puntos excepto node.js), Valor: lista de variantes (minúsculas)
#         mapping = {
#             'python': ['python', 'python3'],
#             'java': ['java'],
#             'javascript': ['javascript', 'js'],
#             'react': ['react', 'react.js', 'reactjs'],
#             'react native': ['react native', 'reactnative'],
#             'angular': ['angular', 'angular.js', 'angularjs'],
#             'vue': ['vue', 'vue.js', 'vuejs'], # Corregido duplicado
#             'node.js': ['node.js', 'node', 'nodejs'],
#             'dotnetcore': ['.net core', 'dotnet core', '.netcore', 'net core'], # Añadido sin punto
#             'dotnetframework': ['.net framework', 'dotnet framework', '.netframework', 'net framework'], # Añadido sin punto
#             'csharp': ['c#', 'csharp'],
#             'mongodb': ['mongodb', 'mongo'],
#             'postgresql': ['postgresql', 'postgres', 'pgsql'],
#             'mysql': ['mysql'],
#             'sqlserver': ['sql server', 'sqlserver', 'mssql'],
#             'docker': ['docker'],
#             'kubernetes': ['kubernetes', 'k8s'],
#             'aws': ['aws', 'amazon web services'],
#             'azure': ['azure', 'microsoft azure'],
#             'gcp': ['gcp', 'google cloud platform'], # Si lo usas
#             'git': ['git'], # Si es relevante
#             'jenkins': ['jenkins'],
#             'selenium': ['selenium'],
#             'figma': ['figma'],
#             'html': ['html', 'html5'], # Se manejará 'html / css' por separado
#             'css': ['css', 'css3'],
#             'flutter': ['flutter'],
#             'typescript': ['typescript', 'ts'],
#             'db relacionales': ['db relacionales', 'sql'],
#             'uml': ['uml'], # Si es relevante
#             'mockups': ['mockups'], # Si es relevante
#             'jira': ['jira'], # Si es relevante
#             'microservicios': ['microservicios', 'microservices'],
#             'kafka': ['kafka'],
#             'spring': ['spring', 'spring boot'],
#             'ansible': ['ansible'],
#             'terraform': ['terraform'],
#             'pandas': ['pandas'], # Añadido
#             'numpy': ['numpy'],   # Añadido
#             'tensorflow': ['tensorflow', 'tf'], # Añadido
#             'pytorch': ['pytorch', 'torch'],     # Añadido
#             'scikit-learn': ['scikit-learn', 'sklearn'], # Añadido
#             # Añade más tecnologías clave que esperes encontrar o filtrar
#         }
#         # Asegurarse que 'html / css' no esté como variante aquí, se trata en el parseo
#         for k, v_list in mapping.items():
#              mapping[k] = [v for v in v_list if v != 'html / css']

#         return mapping

#     def _create_reverse_tech_mapping(self) -> Dict[str, List[str]]:
#         """Crea un mapeo inverso de variante (lower) a lista de nombres estándar."""
#         reverse_map = defaultdict(list)
#         for standard, variants in self.tech_mapping.items():
#             for variant in variants:
#                 # Limpiar variante (lower, strip) antes de añadir al mapa inverso
#                 cleaned_variant = variant.lower().strip()
#                 if cleaned_variant: # Solo añadir si no está vacío
#                     reverse_map[cleaned_variant].append(standard)
#         if DEBUG_MODE: logger.debug(f"Reverse tech mapping created with {len(reverse_map)} entries.")
#         return reverse_map

#     def _normalize_tech_name(self, tech_name: str) -> Optional[str]:
#         """
#         Normaliza un nombre de tecnología a su versión estándar definida en tech_mapping.
#         Devuelve None si la entrada no es válida o no se encuentra mapeo útil.
#         """
#         # Chequeo inicial robusto para None, no-string, o string vacío/espacios
#         if not isinstance(tech_name, str) or pd.isna(tech_name) or not tech_name.strip():
#             return None

#         tech_lower = tech_name.strip().lower()

#         # Chequeo extra por si acaso tech_lower fuera None (aunque no debería con el chequeo anterior)
#         if tech_lower is None:
#              return None

#         # Buscar en el mapeo inverso (coincidencia exacta de variante)
#         if tech_lower in self.reverse_tech_mapping:
#             # Devuelve el primer estándar si hay múltiples (ej. 'js' -> 'javascript')
#             return self.reverse_tech_mapping[tech_lower][0]

#         # Buscar si la entrada ya es una clave estándar
#         if tech_lower in self.tech_mapping:
#             return tech_lower

#         # Si no se encontró en el mapeo, decidir qué hacer:
#         # Opción 1: Devolver None para ignorar tecnologías no mapeadas.
#         # logger.debug(f"Technology '{tech_name}' (normalized to '{tech_lower}') not found in mapping. Ignoring.")
#         # return None
#         # Opción 2: Devolver la versión en minúsculas para tratarla como 'desconocida' más adelante.
#         return tech_lower # Devolvemos la versión limpia en minúsculas

#     def _get_standard_tech_col_name(self, standard_tech_name: str, suffix: str) -> str:
#         """Genera un nombre de columna consistente para una tecnología estándar."""
#         if not standard_tech_name: # Manejar caso None o vacío
#             logger.warning(f"Se intentó obtener nombre de columna para tecnología vacía con sufijo {suffix}")
#             return f"invalid_tech{suffix}" # Devolver un nombre inválido predecible
#         # Usar el nombre estándar directamente, reemplazando '.' con '_' (excepto node.js)
#         if standard_tech_name == "node.js":
#             base_name = "node.js"
#         else:
#             # Reemplazar caracteres no alfanuméricos (excepto '_') con '_' para nombres de columna seguros
#             base_name = re.sub(r'[^\w]+', '_', standard_tech_name.strip()).strip('_')
#             # Asegurar que no empiece o termine con '_' y no tenga '__' seguidos
#             base_name = re.sub(r'_+', '_', base_name).strip('_')
#         return f"{base_name}{suffix}"

#     def _map_role(self, puesto_trabajo_str: Optional[str], rol_str: Optional[str]) -> str:
#         """Intenta mapear un puesto/rol a un rol estándar definido en role_keywords_map."""
#         text_to_search = ""
#         # Priorizar 'Puesto de Trabajo', luego 'Rol'. Convertir a string y limpiar.
#         if isinstance(puesto_trabajo_str, str) and puesto_trabajo_str.strip():
#             text_to_search = puesto_trabajo_str.lower().strip()
#         elif isinstance(rol_str, str) and rol_str.strip():
#             text_to_search = rol_str.lower().strip()

#         if not text_to_search:
#             return 'desconocido' # Rol por defecto si ambos campos están vacíos

#         # Buscar coincidencia con keywords específicas primero (más preciso)
#         for standard_role, keywords in self.role_keywords_map.items():
#             if standard_role == 'otro' or standard_role == 'desconocido': continue # Saltar estos
#             for keyword in keywords:
#                 # Usar word boundaries (\b) para evitar matches parciales (ej. 'qa' en 'squad') si es necesario
#                 # O buscar simplemente si la keyword está contenida
#                 if keyword in text_to_search:
#                     # logger.debug(f"Mapeado '{text_to_search}' a '{standard_role}' usando keyword '{keyword}'")
#                     return standard_role

#         # Si no hay match con keywords, intentar match más general con las claves estándar
#         for standard_role in self.role_keywords_map.keys():
#              if standard_role == 'otro' or standard_role == 'desconocido': continue
#              if standard_role in text_to_search:
#                   # logger.debug(f"Mapeado '{text_to_search}' a '{standard_role}' usando clave estándar")
#                   return standard_role

#         # logger.debug(f"No se encontró mapeo para '{text_to_search}'. Asignando 'otro'.")
#         return 'otro' # Rol por defecto si no hay ningún match

#     def _preprocess_data(self, df: pd.DataFrame):
#         """Realiza el preprocesamiento completo de los datos de 'users_mindfactory.csv'."""
#         logger.info("Starting data preprocessing for MindFactory CSV...")

#         original_csv_columns = list(df.columns)
#         logger.debug(f"Original CSV columns: {original_csv_columns}")

#         # --- Rename columns ---
#         # Claves: Nombres EXACTOS en el CSV. Valores: Nombres internos que usaremos.
#         rename_map = {
#             'last_name': 'last_name', # Ya está en minúscula, no necesita _original si no lo usas
#             'email': 'email',
#             'Proyectos': 'project_names_raw', # Mantener mayúscula si así está en CSV
#             'Puesto de Trabajo': 'job_title_raw', # Mantener mayúsculas/espacios si así está en CSV
#             'rol': 'role_raw',
#             'tecnologías': 'technologies_raw',
#             'seniority': 'seniority_raw',
#             'Presupuesto': 'salario_original' # Mantener mayúscula si así está en CSV
#         }
#         df.rename(columns=rename_map, inplace=True, errors='ignore') # errors='ignore' si alguna columna no existe
#         current_columns_after_rename = list(df.columns)
#         logger.debug(f"DataFrame columns after attempting rename: {current_columns_after_rename}")

#         # --- Handle Missing Essential Columns (Post-Rename) ---
#         essential_cols = ['email', 'job_title_raw', 'role_raw', 'technologies_raw', 'seniority_raw', 'salario_original']
#         for col in essential_cols:
#             if col not in df.columns:
#                 logger.warning(f"Columna esencial '{col}' no encontrada después del renombrado. Se creará con valores por defecto. Verifica el CSV y rename_map.")
#                 df[col] = None # O un valor por defecto apropiado (ej. '', 0)

#         # Si last_name no está, intentar usar email como nombre completo
#         if 'last_name' not in df.columns:
#             logger.warning("Columna 'last_name' no encontrada. Usando 'email' para 'nombre_completo'.")
#             df['nombre_completo'] = df['email'].fillna('Unknown')
#         else:
#              df['nombre_completo'] = df['last_name'].fillna('Unknown') # Usar 'last_name' si existe

#         df['id'] = df.index # Usar índice como ID

#         # --- Map Role ---
#         df['rol_asignado'] = df.apply(lambda row: self._map_role(row.get('job_title_raw'), row.get('role_raw')), axis=1)
#         logger.debug(f"Unique 'rol_asignado' after mapping: {df['rol_asignado'].unique()}")

#         # --- Process Seniority ---
#         df['seniority_normalizado'] = df['seniority_raw'].astype(str).str.lower().str.strip().replace('nan','desconocido')
#         # Usar .get() en el map para manejar claves no encontradas en seniority_map
#         df['anos_experiencia'] = df['seniority_normalizado'].map(lambda s: self.seniority_map.get(s, self.seniority_map['desconocido']).get('anos_experiencia', 0))
#         df['tech_exp_factor'] = df['seniority_normalizado'].map(lambda s: self.seniority_map.get(s, self.seniority_map['desconocido']).get('tech_exp_factor', 0.1))
#         df['nivel_valor'] = df['seniority_normalizado'].map(lambda s: self.seniority_map.get(s, self.seniority_map['desconocido']).get('level_value', 0))

#         # --- Initialize Tech Columns ---
#         all_known_standard_techs = list(self.tech_mapping.keys())
#         for tech_std_name in all_known_standard_techs:
#             df[self._get_standard_tech_col_name(tech_std_name, '_exp')] = 0.0
#             df[self._get_standard_tech_col_name(tech_std_name, '_principal')] = False
#         logger.debug("Initialized tech columns (_exp, _principal) for known techs.")

#         # --- Process Technologies String ---
#         for index, row in df.iterrows():
#             tech_string = row.get('technologies_raw')
#             if pd.isna(tech_string) or not isinstance(tech_string, str) or not tech_string.strip():
#                 continue

#             listed_techs_raw = re.split(r'[;,]\s*', tech_string.strip())
#             employee_standard_techs_found = set()

#             for tech_item_raw in listed_techs_raw:
#                 tech_item_clean = tech_item_raw.strip()
#                 if not tech_item_clean: continue

#                 # Divide "Html / Css" explícitamente aquí
#                 if "html / css" in tech_item_clean.lower():
#                     potential_techs = ["html", "css"]
#                 else:
#                     normalized_single_tech = self._normalize_tech_name(tech_item_clean)
#                     potential_techs = [normalized_single_tech] if normalized_single_tech else []

#                 for normalized_tech in potential_techs:
#                     if normalized_tech and normalized_tech in self.tech_mapping:
#                         employee_standard_techs_found.add(normalized_tech)
#                         exp_col_name = self._get_standard_tech_col_name(normalized_tech, '_exp')
#                         exp_factor = row.get('tech_exp_factor', 0.1)
#                         # Asignar solo si exp_factor es numérico válido
#                         df.loc[index, exp_col_name] = exp_factor if pd.notna(exp_factor) and isinstance(exp_factor, (int, float)) else 0.1
#                         principal_col_name = self._get_standard_tech_col_name(normalized_tech, '_principal')
#                         df.loc[index, principal_col_name] = True

#             # Guardar las techs normalizadas encontradas para posible uso futuro (opcional)
#             # df.loc[index, 'processed_techs'] = ','.join(sorted(list(employee_standard_techs_found)))


#         # --- Add Missing Columns with Defaults ---
#         df['proyectos_completados_original'] = 0
#         df['certificaciones_original'] = 0
#         df['horas_capacitacion_original'] = 0
#         df['ingles_avanzado'] = False
#         df['lider_equipo'] = False

#         # --- Store Original Numeric Values ---
#         numeric_cols_for_original_storage = [
#             'salario_original', 'anos_experiencia', 'proyectos_completados_original',
#             'certificaciones_original', 'horas_capacitacion_original', 'nivel_valor'
#         ]
#         exp_cols_generated = [col for col in df.columns if col.endswith('_exp')]
#         numeric_cols_for_original_storage.extend(exp_cols_generated)

#         # Asegurar que todas las columnas existan y sean numéricas antes de copiar
#         for col in list(numeric_cols_for_original_storage): # Iterar sobre una copia de la lista
#              if col in df.columns:
#                   # Intentar convertir a numérico, rellenar NaN con 0
#                   df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
#                   # Si después de convertir, la columna no es numérica, quitarla de la lista para evitar errores
#                   if not pd.api.types.is_numeric_dtype(df[col]):
#                       logger.warning(f"Columna '{col}' no es numérica después de conversión. Excluyendo de originales.")
#                       numeric_cols_for_original_storage.remove(col)
#              else:
#                   logger.warning(f"Columna '{col}' no encontrada en DataFrame. Excluyendo de originales.")
#                   numeric_cols_for_original_storage.remove(col) # Quitarla si no existe

#         # Copiar solo las columnas válidas y existentes
#         self.df_employees_original_numeric_values = df[numeric_cols_for_original_storage].copy()
#         # Renombrar para la salida JSON
#         self.df_employees_original_numeric_values.rename(columns={
#             'salario_original': 'salario',
#             'proyectos_completados_original': 'proyectos_completados',
#             'certificaciones_original': 'certificaciones',
#             'horas_capacitacion_original': 'horas_capacitacion',
#         }, inplace=True, errors='ignore')

#         # --- Prepare columns for Normalization ---
#         # Renombrar columnas en el DF principal que serán normalizadas
#         df.rename(columns={
#             'proyectos_completados_original': 'proyectos_completados_norm',
#             'certificaciones_original': 'certificaciones_norm',
#             'horas_capacitacion_original': 'horas_capacitacion_norm',
#             'salario_original': 'salario_norm' # Renombrar para normalización
#         }, inplace=True, errors='ignore')

#         # --- Drop Raw/Temporary Columns ---
#         # Guardar copias de columnas que quieres mantener en la salida final antes de dropearlas
#         # Ejemplo: guardar 'job_title_raw' y 'seniority_raw' si los quieres en el MemberResponse final
#         if 'job_title_raw' in df.columns: df['job_title_raw_bkp'] = df['job_title_raw']
#         if 'seniority_raw' in df.columns: df['seniority_raw_bkp'] = df['seniority_raw']

#         cols_to_drop = ['job_title_raw', 'role_raw', 'technologies_raw', 'seniority_raw',
#                         'project_names_raw', 'tech_exp_factor'] # Quitar last_name_original si no existe o no se necesita
#         df.drop(columns=[col for col in cols_to_drop if col in df.columns], inplace=True, errors='ignore')

#         logger.info("Data preprocessing finished.")
#         return df

#     def _normalize_numeric_values(self):
#         """Normaliza columnas numéricas seleccionadas usando MinMaxScaler."""
#         if self.df_employees.empty:
#             logger.warning("Employee DataFrame empty. Skipping normalization.")
#             return

#         # Columnas destinadas a normalización (deben existir después de _preprocess_data)
#         cols_to_normalize = ['salario_norm', 'anos_experiencia', 'proyectos_completados_norm',
#                              'certificaciones_norm', 'horas_capacitacion_norm', 'nivel_valor']
#         exp_cols = [col for col in self.df_employees.columns if col.endswith('_exp')]
#         cols_to_normalize.extend(exp_cols)

#         # Filtrar solo las que realmente existen y son numéricas en el DataFrame actual
#         valid_cols_to_normalize = [
#             col for col in cols_to_normalize
#             if col in self.df_employees.columns and pd.api.types.is_numeric_dtype(self.df_employees[col])
#         ]

#         if not valid_cols_to_normalize:
#             logger.warning("No valid numeric columns found for normalization.")
#             return

#         logger.info(f"Normalizing {len(valid_cols_to_normalize)} columns: {valid_cols_to_normalize}")
#         # Crear subset, asegurando que no haya NaNs (ya deberían estar en 0 por _preprocess_data)
#         df_to_normalize_subset = self.df_employees[valid_cols_to_normalize].copy().fillna(0)

#         scaler = MinMaxScaler()
#         try:
#             # Escalar los datos
#             normalized_values = scaler.fit_transform(df_to_normalize_subset)
#             # Crear DataFrame temporal con valores escalados
#             df_normalized_subset = pd.DataFrame(normalized_values, columns=valid_cols_to_normalize, index=self.df_employees.index)
#             # Actualizar las columnas en el DataFrame principal
#             for col in valid_cols_to_normalize:
#                 self.df_employees[col] = df_normalized_subset[col]
#             logger.info("Normalization completed successfully.")
#             if DEBUG_MODE:
#                 logger.debug(f"Sample normalized data:\n{self.df_employees[valid_cols_to_normalize].head()}")
#         except Exception as e:
#             logger.exception(f"Error during MinMaxScaling for columns {valid_cols_to_normalize}: {e}")


#     def _infer_techs_from_description(self, description: str) -> Set[str]:
#         """Infiere tecnologías normalizadas desde la descripción del proyecto usando spaCy."""
#         if not self.nlp or not isinstance(description, str) or not description.strip():
#             return set()
#         inferred_techs = set()
#         try:
#             doc = self.nlp(description.lower())
#             # Estrategia combinada: Entidades + Tokens relevantes (Nombres/Sustantivos Propios)
#             potential_texts = set()
#             for ent in doc.ents:
#                 # Ajustar etiquetas según los modelos de spaCy y lo que funcione mejor
#                 if ent.label_ in ["ORG", "PRODUCT", "TECH", "LANGUAGE", "WORK_OF_ART", "PERSON"]: # PERSON a veces captura nombres (Java)
#                      potential_texts.add(ent.text)
#             for token in doc:
#                 if token.pos_ in ["NOUN", "PROPN"] and not token.is_stop and len(token.text) > 1:
#                     potential_texts.add(token.lemma_ if token.lemma_ != "-PRON-" and len(token.lemma_)>1 else token.text)

#             # Normalizar los textos potenciales
#             for text in potential_texts:
#                 norm_tech = self._normalize_tech_name(text)
#                 # Solo añadir si se normalizó a una tecnología conocida en nuestro mapeo
#                 if norm_tech and norm_tech in self.tech_mapping:
#                     inferred_techs.add(norm_tech)

#         except Exception as e:
#             logger.exception(f"Error durante el procesamiento NLP de la descripción: {e}")

#         logger.info(f"NLP inferred standard techs from description: {inferred_techs}")
#         return inferred_techs


#     def calculate_score(self, row: pd.Series, required_techs_for_role: Set[str], all_project_techs: Set[str]) -> float:
#         """Calcula la puntuación de relevancia para un candidato dado los requisitos."""
#         # Los valores base (anos_experiencia, nivel_valor) y _exp ya están normalizados (0-1)
#         tech_score, exp_score = 0.0, 0.0
#         candidate_id = row.get('id', 'N/A')

#         # 1. Score por Tecnologías
#         tech_found_for_role_count = 0
#         all_relevant_techs = required_techs_for_role.union(all_project_techs)

#         for tech_std_name in all_relevant_techs:
#             exp_col = self._get_standard_tech_col_name(tech_std_name, '_exp')
#             exp_value = row.get(exp_col, 0.0) # Obtener valor de experiencia normalizado

#             if exp_value > 0: # Si el empleado tiene esta tecnología
#                 principal_col = self._get_standard_tech_col_name(tech_std_name, '_principal')
#                 is_principal = row.get(principal_col, False)

#                 # Ponderación base por tener la tecnología (basada en su exp normalizada)
#                 contribution = exp_value

#                 # Bonus si es principal
#                 if is_principal:
#                     contribution *= 1.5

#                 # Bonus mayor si es una tecnología requerida para ESE ROL
#                 if tech_std_name in required_techs_for_role:
#                     contribution *= 2.0 # Doble peso si es requerida para el rol
#                     tech_found_for_role_count += 1
#                 # Bonus menor si es requerida para el proyecto en general (pero no específica del rol)
#                 elif tech_std_name in all_project_techs:
#                      contribution *= 1.0 # Peso normal si es del proyecto general

#                 tech_score += contribution

#         # Penalización si no cumple NINGUNA tecnología requerida para el ROL (si no fue filtrado)
#         if required_techs_for_role and tech_found_for_role_count == 0 and STRICT_FILTER_MODE != 'none':
#              logger.debug(f"ID {candidate_id}: Penalizando score por no cumplir techs requeridas del rol {required_techs_for_role}")
#              tech_score -= 50 # Penalización fuerte

#         # 2. Score por Experiencia General
#         # Usar los valores normalizados directamente
#         exp_score += row.get('anos_experiencia', 0.0) * 5.0 # Peso para años de exp
#         exp_score += row.get('nivel_valor', 0.0) * 2.0      # Peso para nivel/seniority

#         # 3. Ponderación Final (Ajustar según importancia relativa deseada)
#         # Dar más peso a las tecnologías relevantes, luego a la experiencia
#         total_score = (tech_score * 0.70) + (exp_score * 0.30)

#         if DEBUG_MODE:
#              logger.debug(f"Score Calc ID {candidate_id} ({row.get('rol_asignado','N/A')}): TechScore(raw)={tech_score:.2f}, ExpScore(raw)={exp_score:.2f} -> TOTAL SCORE = {total_score:.3f}")

#         # Asegurar que el score no sea NaN o infinito
#         return total_score if pd.notna(total_score) and np.isfinite(total_score) else 0.0


#     def recommend_team(self, project_description: str, team_structure: Dict[str, int], budget: float, explicit_technologies_by_role: Optional[Dict[str, List[str]]]) -> Dict[str, Any]:
#         """
#         Orquesta el proceso completo de recomendación de equipo.
#         """
#         if self.df_employees is None or self.df_employees.empty:
#             logger.error("No hay datos de empleados cargados o procesados. No se puede recomendar.")
#             # Devuelve una estructura de respuesta válida pero vacía/indicando error
#             return {
#                 "equipo": [], "presupuesto": {"total": float(budget), "utilizado": 0.0, "restante": float(budget), "porcentaje_utilizado": 0.0},
#                 "metricas": {"promedio_puntaje": 0.0, "tecnologias_faltantes": [], "roles_cubiertos": {}, "roles_solicitados": team_structure},
#                 "analisis_equipo": "Error: No hay datos de empleados disponibles.", "status_message": "Error: Datos no disponibles.", "inferred_project_technologies": []
#             }

#         logger.info(f"Starting team recommendation process. Budget: {budget:.0f}")
#         logger.debug(f"Requested Structure: {team_structure}")
#         logger.debug(f"Explicit Techs by Role: {explicit_technologies_by_role}")

#         # 1. Inferir y Combinar Tecnologías
#         inferred_standard_techs = self._infer_techs_from_description(project_description)
#         all_project_techs_standard = set(inferred_standard_techs)
#         final_techs_for_role_filter = defaultdict(set) # Techs explícitas por rol para filtro/score específico

#         # Procesar tecnologías explícitas
#         if explicit_technologies_by_role:
#              for role_key, techs_list in explicit_technologies_by_role.items():
#                   role_norm_ui = role_key.lower().strip()
#                   current_role_explicit_std_techs = {
#                        norm_t for tech_raw in techs_list
#                        if (norm_t := self._normalize_tech_name(tech_raw)) and norm_t in self.tech_mapping
#                   }
#                   final_techs_for_role_filter[role_norm_ui].update(current_role_explicit_std_techs)
#                   all_project_techs_standard.update(current_role_explicit_std_techs) # Añadir al pool general
#         logger.info(f"All project standard technologies (explicit + inferred): {all_project_techs_standard}")


#         # 2. Filtrar y Puntuar Candidatos por Rol
#         all_candidate_rows_for_selection = []
#         processed_ids = set() # Para evitar duplicados si una persona pudiera calificar para >1 rol

#         for role_from_structure, count_needed in team_structure.items():
#             role_normalized_struct = role_from_structure.lower().strip()
#             if count_needed <= 0: continue # Saltar si no se necesitan miembros para este rol

#             logger.info(f"Processing role: '{role_normalized_struct}', need {count_needed} members.")
#             candidates_for_role_df = self.df_employees[self.df_employees['rol_asignado'] == role_normalized_struct].copy()
#             if candidates_for_role_df.empty:
#                  logger.warning(f"No candidates initially found for role: {role_normalized_struct}.")
#                  continue

#             # Aplicar Filtro Estricto (basado en las techs explícitas para ESTE rol)
#             current_role_filter_techs = final_techs_for_role_filter.get(role_normalized_struct, set())
#             if STRICT_FILTER_MODE != 'none' and current_role_filter_techs:
#                 logger.info(f"Applying strict filter '{STRICT_FILTER_MODE}' for role '{role_normalized_struct}' with techs: {current_role_filter_techs}")
#                 conditions = []
#                 for tech_std_name in current_role_filter_techs:
#                     if STRICT_FILTER_MODE == 'principal':
#                         col_name = self._get_standard_tech_col_name(tech_std_name, '_principal')
#                         if col_name in candidates_for_role_df.columns: conditions.append(f"`{col_name}` == True")
#                     elif STRICT_FILTER_MODE == 'exp':
#                         col_name = self._get_standard_tech_col_name(tech_std_name, '_exp')
#                         if col_name in candidates_for_role_df.columns: conditions.append(f"`{col_name}` >= {MIN_EXP_THRESHOLD}")
#                 if conditions:
#                     query_str = " or ".join(conditions)
#                     try:
#                         original_len = len(candidates_for_role_df)
#                         candidates_for_role_df.query(query_str, inplace=True)
#                         logger.info(f"Candidates for role '{role_normalized_struct}' after strict filter: {len(candidates_for_role_df)}/{original_len}")
#                     except Exception as e: logger.error(f"Error applying strict filter query: {e}. Query: {query_str}")
#             if candidates_for_role_df.empty:
#                 logger.warning(f"No candidates remain for role '{role_normalized_struct}' after filters.")
#                 continue

#             # Calcular Score (pasa techs explícitas del rol y todas las del proyecto)
#             candidates_for_role_df['score'] = candidates_for_role_df.apply(
#                 lambda r: self.calculate_score(r, current_role_filter_techs, all_project_techs_standard), axis=1
#             )

#             # Añadir Salario Original para ordenar y seleccionar
#             # Unir de forma segura usando el índice
#             candidates_for_role_df = candidates_for_role_df.join(
#                  self.df_employees_original_numeric_values[['salario']], # Selecciona solo la columna 'salario'
#                  how='left' # Left join para mantener todos los candidatos
#             )
#             # Renombrar la columna unida para claridad
#             candidates_for_role_df.rename(columns={'salario': 'salario_para_sort'}, inplace=True)
#             candidates_for_role_df['salario_para_sort'].fillna(0, inplace=True) # Rellenar NaNs si la unión falló para algún índice


#             # Ordenar y seleccionar candidatos para la lista global
#             sorted_candidates_df = candidates_for_role_df.sort_values(
#                 by=['score', 'salario_para_sort'], ascending=[False, True]
#             )
#             for idx, cand_row_series in sorted_candidates_df.iterrows():
#                  member_id = int(cand_row_series['id'])
#                  if member_id in processed_ids: continue # Evitar duplicados

#                  original_values_cand = self.df_employees_original_numeric_values.loc[idx]
#                  # Recuperar valores originales guardados antes del drop en _preprocess_data
#                  job_title_original = cand_row_series.get('job_title_raw_bkp', 'N/A')
#                  seniority_original_val = cand_row_series.get('seniority_raw_bkp', 'N/A')

#                  member_data = {
#                     'id': member_id,
#                     'nombre': cand_row_series.get('nombre_completo', 'N/A'),
#                     'email': cand_row_series.get('email', 'N/A'),
#                     'puesto_original': job_title_original,
#                     'rol_asignado': cand_row_series['rol_asignado'],
#                     'rol_asignado_display': cand_row_series['rol_asignado'].replace('_', ' ').title(),
#                     'seniority_original': seniority_original_val,
#                     'seniority_normalizado': cand_row_series.get('seniority_normalizado', 'N/A'),
#                     'anos_experiencia': int(original_values_cand.get('anos_experiencia', 0)),
#                     'proyectos_completados': int(original_values_cand.get('proyectos_completados', 0)), # Será 0
#                     'salario': int(original_values_cand.get('salario', 0)), # Salario REAL
#                     'score': round(cand_row_series['score'], 4), # Más decimales si se quiere
#                     'tecnologias_conocidas': [],
#                     'nivel_valor_original': int(original_values_cand.get('nivel_valor',0)),
#                  }
#                  known_techs_for_member_std = {
#                       tech_std for tech_std in self.tech_mapping
#                       if cand_row_series.get(self._get_standard_tech_col_name(tech_std, '_exp'), 0) > 0 # Umbral bajo aquí
#                  }
#                  member_data['tecnologias_conocidas'] = sorted([
#                       self.tech_mapping[std_tech][0].replace('.', ' ').title() # Nombre legible
#                       for std_tech in known_techs_for_member_std
#                  ])
#                  all_candidate_rows_for_selection.append(member_data)
#                  processed_ids.add(member_id) # Marcar como procesado

#         # 3. Selección Final (Presupuesto y Estructura)
#         if not all_candidate_rows_for_selection:
#             logger.warning("No suitable candidates found for any role after processing all roles.")
#             return {
#                  "equipo": [], "presupuesto": {"total": float(budget), "utilizado": 0.0, "restante": float(budget), "porcentaje_utilizado": 0.0},
#                  "metricas": {"promedio_puntaje": 0.0, "tecnologias_faltantes": sorted(list(all_project_techs_standard)), "roles_cubiertos": {}, "roles_solicitados": team_structure},
#                  "analisis_equipo": "No se encontraron candidatos adecuados para los roles solicitados.", "status_message": "No se encontraron candidatos.", "inferred_project_technologies": sorted(list(inferred_standard_techs))
#             }

#         # Ordenar la lista global por score (desc) y salario (asc)
#         all_candidate_rows_for_selection.sort(key=lambda x: (-x['score'], x['salario']))

#         final_team = []
#         current_budget_spent = 0.0
#         roles_filled_count = {role_key.lower().strip(): 0 for role_key in team_structure.keys()}
#         target_roles_to_fill_count = {role_key.lower().strip(): count for role_key, count in team_structure.items() if count > 0} # Solo roles con count > 0
#         selected_member_ids_final = set()
#         total_roles_needed_overall = sum(target_roles_to_fill_count.values())

#         logger.info(f"Starting final selection from {len(all_candidate_rows_for_selection)} pre-selected candidates.")

#         for candidate_dict in all_candidate_rows_for_selection:
#             # Si ya hemos llenado todos los puestos, podemos parar
#             if sum(roles_filled_count.values()) >= total_roles_needed_overall:
#                 logger.info("All requested roles filled. Stopping selection.")
#                 break

#             candidate_role_assigned = candidate_dict['rol_asignado']
#             candidate_id = candidate_dict['id']
#             candidate_salary = float(candidate_dict['salario']) # Asegurar float

#             # Verificar si el rol de este candidato es uno que necesitamos llenar
#             if candidate_role_assigned in target_roles_to_fill_count:
#                 # Verificar si aún necesitamos llenar puestos para este rol
#                 if roles_filled_count.get(candidate_role_assigned, 0) < target_roles_to_fill_count[candidate_role_assigned]:
#                     # Verificar si no ha sido seleccionado ya
#                     if candidate_id not in selected_member_ids_final:
#                         # Verificar si entra en el presupuesto
#                         if (current_budget_spent + candidate_salary) <= budget:
#                             final_team.append(candidate_dict)
#                             current_budget_spent += candidate_salary
#                             roles_filled_count[candidate_role_assigned] += 1
#                             selected_member_ids_final.add(candidate_id)
#                             # logger.debug(f"Selected: {candidate_dict['nombre']} for role {candidate_role_assigned} (Score: {candidate_dict['score']:.2f}, Salario: {candidate_salary:.0f}). Budget left: {budget - current_budget_spent:.0f}")
#                         # else: logger.debug(f"Skipped (budget): {candidate_dict['nombre']} for {candidate_role_assigned} (Sal: {candidate_salary:.0f})")
#                     # else: logger.debug(f"Skipped (already selected): {candidate_dict['nombre']}")
#                 # else: logger.debug(f"Skipped (role full): {candidate_dict['nombre']} for {candidate_role_assigned}")
#             # else: logger.debug(f"Skipped (role not needed): {candidate_dict['nombre']} for {candidate_role_assigned}")

#         # 4. Preparar Respuesta Final
#         budget_remaining = budget - current_budget_spent
#         status_message = "Team successfully generated."
#         if not final_team and total_roles_needed_overall > 0:
#             status_message = "Could not form a team meeting the criteria and budget."
#         elif sum(roles_filled_count.values()) < total_roles_needed_overall:
#             status_message = "Team partially formed. Not all requested roles could be filled due to budget or candidate availability."
#             # Loguear roles faltantes
#             for r, needed in target_roles_to_fill_count.items():
#                 filled = roles_filled_count.get(r, 0)
#                 if filled < needed:
#                      logger.warning(f"Role '{r}' not fully filled: needed {needed}, got {filled}")

#         # Calcular tecnologías faltantes (opcional pero útil)
#         team_techs_set = set()
#         for member in final_team:
#             # Usar las techs normalizadas (claves del mapping) para la comparación
#             for tech_name in member['tecnologias_conocidas']:
#                  norm_tech = self._normalize_tech_name(tech_name)
#                  if norm_tech: team_techs_set.add(norm_tech)
#         missing_techs = sorted(list(all_project_techs_standard - team_techs_set))

#         logger.info(f"Recommendation process finished. Final team size: {len(final_team)}. Budget Spent: {current_budget_spent:.2f}. Status: {status_message}")

#         response_payload = {
#             "equipo": final_team,
#             "presupuesto": {
#                 "total": float(budget),
#                 "utilizado": float(current_budget_spent),
#                 "restante": float(budget_remaining),
#                 "porcentaje_utilizado": (current_budget_spent / budget) if budget > 0 else 0.0
#             },
#             "metricas": {
#                 "promedio_puntaje": np.mean([m['score'] for m in final_team]).item() if final_team else 0.0, # .item() para convertir de numpy.float64
#                 "tecnologias_faltantes": missing_techs,
#                 "roles_cubiertos": roles_filled_count,
#                 "roles_solicitados": target_roles_to_fill_count # Usar el target real
#             },
#             "analisis_equipo": status_message, # Usar el status como análisis general
#             "status_message": status_message, # Mantener por compatibilidad
#             "inferred_project_technologies": sorted(list(inferred_standard_techs))
#         }

#         return response_payload   

# software-team-builder/app/recommendation_engine.py

import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import spacy
import logging
import re
from collections import defaultdict
from typing import Dict, List, Any, Set, Optional

# --- Variables de Configuración (Puedes leerlas desde app.config si lo refactorizas) ---
# Asegúrate que estos valores sean los que quieres o léelos desde Config
DEBUG_MODE = True
STRICT_FILTER_MODE = 'principal'  # Opciones: 'principal', 'exp', 'none'
MIN_EXP_THRESHOLD = 0.3          # Umbral para STRICT_FILTER_MODE = 'exp' (normalizado 0-1)
NLP_MODEL_NAME = "es_core_news_sm" # Modelo de lenguaje spaCy

# Configuración básica de Logging
logging.basicConfig(level=logging.INFO if not DEBUG_MODE else logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__) # Logger específico para este módulo

# --- Cargar Modelo spaCy (Globalmente al importar el módulo) ---
nlp_spacy = None # Inicializar como None
try:
    nlp_spacy = spacy.load(NLP_MODEL_NAME)
    logger.info(f"Modelo spaCy '{NLP_MODEL_NAME}' cargado globalmente.")
except OSError:
    logger.error(f"Modelo spaCy '{NLP_MODEL_NAME}' no encontrado. Descárgalo ejecutando: python -m spacy download {NLP_MODEL_NAME}")
    logger.warning("La inferencia de tecnologías desde la descripción del proyecto estará desactivada.")
except Exception as e:
     logger.exception(f"Error inesperado al cargar el modelo spaCy '{NLP_MODEL_NAME}': {e}")


class SoftwareTeamRecommender:
    """
    Clase principal para recomendar equipos de software basados en datos de empleados,
    requisitos del proyecto y presupuesto. Adaptado para 'users_mindfactory.csv'.
    """
    def __init__(self, df_employees: pd.DataFrame):
        """
        Inicializa el motor de recomendación.

        Args:
            df_employees (pd.DataFrame): DataFrame de pandas cargado desde el CSV.
        """
        logger.info("Initializing SoftwareTeamRecommender...")
        if df_employees is None or df_employees.empty:
             logger.error("Se recibió un DataFrame vacío o None al inicializar el motor.")
             raise ValueError("El DataFrame de empleados no puede estar vacío para inicializar el motor.")

        self.nlp = nlp_spacy # Asignar el modelo global cargado a la instancia

        # --- Definiciones y Mapeos ---
        self.tech_mapping = self._initialize_tech_mapping()
        self.reverse_tech_mapping = self._create_reverse_tech_mapping()
        self.seniority_map = {
            'trainee': {'anos_experiencia': 0.5, 'tech_exp_factor': 0.2, 'level_value': 1},
            'junior': {'anos_experiencia': 1, 'tech_exp_factor': 0.4, 'level_value': 2},
            'junior advanced': {'anos_experiencia': 2, 'tech_exp_factor': 0.5, 'level_value': 3},
            'semi senior': {'anos_experiencia': 3, 'tech_exp_factor': 0.7, 'level_value': 4},
            'ssr': {'anos_experiencia': 3, 'tech_exp_factor': 0.7, 'level_value': 4},
            'senior': {'anos_experiencia': 5, 'tech_exp_factor': 0.9, 'level_value': 5},
            'sr': {'anos_experiencia': 5, 'tech_exp_factor': 0.9, 'level_value': 5},
            'expert': {'anos_experiencia': 7, 'tech_exp_factor': 0.95, 'level_value': 6},
            'lead': {'anos_experiencia': 6, 'tech_exp_factor': 0.9, 'level_value': 6},
            'project manager': {'anos_experiencia': 5, 'tech_exp_factor': 0.5, 'level_value': 5},
            'manager': {'anos_experiencia': 7, 'tech_exp_factor': 0.4, 'level_value': 6},
            'desconocido': {'anos_experiencia': 0, 'tech_exp_factor': 0.1, 'level_value': 0}
        }
        self.role_keywords_map = {
            'backend': ['backend', 'back end', 'dev. back end', 'desarrollador back', 'programador back'],
            'frontend': ['frontend', 'front end', 'dev. font end', 'dev. front end', 'desarrollador front', 'maquetador', 'ui dev'],
            'fullstack': ['fullstack', 'full stack', 'dev. full stack', 'desarrollador fullstack', 'desarrollador'],
            'devops': ['devops', 'dev ops', 'sre', 'cloud engineer', 'ingeniero de infraestructura'],
            'qa': ['qa', 'analista de calidad', 'tester', 'quality assurance', 'automation engineer', 'analista calidad (qa)'],
            'project manager': ['project manager', 'pm', 'lider de proyecto', 'coordinador de proyecto'],
            'analista funcional': ['analista funcional', 'functional analyst', 'analista de requerimientos'],
            'diseñador ux/ui': ['diseñador ux/ui', 'ux designer', 'ui designer', 'diseñador ui', 'diseñador ux', 'product designer', 'ux/ui'],
            'arquitecto': ['arquitecto', 'architect'],
            'data scientist': ['data scientist', 'cientifico de datos', 'machine learning engineer'],
            'scrum master': ['scrum master', 'agile coach'],
            'rrhh': ['rrhh', 'recursos humanos', 'human resources', 'talent acquisition', 'analista rrhh', 'manager de rrhh'],
            'marketing': ['marketing', 'comunicacion', 'community manager', 'analista de marketing'],
            'administrativo': ['administracion', 'administrativo', 'finanzas', 'contable', 'manager administración y finananzas', 'analista administración'],
            'ceo': ['ceo', 'director', 'gerente general'],
            'otro': []
        }

        # DataFrames para almacenar valores originales y procesados
        self.df_employees_original_numeric_values = pd.DataFrame()
        # Preprocesar los datos
        self.df_employees = self._preprocess_data(df_employees.copy()) # Trabajar con una copia

        # Normalizar valores numéricos después del preprocesamiento
        if not self.df_employees.empty:
            self._normalize_numeric_values()
            logger.info("Motor de recomendación inicializado y datos procesados.")
            if DEBUG_MODE:
                logger.debug(f"Columnas finales en df_employees: {self.df_employees.columns.tolist()}")
                logger.debug(f"Columnas finales en df_employees_original_numeric_values: {self.df_employees_original_numeric_values.columns.tolist()}")
        else:
            logger.warning("El DataFrame de empleados está vacío después del preprocesamiento.")


    def _initialize_tech_mapping(self) -> Dict[str, List[str]]:
        """Define el mapeo de variantes de nombres de tecnología a un nombre estándar (clave)."""
        logger.debug("Initializing technology mapping.")
        mapping = {
            'python': ['python', 'python3'], 'java': ['java'], 'javascript': ['javascript', 'js'],
            'react': ['react', 'react.js', 'reactjs'], 'react native': ['react native', 'reactnative'],
            'angular': ['angular', 'angular.js', 'angularjs'], 'vue': ['vue', 'vue.js', 'vuejs'],
            'node.js': ['node.js', 'node', 'nodejs'], 'dotnetcore': ['.net core', 'dotnet core', '.netcore', 'net core'],
            'dotnetframework': ['.net framework', 'dotnet framework', '.netframework', 'net framework'], 'csharp': ['c#', 'csharp'],
            'mongodb': ['mongodb', 'mongo'], 'postgresql': ['postgresql', 'postgres', 'pgsql'], 'mysql': ['mysql'],
            'sqlserver': ['sql server', 'sqlserver', 'mssql'], 'docker': ['docker'], 'kubernetes': ['kubernetes', 'k8s'],
            'aws': ['aws', 'amazon web services'], 'azure': ['azure', 'microsoft azure'], 'gcp': ['gcp', 'google cloud platform'],
            'git': ['git'], 'jenkins': ['jenkins'], 'selenium': ['selenium'], 'figma': ['figma'],
            'html': ['html', 'html5'], 'css': ['css', 'css3'], 'flutter': ['flutter'],
            'typescript': ['typescript', 'ts'], 'db relacionales': ['db relacionales', 'sql', 'db relacionales'],
            'uml': ['uml'], 'mockups': ['mockups'], 'jira': ['jira'], 'microservicios': ['microservicios', 'microservices'],
            'kafka': ['kafka'], 'spring': ['spring', 'spring boot'], 'ansible': ['ansible'], 'terraform': ['terraform'],
            'pandas': ['pandas'], 'numpy': ['numpy'], 'tensorflow': ['tensorflow', 'tf'],
            'pytorch': ['pytorch', 'torch'], 'scikit-learn': ['scikit-learn', 'sklearn'],
        }
        for k, v_list in mapping.items():
             mapping[k] = [v for v in v_list if v != 'html / css']
        return mapping

    def _create_reverse_tech_mapping(self) -> Dict[str, List[str]]:
        """Crea un mapeo inverso de variante (lower) a lista de nombres estándar."""
        reverse_map = defaultdict(list)
        for standard, variants in self.tech_mapping.items():
            for variant in variants:
                cleaned_variant = variant.lower().strip()
                if cleaned_variant:
                    reverse_map[cleaned_variant].append(standard)
        if DEBUG_MODE: logger.debug(f"Reverse tech mapping created with {len(reverse_map)} entries.")
        return reverse_map

    def _normalize_tech_name(self, tech_name: str) -> Optional[str]:
        """Normaliza un nombre de tecnología. Devuelve estándar, lower, o None."""
        if not isinstance(tech_name, str) or pd.isna(tech_name) or not tech_name.strip():
            return None # Devolver None si no es string válido
        tech_lower = tech_name.strip().lower()
        if tech_lower is None: return None # Chequeo extra

        if tech_lower in self.reverse_tech_mapping:
            return self.reverse_tech_mapping[tech_lower][0]
        if tech_lower in self.tech_mapping:
            return tech_lower
        return tech_lower # Devuelve lowercased si no está en el mapeo

    def _get_standard_tech_col_name(self, standard_tech_name: str, suffix: str) -> str:
        """Genera un nombre de columna seguro para una tecnología estándar."""
        if not standard_tech_name:
            logger.warning(f"Intentando obtener nombre de columna para tech vacía con sufijo {suffix}")
            return f"invalid_tech{suffix}"
        if standard_tech_name == "node.js": base_name = "node.js"
        else:
            base_name = re.sub(r'[^\w]+', '_', standard_tech_name.strip()).strip('_')
            base_name = re.sub(r'_+', '_', base_name).strip('_')
        return f"{base_name}{suffix}"

    def _map_role(self, puesto_trabajo_str: Optional[str], rol_str: Optional[str]) -> str:
        """Mapea puesto/rol a un rol estándar."""
        text_to_search = ""
        if isinstance(puesto_trabajo_str, str) and puesto_trabajo_str.strip():
            text_to_search = puesto_trabajo_str.lower().strip()
        elif isinstance(rol_str, str) and rol_str.strip():
            text_to_search = rol_str.lower().strip()
        if not text_to_search: return 'desconocido'
        for standard_role, keywords in self.role_keywords_map.items():
            if standard_role in ['otro', 'desconocido']: continue
            for keyword in keywords:
                if keyword in text_to_search: return standard_role
        for standard_role in self.role_keywords_map.keys():
            if standard_role in ['otro', 'desconocido']: continue
            if standard_role in text_to_search: return standard_role
        return 'otro'

    def _preprocess_data(self, df: pd.DataFrame):
        """Realiza el preprocesamiento completo de los datos de 'users_mindfactory.csv'."""
        logger.info("Starting data preprocessing for MindFactory CSV...")
        original_csv_columns = list(df.columns)
        logger.debug(f"Original CSV columns: {original_csv_columns}")

        # --- Rename columns (Asegúrate que las CLAVES coincidan con tu CSV) ---
        rename_map = {
            'last_name': 'last_name',           # CSV tiene 'last_name'
            'email': 'email',                   # CSV tiene 'email'
            'Proyectos': 'project_names_raw',   # CSV tiene 'Proyectos'
            'Puesto de Trabajo': 'job_title_raw',# CSV tiene 'Puesto de Trabajo'
            'rol': 'role_raw',                  # CSV tiene 'rol'
            'tecnologías': 'technologies_raw',    # CSV tiene 'tecnologías'
            'seniority': 'seniority_raw',         # CSV tiene 'seniority'
            'Presupuesto': 'salario_original'   # CSV tiene 'Presupuesto'
        }
        df.rename(columns=rename_map, inplace=True, errors='raise') # 'raise' para ver si falla el rename
        current_columns_after_rename = list(df.columns)
        logger.debug(f"DataFrame columns after attempting rename: {current_columns_after_rename}")

        # --- Handle Missing Essential Columns & Create nombre_completo ---
        essential_cols = ['email', 'job_title_raw', 'role_raw', 'technologies_raw', 'seniority_raw', 'salario_original']
        for col in essential_cols:
            if col not in df.columns:
                logger.error(f"Columna esencial '{col}' NO encontrada después del renombrado. Verifica CSV y rename_map. Saliendo.")
                raise ValueError(f"Columna esencial faltante: {col}")
        if 'last_name' not in df.columns:
            logger.warning("Columna 'last_name' no encontrada. Usando 'email' para 'nombre_completo'.")
            df['nombre_completo'] = df['email'].fillna('Unknown')
        else:
             df['nombre_completo'] = df['last_name'].fillna('Unknown')
        df['id'] = df.index

        # --- Map Role ---
        df['rol_asignado'] = df.apply(lambda row: self._map_role(row.get('job_title_raw'), row.get('role_raw')), axis=1)
        logger.debug(f"Unique 'rol_asignado' after mapping: {df['rol_asignado'].unique()}")

        # --- Process Seniority ---
        df['seniority_normalizado'] = df['seniority_raw'].astype(str).str.lower().str.strip().replace('nan','desconocido')
        df['anos_experiencia'] = df['seniority_normalizado'].map(lambda s: self.seniority_map.get(s, self.seniority_map['desconocido'])['anos_experiencia'])
        df['tech_exp_factor'] = df['seniority_normalizado'].map(lambda s: self.seniority_map.get(s, self.seniority_map['desconocido'])['tech_exp_factor'])
        df['nivel_valor'] = df['seniority_normalizado'].map(lambda s: self.seniority_map.get(s, self.seniority_map['desconocido'])['level_value'])

        # --- Initialize Tech Columns ---
        all_known_standard_techs = list(self.tech_mapping.keys())
        for tech_std_name in all_known_standard_techs:
            df[self._get_standard_tech_col_name(tech_std_name, '_exp')] = 0.0
            df[self._get_standard_tech_col_name(tech_std_name, '_principal')] = False
        logger.debug("Initialized tech columns (_exp, _principal) for known techs.")

        # --- Process Technologies String ---
        for index, row in df.iterrows():
            tech_string = row.get('technologies_raw')
            if pd.isna(tech_string) or not isinstance(tech_string, str) or not tech_string.strip(): continue
            listed_techs_raw = re.split(r'[;,]\s*', tech_string.strip())
            for tech_item_raw in listed_techs_raw:
                tech_item_clean = tech_item_raw.strip()
                if not tech_item_clean: continue
                potential_techs = ["html", "css"] if "html / css" in tech_item_clean.lower() else [self._normalize_tech_name(tech_item_clean)]
                for normalized_tech in potential_techs:
                    if normalized_tech and normalized_tech in self.tech_mapping:
                        exp_col_name = self._get_standard_tech_col_name(normalized_tech, '_exp')
                        exp_factor = row.get('tech_exp_factor', 0.1)
                        df.loc[index, exp_col_name] = exp_factor if pd.notna(exp_factor) and isinstance(exp_factor, (int, float)) else 0.1
                        principal_col_name = self._get_standard_tech_col_name(normalized_tech, '_principal')
                        df.loc[index, principal_col_name] = True

        # --- Add Missing Columns with Defaults ---
        df['proyectos_completados_original'] = 0
        df['certificaciones_original'] = 0
        df['horas_capacitacion_original'] = 0
        df['ingles_avanzado'] = False
        df['lider_equipo'] = False

        # --- Store Original Numeric Values ---
        numeric_cols_for_original_storage = [
            'salario_original', 'anos_experiencia', 'proyectos_completados_original',
            'certificaciones_original', 'horas_capacitacion_original', 'nivel_valor'
        ]
        exp_cols_generated = [col for col in df.columns if col.endswith('_exp')]
        numeric_cols_for_original_storage.extend(exp_cols_generated)
        valid_original_cols = []
        for col in list(numeric_cols_for_original_storage):
             if col in df.columns:
                  df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                  if pd.api.types.is_numeric_dtype(df[col]):
                      valid_original_cols.append(col)
                  else: logger.warning(f"Col '{col}' no numérica post-conversión. Excluida de originales.")
             else: logger.warning(f"Col '{col}' no existe. Excluida de originales.")
        self.df_employees_original_numeric_values = df[valid_original_cols].copy()
        self.df_employees_original_numeric_values.rename(columns={
            'salario_original': 'salario', 'proyectos_completados_original': 'proyectos_completados',
            'certificaciones_original': 'certificaciones', 'horas_capacitacion_original': 'horas_capacitacion',
        }, inplace=True, errors='ignore')

        # --- Prepare columns for Normalization ---
        df.rename(columns={
            'proyectos_completados_original': 'proyectos_completados_norm',
            'certificaciones_original': 'certificaciones_norm',
            'horas_capacitacion_original': 'horas_capacitacion_norm',
            'salario_original': 'salario_norm'
        }, inplace=True, errors='ignore')

        # --- Backup and Drop Raw Columns ---
        # Guardar backups ANTES de dropear las columnas originales
        if 'job_title_raw' in df.columns: df['job_title_raw_bkp'] = df['job_title_raw']
        if 'seniority_raw' in df.columns: df['seniority_raw_bkp'] = df['seniority_raw']

        cols_to_drop = ['job_title_raw', 'role_raw', 'technologies_raw', 'seniority_raw',
                        'project_names_raw', 'tech_exp_factor'] # No dropear 'last_name' si se usa para nombre_completo
        df.drop(columns=[col for col in cols_to_drop if col in df.columns], inplace=True, errors='ignore')

        logger.info("Data preprocessing finished.")
        return df

    def _normalize_numeric_values(self):
        """Normaliza columnas numéricas seleccionadas usando MinMaxScaler."""
        if self.df_employees.empty: logger.warning("DataFrame vacío, saltando normalización."); return
        cols_to_normalize = ['salario_norm', 'anos_experiencia', 'proyectos_completados_norm',
                             'certificaciones_norm', 'horas_capacitacion_norm', 'nivel_valor']
        exp_cols = [col for col in self.df_employees.columns if col.endswith('_exp')]
        cols_to_normalize.extend(exp_cols)
        valid_cols_to_normalize = [c for c in cols_to_normalize if c in self.df_employees.columns and pd.api.types.is_numeric_dtype(self.df_employees[c])]
        if not valid_cols_to_normalize: logger.warning("No hay columnas válidas para normalizar."); return
        logger.info(f"Normalizing {len(valid_cols_to_normalize)} columns.")
        df_to_normalize_subset = self.df_employees[valid_cols_to_normalize].copy().fillna(0)
        scaler = MinMaxScaler()
        try:
            normalized_values = scaler.fit_transform(df_to_normalize_subset)
            df_normalized_subset = pd.DataFrame(normalized_values, columns=valid_cols_to_normalize, index=self.df_employees.index)
            for col in valid_cols_to_normalize: self.df_employees[col] = df_normalized_subset[col]
            logger.info("Normalization completed.")
            # if DEBUG_MODE: logger.debug(f"Sample normalized data:\n{self.df_employees[valid_cols_to_normalize].head()}")
        except Exception as e: logger.exception(f"Error durante MinMaxScaling: {e}")

    def _infer_techs_from_description(self, description: str) -> Set[str]:
        """Infiere tecnologías normalizadas desde la descripción del proyecto."""
        if not self.nlp or not isinstance(description, str) or not description.strip(): return set()
        inferred_techs = set()
        try:
            doc = self.nlp(description.lower())
            potential_texts = set()
            for ent in doc.ents:
                if ent.label_ in ["ORG", "PRODUCT", "TECH", "LANGUAGE", "WORK_OF_ART", "PERSON"]:
                     potential_texts.add(ent.text)
            for token in doc:
                if token.pos_ in ["NOUN", "PROPN"] and not token.is_stop and len(token.text) > 1:
                    potential_texts.add(token.lemma_ if token.lemma_ != "-PRON-" and len(token.lemma_)>1 else token.text)
            for text in potential_texts:
                norm_tech = self._normalize_tech_name(text)
                if norm_tech and norm_tech in self.tech_mapping: inferred_techs.add(norm_tech)
        except Exception as e: logger.exception(f"Error durante procesamiento NLP: {e}")
        logger.info(f"NLP inferred standard techs: {inferred_techs}")
        return inferred_techs

    def calculate_score(self, row: pd.Series, required_techs_for_role: Set[str], all_project_techs: Set[str]) -> float:
        """Calcula la puntuación de relevancia para un candidato."""
        tech_score, exp_score = 0.0, 0.0
        candidate_id = row.get('id', 'N/A')
        tech_found_for_role_count = 0
        all_relevant_techs = required_techs_for_role.union(all_project_techs)
        for tech_std_name in all_relevant_techs:
            exp_col, exp_value = self._get_standard_tech_col_name(tech_std_name, '_exp'), row.get(self._get_standard_tech_col_name(tech_std_name, '_exp'), 0.0)
            if exp_value > 0:
                principal_col, is_principal = self._get_standard_tech_col_name(tech_std_name, '_principal'), row.get(self._get_standard_tech_col_name(tech_std_name, '_principal'), False)
                contribution = exp_value * (1.5 if is_principal else 1.0)
                if tech_std_name in required_techs_for_role:
                    contribution *= 2.0; tech_found_for_role_count += 1
                elif tech_std_name in all_project_techs: contribution *= 1.0
                tech_score += contribution
        if required_techs_for_role and tech_found_for_role_count == 0 and STRICT_FILTER_MODE != 'none': tech_score -= 50
        exp_score += row.get('anos_experiencia', 0.0) * 5.0
        exp_score += row.get('nivel_valor', 0.0) * 2.0
        total_score = (tech_score * 0.70) + (exp_score * 0.30) # Ajustar pesos si es necesario
        # if DEBUG_MODE: logger.debug(f"Score Calc ID {candidate_id} ({row.get('rol_asignado','N/A')}): Tech={tech_score:.2f}, Exp={exp_score:.2f} -> TOTAL={total_score:.3f}")
        return total_score if pd.notna(total_score) and np.isfinite(total_score) else 0.0

    def recommend_team(self, project_description: str, team_structure: Dict[str, int], budget: float, explicit_technologies_by_role: Optional[Dict[str, List[str]]]) -> Dict[str, Any]:
        """Orquesta el proceso completo de recomendación de equipo."""
        if self.df_employees is None or self.df_employees.empty:
            logger.error("No hay datos de empleados cargados. No se puede recomendar.")
            return {"equipo": [], "presupuesto": {"total": float(budget), "utilizado": 0.0, "restante": float(budget), "porcentaje_utilizado": 0.0}, "metricas": {"promedio_puntaje": 0.0, "tecnologias_faltantes": [], "roles_cubiertos": {}, "roles_solicitados": team_structure}, "analisis_equipo": "Error: Datos no disponibles.", "status_message": "Error: Datos no disponibles.", "inferred_project_technologies": []}

        logger.info(f"Starting team recommendation. Budget: {budget:.0f}, Structure: {team_structure}")
        inferred_standard_techs = self._infer_techs_from_description(project_description)
        all_project_techs_standard, final_techs_for_role_filter = set(inferred_standard_techs), defaultdict(set)
        if explicit_technologies_by_role:
             for role_key, techs_list in explicit_technologies_by_role.items():
                  role_norm_ui = role_key.lower().strip()
                  current_role_explicit_std_techs = {norm_t for tech_raw in techs_list if (norm_t := self._normalize_tech_name(tech_raw)) and norm_t in self.tech_mapping}
                  final_techs_for_role_filter[role_norm_ui].update(current_role_explicit_std_techs)
                  all_project_techs_standard.update(current_role_explicit_std_techs)
        logger.info(f"All project techs considered: {all_project_techs_standard}")

        all_candidate_rows_for_selection, processed_ids = [], set()
        for role_from_structure, count_needed in team_structure.items():
            role_normalized_struct = role_from_structure.lower().strip()
            if count_needed <= 0: continue
            logger.info(f"Processing role: '{role_normalized_struct}', need {count_needed}.")
            candidates_for_role_df = self.df_employees[self.df_employees['rol_asignado'] == role_normalized_struct].copy()
            if candidates_for_role_df.empty: logger.warning(f"No candidates for role: {role_normalized_struct}."); continue
            current_role_filter_techs = final_techs_for_role_filter.get(role_normalized_struct, set())
            if STRICT_FILTER_MODE != 'none' and current_role_filter_techs:
                conditions = []
                for tech_std_name in current_role_filter_techs:
                    col_name = self._get_standard_tech_col_name(tech_std_name, '_principal' if STRICT_FILTER_MODE == 'principal' else '_exp')
                    if col_name in candidates_for_role_df.columns:
                        if STRICT_FILTER_MODE == 'principal': conditions.append(f"`{col_name}` == True")
                        elif STRICT_FILTER_MODE == 'exp': conditions.append(f"`{col_name}` >= {MIN_EXP_THRESHOLD}")
                if conditions:
                    query_str = " or ".join(conditions)
                    try: candidates_for_role_df.query(query_str, inplace=True)
                    except Exception as e: logger.error(f"Error strict filter query: {e}. Query: {query_str}")
            if candidates_for_role_df.empty: logger.warning(f"No candidates remain for role '{role_normalized_struct}' after filters."); continue
            candidates_for_role_df['score'] = candidates_for_role_df.apply(lambda r: self.calculate_score(r, current_role_filter_techs, all_project_techs_standard), axis=1)
            candidates_for_role_df = candidates_for_role_df.join(self.df_employees_original_numeric_values[['salario']], how='left')
            candidates_for_role_df.rename(columns={'salario': 'salario_para_sort'}, inplace=True)
            candidates_for_role_df['salario_para_sort'].fillna(0, inplace=True)
            sorted_candidates_df = candidates_for_role_df.sort_values(by=['score', 'salario_para_sort'], ascending=[False, True])

            for idx, cand_row_series in sorted_candidates_df.iterrows():
                 member_id = int(cand_row_series['id'])
                 if member_id in processed_ids: continue
                 original_values_cand = self.df_employees_original_numeric_values.loc[idx]
                 job_title_bkp = cand_row_series.get('job_title_raw_bkp', None)
                 puesto_original_final = str(job_title_bkp) if pd.notna(job_title_bkp) else None
                 seniority_bkp = cand_row_series.get('seniority_raw_bkp', None)
                 seniority_original_final = str(seniority_bkp) if pd.notna(seniority_bkp) else None

                 member_data = {
                    'id': member_id, 'nombre': cand_row_series.get('nombre_completo', 'N/A'),
                    'email': cand_row_series.get('email', 'N/A'), 'puesto_original': puesto_original_final,
                    'rol_asignado': cand_row_series['rol_asignado'], 'rol_asignado_display': cand_row_series['rol_asignado'].replace('_', ' ').title(),
                    'seniority_original': seniority_original_final, 'seniority_normalizado': cand_row_series.get('seniority_normalizado', 'N/A'),
                    'anos_experiencia': int(original_values_cand.get('anos_experiencia', 0)),
                    'proyectos_completados': int(original_values_cand.get('proyectos_completados', 0)),
                    'salario': int(original_values_cand.get('salario', 0)), 'score': round(cand_row_series['score'], 4),
                    'tecnologias_conocidas': [], 'nivel_valor_original': int(original_values_cand.get('nivel_valor',0)),
                 }
                 known_techs_for_member_std = {ts for ts in self.tech_mapping if cand_row_series.get(self._get_standard_tech_col_name(ts, '_exp'), 0) > 0}
                 member_data['tecnologias_conocidas'] = sorted([self.tech_mapping[st][0].replace('.', ' ').title() for st in known_techs_for_member_std])
                 all_candidate_rows_for_selection.append(member_data)
                 processed_ids.add(member_id)

        # 3. Selección Final
        if not all_candidate_rows_for_selection:
            logger.warning("No suitable candidates after processing all roles.")
            # Retornar estructura vacía pero válida
            return {"equipo": [], "presupuesto": {"total": float(budget), "utilizado": 0.0, "restante": float(budget), "porcentaje_utilizado": 0.0}, "metricas": {"promedio_puntaje": 0.0, "tecnologias_faltantes": sorted(list(all_project_techs_standard)), "roles_cubiertos": {}, "roles_solicitados": team_structure}, "analisis_equipo": "No candidates found.", "status_message": "No candidates found.", "inferred_project_technologies": sorted(list(inferred_standard_techs))}

        all_candidate_rows_for_selection.sort(key=lambda x: (-x['score'], x['salario']))
        final_team, current_budget_spent, roles_filled_count = [], 0.0, {r.lower().strip(): 0 for r in team_structure}
        target_roles_to_fill_count = {r.lower().strip(): c for r, c in team_structure.items() if c > 0}
        selected_member_ids_final, total_roles_needed_overall = set(), sum(target_roles_to_fill_count.values())
        logger.info(f"Starting final selection from {len(all_candidate_rows_for_selection)} pre-selected candidates.")

        for candidate_dict in all_candidate_rows_for_selection:
            if sum(roles_filled_count.values()) >= total_roles_needed_overall: break
            candidate_role_assigned, candidate_id, candidate_salary = candidate_dict['rol_asignado'], candidate_dict['id'], float(candidate_dict['salario'])
            if candidate_role_assigned in target_roles_to_fill_count and roles_filled_count.get(candidate_role_assigned, 0) < target_roles_to_fill_count[candidate_role_assigned]:
                if candidate_id not in selected_member_ids_final and (current_budget_spent + candidate_salary) <= budget:
                    final_team.append(candidate_dict); current_budget_spent += candidate_salary
                    roles_filled_count[candidate_role_assigned] += 1; selected_member_ids_final.add(candidate_id)

        # 4. Preparar Respuesta Final
        budget_remaining, status_message = budget - current_budget_spent, "Team successfully generated."
        if not final_team and total_roles_needed_overall > 0: status_message = "Could not form a team meeting the criteria and budget."
        elif sum(roles_filled_count.values()) < total_roles_needed_overall: status_message = "Team partially formed. Not all requested roles could be filled."
        team_techs_set = {norm_tech for member in final_team for tech_name in member['tecnologias_conocidas'] if (norm_tech := self._normalize_tech_name(tech_name))}
        missing_techs = sorted(list(all_project_techs_standard - team_techs_set))
        logger.info(f"Recommendation finished. Team size: {len(final_team)}. Budget Spent: {current_budget_spent:.2f}. Status: {status_message}")

        response_payload = {
            "equipo": final_team,
            "presupuesto": {"total": float(budget), "utilizado": float(current_budget_spent), "restante": float(budget_remaining), "porcentaje_utilizado": (current_budget_spent / budget) if budget > 0 else 0.0},
            "metricas": {"promedio_puntaje": np.mean([m['score'] for m in final_team]).item() if final_team else 0.0, "tecnologias_faltantes": missing_techs, "roles_cubiertos": roles_filled_count, "roles_solicitados": target_roles_to_fill_count},
            "analisis_equipo": status_message, "status_message": status_message, "inferred_project_technologies": sorted(list(inferred_standard_techs))
        }
        return response_payload