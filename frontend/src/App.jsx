// frontend/src/App.jsx
// import React, { useState, useEffect } from 'react'; // useEffect para cargar roles/techs del backend si fuera necesario
// import './App.css';
// import LoginPage from './components/LoginPage';
// import RegisterPage from './components/RegisterPage';
// import './components/LoginPage.css';
// import './components/RegisterPage.css';

// // Definición de tecnologías y roles (Ajustar según los roles mapeados en el backend)
// // Estos son los roles que el usuario podrá seleccionar para la estructura del equipo.
// // Deben coincidir con las CLAVES de `self.role_keywords_map` en Python (o los roles que esperas usar).
// const UIRoles = ['backend', 'frontend', 'fullstack', 'devops', 'qa', 'project manager', 'analista funcional', 'diseñador ux/ui', 'arquitecto', 'data scientist', 'scrum master'];

// // Tecnologías disponibles por rol para el UI (ajustar según tu `tech_mapping` y lo que quieras ofrecer)
// const availableTechsByRole = {
//   backend: ['Python', 'Java', 'Node.js', '.Net Core', '.Net Framework', 'Django', 'Spring', 'PostgreSQL', 'MongoDB', 'MySQL', 'SQL Server', 'Docker', 'AWS', 'Azure', 'Microservicios', 'Kafka'],
//   frontend: ['JavaScript', 'React', 'Angular', 'Vue', 'TypeScript', 'HTML', 'CSS', 'React Native', 'Flutter', 'Figma'],
//   fullstack: ['Python', 'Java', 'Node.js', 'React', 'Angular', 'Vue', 'TypeScript', '.Net Core', 'HTML', 'CSS', 'AWS', 'Docker'],
//   devops: ['Docker', 'Kubernetes', 'AWS', 'Azure', 'Jenkins', 'Git', 'Linux', 'Terraform', 'Ansible', 'GCP'],
//   qa: ['Selenium', 'Cypress', 'JUnit', 'Postman', 'JMeter', 'Python', 'Jira'],
//   'project manager': ['Jira', 'Agile', 'Scrum', 'MS Project'], // Techs más orientadas a gestión
//   'analista funcional': ['UML', 'SQL', 'Jira', 'Mockups', 'DB Relacionales'],
//   'diseñador ux/ui': ['Figma', 'Adobe XD', 'Sketch', 'HTML', 'CSS', 'User Research'],
//   arquitecto: ['AWS', 'Azure', 'Microservicios', 'Docker', 'Kubernetes', 'TOGAF'],
//   'data scientist': ['Python', 'R', 'TensorFlow', 'PyTorch', 'Pandas', 'Scikit-learn'],
//   'scrum master': ['Jira', 'Agile', 'Kanban'],
//   // Puedes añadir más roles y sus tecnologías si los tienes en `role_keywords_map`
// };

// const initialFormData = {
//     description: '',
//     budget: 1500000, // Un presupuesto inicial más acorde al CSV
//     // Estructura de roles dinámica
//     roles: UIRoles.reduce((acc, role) => { acc[role] = 0; return acc; }, {}),
//     // Tecnologías explícitas por rol
//     techs: UIRoles.reduce((acc, role) => { acc[role] = []; return acc; }, {})
// };
// initialFormData.roles.backend = 1; // Default 1 backend
// initialFormData.roles.frontend = 1; // Default 1 frontend


// function App() {
//   const [isAuthenticated, setIsAuthenticated] = useState(false);
//   const [username, setUsername] = useState('');
//   const [authMode, setAuthMode] = useState('login');
//   const [formData, setFormData] = useState(initialFormData);
//   const [teamResult, setTeamResult] = useState(null);
//   const [loading, setLoading] = useState(false);
//   const [error, setError] = useState(null);
//   const [inferredTechsUI, setInferredTechsUI] = useState([]);


//   const handleLoginSuccess = (loggedInUsername) => {
//     setIsAuthenticated(true);
//     setUsername(loggedInUsername);
//     setError(null);
//     setAuthMode('login');
//   };

//   const handleLogout = () => {
//     setIsAuthenticated(false);
//     setUsername('');
//     setTeamResult(null);
//     setFormData(initialFormData);
//     setError(null);
//     setAuthMode('login');
//     setInferredTechsUI([]);
//   };

//   const switchToRegister = () => setAuthMode('register');
//   const switchToLogin = () => setAuthMode('login');
//   const handleRegisterSuccess = (registeredUsername) => {
//      console.log(`Usuario ${registeredUsername} registrado.`);
//      setTimeout(() => setAuthMode('login'), 2000);
//   };

//   const handleInputChange = (e) => {
//     const { name, value, type } = e.target;
//     setFormData(prev => ({
//       ...prev,
//       [name]: type === 'number' ? (value === '' ? '' : Number(value)) : value
//     }));
//   };

//   const handleRoleCountChange = (role, value) => {
//     const count = value === '' ? 0 : Number(value);
//     setFormData(prev => ({
//         ...prev,
//         roles: { ...prev.roles, [role]: Math.max(0, count) } // Asegurar que no sea negativo
//     }));
//   };

//   const handleTechToggle = (role, tech) => {
//     setFormData(prev => {
//       const currentTechs = prev.techs[role] || [];
//       const isSelected = currentTechs.includes(tech);
//       const updatedTechs = isSelected ? currentTechs.filter(t => t !== tech) : [...currentTechs, tech];
//       return { ...prev, techs: { ...prev.techs, [role]: updatedTechs } };
//     });
//   };

//   const handleSubmit = async (e) => {
//     e.preventDefault();
//     setLoading(true);
//     setError(null);
//     setTeamResult(null);
//     setInferredTechsUI([]);

//     const team_structure = {};
//     for (const role in formData.roles) {
//       if (formData.roles[role] > 0) {
//         team_structure[role] = formData.roles[role];
//       }
//     }

//     const explicit_technologies_by_role = {}; // Cambiado el nombre para coincidir con el backend
//     for (const role in formData.techs) {
//       if (team_structure[role] && formData.techs[role]?.length > 0) {
//         explicit_technologies_by_role[role] = formData.techs[role];
//       }
//     }

//     const requestBody = {
//       project_description: formData.description || "Proyecto de desarrollo de software general",
//       team_structure: team_structure,
//       budget: parseFloat(formData.budget) || 0,
//       explicit_technologies_by_role: explicit_technologies_by_role // Nombre de campo esperado por el backend
//     };

//     console.log("Enviando al backend:", JSON.stringify(requestBody, null, 2));

//     try {
//       const response = await fetch('http://localhost:8000/api/teams/generate', { // Asegúrate que el endpoint sea el correcto
//         method: 'POST',
//         headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
//         body: JSON.stringify(requestBody)
//       });

//       const responseData = await response.json();

//       if (!response.ok) {
//         console.error("Error del backend:", responseData);
//         throw new Error(responseData.detail || responseData.message || `Error ${response.status}`);
//       }

//       console.log("Respuesta recibida del backend:", responseData);
//       setTeamResult(responseData); // El backend ahora devuelve la estructura completa esperada
//       if (responseData.inferred_project_technologies) {
//         setInferredTechsUI(responseData.inferred_project_technologies);
//       }

//     } catch (err) {
//       setError(err.message || "Ocurrió un error al conectar con el servidor.");
//       console.error("Error en la solicitud fetch:", err);
//     } finally {
//       setLoading(false);
//     }
//   };

//   if (!isAuthenticated) {
//     return authMode === 'login' ? (
//       <LoginPage onLoginSuccess={handleLoginSuccess} onSwitchToRegister={switchToRegister} />
//     ) : (
//       <RegisterPage onSwitchToLogin={switchToLogin} onRegisterSuccess={handleRegisterSuccess} />
//     );
//   }

//   return (
//     <div className="app-container">
//       <header className="app-header">
//          <h1>Software Team Builder IA (MindFactory)</h1>
//          <div className="user-info">
//            <span>Bienvenido, {username}!</span>
//            <button onClick={handleLogout} className="logout-button">Cerrar Sesión</button>
//          </div>
//        </header>

//        <main>
//          <p className="app-description">Describe tu proyecto, define la estructura del equipo, el presupuesto y las tecnologías clave. La IA te recomendará el mejor equipo técnico de MindFactory.</p>

//          <form onSubmit={handleSubmit} className="team-builder-form">
//             <div className="form-section">
//               <h2>1. Detalles del Proyecto</h2>
//               <div className="form-group"> <label htmlFor="description">Descripción:</label> <textarea id="description" name="description" value={formData.description} onChange={handleInputChange} rows="3" placeholder="Ej: Desarrollo de app móvil con backend en Python..." /> </div>
//               <div className="form-group"> <label htmlFor="budget">Presupuesto Total ($):</label> <input type="number" id="budget" name="budget" value={formData.budget} onChange={handleInputChange} min="0" step="10000" /> </div>
//             </div>

//             <div className="form-section">
//               <h2>2. Estructura del Equipo</h2>
//               <div className="role-structure-grid">
//                 {UIRoles.map(role => (
//                   <div className="form-group" key={role}>
//                     <label htmlFor={`role-${role}`}>{role.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}:</label>
//                     <input
//                       type="number"
//                       id={`role-${role}`}
//                       name={`role-${role}`}
//                       min="0"
//                       value={formData.roles[role]}
//                       onChange={(e) => handleRoleCountChange(role, e.target.value)}
//                     />
//                   </div>
//                 ))}
//               </div>
//             </div>

//             <div className="form-section tech-selection">
//               <h2>3. Tecnologías Clave (Opcional por Rol)</h2>
//               {UIRoles.map(role => (
//                 formData.roles[role] > 0 && (
//                   <div key={`techgroup-${role}`} className="tech-group">
//                     <h4>{role.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</h4>
//                     <div className="tech-checkboxes">
//                       {(availableTechsByRole[role] || []).map(tech => (
//                         <label key={`${role}-${tech}`}>
//                           <input type="checkbox" value={tech} checked={formData.techs[role]?.includes(tech) || false} onChange={() => handleTechToggle(role, tech)} />
//                           {tech}
//                         </label>
//                       ))}
//                     </div>
//                   </div>
//                 )
//               ))}
//             </div>
//             {inferredTechsUI.length > 0 && (
//                 <div className="inferred-techs-display card">
//                     <h4>Tecnologías Inferidas de la Descripción:</h4>
//                     <p>{inferredTechsUI.join(', ')}</p>
//                 </div>
//             )}

//             <div className="submit-section"> <button type="submit" disabled={loading}>{loading ? 'Buscando...' : 'Generar Equipo'}</button> </div>
//          </form>

//          {error && <div className="error-message">Error: {error}</div>}
//          {teamResult && !error && (
//              <div className="team-results">
//                  <h2>Equipo Recomendado</h2>
//                  {teamResult.presupuesto && ( <div className="result-summary"> <div className="budget-info card"> <h3>Presupuesto</h3> <p>Total Solicitado: <span>${(teamResult.presupuesto.total ?? 0).toLocaleString('es-AR')}</span></p> <p>Utilizado Estimado: <span>${(teamResult.presupuesto.utilizado ?? 0).toLocaleString('es-AR')}</span></p> <p>Restante Estimado: <span className={(teamResult.presupuesto.restante ?? 0) < 0 ? 'negative-budget' : ''}>${(teamResult.presupuesto.restante ?? 0).toLocaleString('es-AR')}</span> ({((teamResult.presupuesto.porcentaje_utilizado ?? 0) * 100).toFixed(1)}% usado)</p> </div> </div> )}
                 
//                  {teamResult.analisis_equipo && ( <div className="analysis-info card"> <h3>Análisis General</h3> <p>{teamResult.analisis_equipo}</p> </div> )}
                 
//                  <h3>Miembros del Equipo ({teamResult.equipo?.length || 0})</h3>
//                  {teamResult.equipo?.length > 0 ? (
//                     <div className="team-members">
//                         {teamResult.equipo.map((member, index) => (
//                             <div key={`${member.id}-${index}-${member.rol_asignado}`} className="member-card card">
//                                 <h4>{member.nombre || member.email} {/* Muestra email si no hay nombre */}
//                                     <span className="member-level"> ({member.seniority_original || member.seniority_normalizado || 'N/A'})</span>
//                                 </h4>
//                                 <p><strong>Rol Asignado:</strong> <span className="member-role">{member.rol_asignado_display || member.rol_asignado}</span></p>
//                                 <p><strong>Puesto Original:</strong> {member.puesto_original || 'N/A'}</p>
//                                 <p><strong>Años Exp (Estimados):</strong> {member.anos_experiencia || 0}</p>
//                                 <p><strong>Tecnologías Conocidas:</strong> {member.tecnologias_conocidas?.join(', ') || 'N/A'}</p>
//                                 <p><strong>Salario (Estimado):</strong> <span className="member-salary">${(member.salario ?? 0).toLocaleString('es-AR')}</span></p>
//                                 <p><strong>Score (Relevancia):</strong> {member.score?.toFixed(3) || 'N/A'}</p>
//                             </div>
//                         ))}
//                     </div>
//                  ) : ( <p>No se encontraron miembros adecuados según los criterios y presupuesto.</p> )}
                 
//                  {teamResult.metricas && (
//                     <div className="metrics-info card">
//                         <h3>Métricas Adicionales</h3>
//                         <p>Score Promedio del Equipo: {teamResult.metricas.promedio_puntaje?.toFixed(3) || 'N/A'}</p>
//                         <p>Roles Solicitados: {Object.entries(teamResult.metricas.roles_solicitados || {}).map(([r,c])=>`${r}(${c})`).join(', ')}</p>
//                         <p>Roles Cubiertos: {Object.entries(teamResult.metricas.roles_cubiertos || {}).map(([r,c])=>`${r}(${c})`).join(', ')}</p>
//                         {teamResult.metricas.tecnologias_faltantes?.length > 0 && (
//                             <p className="warning-techs">Posibles Tecnologías Faltantes en el Equipo General: {teamResult.metricas.tecnologias_faltantes.join(', ')}</p>
//                         )}
//                     </div>
//                  )}
//              </div>
//          )}
//        </main>
//     </div>
//   );
// }

// export default App;   


// frontend/src/App.jsx
import React, { useState, useEffect } from 'react';
import './App.css';
import LoginPage from './components/LoginPage';
import RegisterPage from './components/RegisterPage';
import './components/LoginPage.css';
import './components/RegisterPage.css';

// --- Definición de Roles y Tecnologías para la UI ---
const UIRoles = [
    'backend', 'frontend', 'fullstack', 'devops', 'qa',
    'project manager', 'analista funcional', 'diseñador ux/ui',
    'arquitecto', 'data scientist', 'scrum master'
];
const availableTechsByRole = {
  backend: ['Python', 'Java', 'Node.js', '.Net Core', '.Net Framework', 'Django', 'Spring', 'PostgreSQL', 'MongoDB', 'MySQL', 'SQL Server', 'Docker', 'AWS', 'Azure', 'Microservicios', 'Kafka'],
  frontend: ['JavaScript', 'React', 'Angular', 'Vue', 'TypeScript', 'HTML', 'CSS', 'React Native', 'Flutter', 'Figma'],
  fullstack: ['Python', 'Java', 'Node.js', 'React', 'Angular', 'Vue', 'TypeScript', '.Net Core', 'HTML', 'CSS', 'AWS', 'Docker'],
  devops: ['Docker', 'Kubernetes', 'AWS', 'Azure', 'Jenkins', 'Git', 'Linux', 'Terraform', 'Ansible', 'GCP'],
  qa: ['Selenium', 'Cypress', 'JUnit', 'Postman', 'JMeter', 'Python', 'Jira'],
  'project manager': ['Jira', 'Agile', 'Scrum', 'MS Project'],
  'analista funcional': ['UML', 'SQL', 'Jira', 'Mockups', 'DB Relacionales'],
  'diseñador ux/ui': ['Figma', 'Adobe XD', 'Sketch', 'HTML', 'CSS', 'User Research'],
  arquitecto: ['AWS', 'Azure', 'Microservicios', 'Docker', 'Kubernetes', 'TOGAF'],
  'data scientist': ['Python', 'R', 'TensorFlow', 'PyTorch', 'Pandas', 'Scikit-learn', 'SQL'],
  'scrum master': ['Jira', 'Agile', 'Kanban', 'Confluence'],
};

// --- Estado Inicial del Formulario ---
const initialFormData = {
    description: '',
    budget: 1500000,
    roles: UIRoles.reduce((acc, role) => { acc[role] = 0; return acc; }, {}),
    techs: UIRoles.reduce((acc, role) => { acc[role] = []; return acc; }, {})
};
initialFormData.roles.backend = 1;
initialFormData.roles.frontend = 1;

// --- Componente Principal App ---
function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [username, setUsername] = useState('');
  const [authMode, setAuthMode] = useState('login');
  const [formData, setFormData] = useState(initialFormData);
  const [teamResult, setTeamResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [inferredTechsUI, setInferredTechsUI] = useState([]);

  // --- Handlers Autenticación ---
  const handleLoginSuccess = (loggedInUsername) => {
    console.log(`Login successful: ${loggedInUsername}`);
    setIsAuthenticated(true);
    setUsername(loggedInUsername);
    setError(null);
    setAuthMode('login');
  };
  const handleLogout = () => {
    setIsAuthenticated(false); setUsername(''); setTeamResult(null);
    setFormData(initialFormData); setError(null); setAuthMode('login');
    setInferredTechsUI([]);
  };
  const switchToRegister = () => { setAuthMode('register'); setError(null); };
  const switchToLogin = () => { setAuthMode('login'); setError(null); };
  const handleRegisterSuccess = (registeredUsername) => {
     console.log(`Usuario ${registeredUsername} registrado exitosamente.`);
     setError("Registro exitoso. Por favor, inicia sesión.");
     setTimeout(() => { setAuthMode('login'); setError(null); }, 2500);
  };

  // --- Handlers Formulario ---
  const handleInputChange = (e) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({ ...prev, [name]: type === 'number' ? (value === '' ? '' : Number(value)) : value }));
  };
  const handleRoleCountChange = (role, value) => {
    const count = value === '' ? 0 : Math.max(0, Number(value));
    setFormData(prev => ({ ...prev, roles: { ...prev.roles, [role]: count } }));
  };
  const handleTechToggle = (role, tech) => {
    setFormData(prev => {
      const currentTechs = prev.techs[role] || [];
      const isSelected = currentTechs.includes(tech);
      const updatedTechs = isSelected ? currentTechs.filter(t => t !== tech) : [...currentTechs, tech];
      return { ...prev, techs: { ...prev.techs, [role]: updatedTechs } };
    });
  };

  // --- Handler Submit ---
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true); setError(null); setTeamResult(null); setInferredTechsUI([]);

    const team_structure = {};
    for (const role in formData.roles) {
      if (formData.roles[role] > 0) {
        team_structure[role] = formData.roles[role];
      }
    }
    if (Object.keys(team_structure).length === 0) {
         setError("Por favor, selecciona al menos un miembro para la estructura del equipo.");
         setLoading(false); return;
    }

    const explicit_technologies_by_role = {};
    for (const role in formData.techs) {
      if (team_structure[role] && formData.techs[role]?.length > 0) {
        explicit_technologies_by_role[role] = formData.techs[role];
      }
    }

    const requestBody = {
      project_description: formData.description || "Proyecto de desarrollo de software general",
      team_structure: team_structure,
      budget: parseFloat(formData.budget.toString()) || 0,
      explicit_technologies_by_role: explicit_technologies_by_role
    };

    console.log("handleSubmit: Iniciando fetch para /api/teams/generate");
    console.log("handleSubmit: requestBody construido:", requestBody);

    try {
      const bodyString = JSON.stringify(requestBody);
      console.log("handleSubmit: JSON.stringify(requestBody) exitoso.");

      const apiUrl = '/api/teams/generate'; // URL relativa, asume que el proxy de Vite o Nginx la maneja
      console.log(`handleSubmit: Fetching POST ${apiUrl}`);

      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: bodyString
      });

      console.log(`handleSubmit: Fetch respondió con status ${response.status}`);

      const responseText = await response.text(); // Obtener el texto CRUDO
      console.log("handleSubmit: Texto CRUDO de la respuesta del servidor:", responseText); // Loguear el texto

      let responseData;
      if (!responseText || responseText.trim() === "") {
        if (response.ok) {
            console.warn("handleSubmit: Respuesta OK (2xx) pero cuerpo vacío.");
            throw new Error("El servidor devolvió una respuesta OK pero vacía, y se esperaba JSON.");
        } else {
            throw new Error(`Error del servidor: ${response.status} ${response.statusText} con cuerpo de respuesta vacío.`);
        }
      }

      try {
        responseData = JSON.parse(responseText);
      } catch (parseError) {
        console.error("handleSubmit: Error al parsear la respuesta JSON:", parseError);
        throw new Error(`Respuesta inválida o no JSON del servidor. Texto recibido (primeros 200 chars): '${responseText.substring(0, 200)}'`);
      }

      if (!response.ok) {
        console.error("handleSubmit: Error del backend (status no OK):", responseData);
        throw new Error(responseData.detail || responseData.message || `Error del servidor: ${response.status}`);
      }

      console.log("handleSubmit: Respuesta JSON válida recibida del backend:", responseData);
      setTeamResult(responseData);
      if (responseData.inferred_project_technologies) {
        setInferredTechsUI(responseData.inferred_project_technologies);
      }

    } catch (err) {
      console.error('handleSubmit: Error en el bloque try/fetch:', err);
      setError(err.message || "Ocurrió un error al generar el equipo. Intenta de nuevo.");
    } finally {
      setLoading(false);
      console.log("handleSubmit: Proceso de fetch finalizado.");
    }
  };

  // --- Renderizado ---
  if (!isAuthenticated) {
    return authMode === 'login' ? (
      <LoginPage onLoginSuccess={handleLoginSuccess} onSwitchToRegister={switchToRegister} />
    ) : (
      <RegisterPage onSwitchToLogin={switchToLogin} onRegisterSuccess={handleRegisterSuccess} />
    );
  }

  return (
    <div className="app-container">
      <header className="app-header">
         <h1>Software Team Builder IA (MindFactory)</h1>
         <div className="user-info">
           <span>Bienvenido, {username}!</span>
           <button onClick={handleLogout} className="logout-button">Cerrar Sesión</button>
         </div>
       </header>
       <main>
         <p className="app-description">Describe tu proyecto, define la estructura del equipo deseada, establece un presupuesto y selecciona tecnologías clave (opcional). La IA te recomendará el equipo técnico óptimo de MindFactory.</p>
         <form onSubmit={handleSubmit} className="team-builder-form">
            <div className="form-section">
              <h2>1. Detalles del Proyecto</h2>
              <div className="form-group">
                <label htmlFor="description">Descripción del Proyecto:</label>
                <textarea id="description" name="description" value={formData.description} onChange={handleInputChange} rows="4" placeholder="Ej: Necesitamos un equipo para migrar..." required />
              </div>
              <div className="form-group">
                <label htmlFor="budget">Presupuesto Total Estimado ($):</label>
                <input type="number" id="budget" name="budget" value={formData.budget} onChange={handleInputChange} min="1" step="10000" required />
              </div>
            </div>
            <div className="form-section">
              <h2>2. Estructura del Equipo (Nº Personas)</h2>
              <div className="role-structure-grid">
                {UIRoles.map(role => (
                  <div className="form-group" key={role}>
                    <label htmlFor={`role-${role}`}>{role.replace(/ /g, '-').split('-').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}:</label>
                    <input type="number" id={`role-${role}`} name={`role-${role}`} min="0" value={formData.roles[role]} onChange={(e) => handleRoleCountChange(role, e.target.value)} placeholder="0"/>
                  </div>
                ))}
              </div>
            </div>
            <div className="form-section tech-selection">
              <h2>3. Tecnologías Clave (Opcional)</h2>
              {UIRoles.map(role => (
                formData.roles[role] > 0 && (
                  <div key={`techgroup-${role}`} className="tech-group">
                    <h4>{role.replace(/ /g, '-').split('-').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}</h4>
                    <div className="tech-checkboxes">
                      {(availableTechsByRole[role] || []).map(tech => (
                        <label key={`${role}-${tech}`} className="tech-label">
                          <input type="checkbox" value={tech} checked={formData.techs[role]?.includes(tech) || false} onChange={() => handleTechToggle(role, tech)} /> {tech}
                        </label>
                      ))}
                       {(availableTechsByRole[role] === undefined || availableTechsByRole[role].length === 0) && (<p className="no-techs-note">No hay tecnologías específicas predefinidas.</p>)}
                    </div>
                  </div>
                )
              ))}
            </div>
            {inferredTechsUI.length > 0 && (
                <div className="inferred-techs-display card">
                    <h4>Tecnologías Inferidas (Detectadas en la Descripción):</h4>
                    <p>{inferredTechsUI.join(', ')}</p>
                    <small><i>Estas tecnologías también se consideran en la recomendación.</i></small>
                </div>
            )}
            <div className="submit-section">
              <button type="submit" disabled={loading} className="generate-button">{loading ? 'Generando Equipo...' : 'Generar Recomendación'}</button>
              {error && <div className="error-message form-error">{error}</div>}
            </div>
         </form>
         {!loading && teamResult && !error && (
             <div className="team-results card">
                 <h2>Equipo Recomendado</h2>
                 {teamResult.presupuesto && ( <div className="result-section budget-info"> <h3>Presupuesto</h3> <p>Total Solicitado: <span>${(teamResult.presupuesto.total ?? 0).toLocaleString('es-AR')}</span></p> <p>Utilizado Estimado: <span>${(teamResult.presupuesto.utilizado ?? 0).toLocaleString('es-AR')}</span></p> <p>Restante Estimado: <span className={(teamResult.presupuesto.restante ?? 0) < 0 ? 'negative-budget' : ''}>${(teamResult.presupuesto.restante ?? 0).toLocaleString('es-AR')}</span> ({((teamResult.presupuesto.porcentaje_utilizado ?? 0) * 100).toFixed(1)}% usado)</p> </div> )}
                 {(teamResult.analisis_equipo || teamResult.status_message) && ( <div className="result-section analysis-info"> <h3>Análisis / Estado</h3> <p>{teamResult.analisis_equipo || teamResult.status_message}</p> </div> )}
                 <div className="result-section">
                    <h3>Miembros del Equipo ({teamResult.equipo?.length || 0})</h3>
                    {teamResult.equipo?.length > 0 ? (
                        <div className="team-members-grid">
                            {teamResult.equipo.map((member) => (
                                <div key={member.id} className="member-card">
                                    <h4>{member.nombre || member.email} <span className="member-level"> ({member.seniority_original || member.seniority_normalizado || 'N/A'})</span></h4>
                                    <p><strong>Rol Asignado:</strong> <span className="member-role">{member.rol_asignado_display || member.rol_asignado}</span></p>
                                    {member.puesto_original && member.puesto_original.toLowerCase() !== (member.rol_asignado_display || '').toLowerCase() && (<p><small><i>Puesto Original: {member.puesto_original}</i></small></p>)}
                                    <p><strong>Años Exp (Est.):</strong> {member.anos_experiencia ?? 'N/A'}</p>
                                    <p><strong>Salario (Est.):</strong> <span className="member-salary">${(member.salario ?? 0).toLocaleString('es-AR')}</span></p>
                                    <p><strong>Score Relevancia:</strong> {member.score?.toFixed(3) ?? 'N/A'}</p>
                                    <p className="member-techs"><strong>Tecnologías:</strong> {member.tecnologias_conocidas?.length > 0 ? member.tecnologias_conocidas.join(', ') : 'N/A'}</p>
                                </div>
                            ))}
                        </div>
                    ) : (<p className="no-members-found">No se encontraron miembros adecuados para la estructura y presupuesto definidos.</p>)}
                 </div>
                 {teamResult.metricas && (
                    <div className="result-section metrics-info">
                        <h3>Métricas del Equipo Recomendado</h3>
                        <p>Score Promedio: {teamResult.metricas.promedio_puntaje?.toFixed(3) ?? 'N/A'}</p>
                        <p>Roles Solicitados: {Object.entries(teamResult.metricas.roles_solicitados || {}).map(([r,c])=>`${r}(${c})`).join(', ') || 'Ninguno'}</p>
                        <p>Roles Cubiertos: {Object.entries(teamResult.metricas.roles_cubiertos || {}).map(([r,c])=>`${r}(${c})`).join(', ') || 'Ninguno'}</p>
                        {teamResult.metricas.tecnologias_faltantes?.length > 0 && (<p className="warning-techs"><strong>Posibles Tecnologías Faltantes:</strong><br/>{teamResult.metricas.tecnologias_faltantes.join(', ')}</p>)}
                    </div>
                 )}
             </div>
         )}
       </main>
       <footer className="app-footer">
           <p>© {new Date().getFullYear()} MindFactory - Software Team Builder</p>
       </footer>
    </div>
  );
}

export default App;