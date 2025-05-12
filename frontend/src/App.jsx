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

    console.log("handleSubmit: Iniciando fetch para el backend.");
    console.log("handleSubmit: requestBody construido:", requestBody);

    try {
      const bodyString = JSON.stringify(requestBody);
      console.log("handleSubmit: JSON.stringify(requestBody) exitoso.");

      // ****************************************************************************
      // CAMBIO IMPORTANTE: URL ABSOLUTA DEL BACKEND PARA /api/teams/generate
      // ****************************************************************************
      const backendApiUrl_GenerateTeam = 'https://software-team-builder.onrender.com/api/teams/generate';
      // ****************************************************************************

      // Similarmente, para las otras llamadas API (login, register) también deberías usar URLs absolutas
      // o una variable de entorno como VITE_API_BASE_URL. Por ahora, solo corrijo esta.
      // Si RegisterPage y LoginPage usan URLs relativas, también necesitarán corrección.

      console.log(`handleSubmit: Fetching POST ${backendApiUrl_GenerateTeam}`);

      const response = await fetch(backendApiUrl_GenerateTeam, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: bodyString
      });

      console.log(`handleSubmit: Fetch respondió con status ${response.status} desde ${backendApiUrl_GenerateTeam}`);

      const responseText = await response.text();
      console.log("handleSubmit: Texto CRUDO de la respuesta del servidor:", responseText);

      let responseData;
      if (!responseText || responseText.trim() === "") {
        if (response.ok) {
            console.warn("handleSubmit: Respuesta OK (2xx) pero cuerpo vacío desde el backend.");
            throw new Error("El backend devolvió una respuesta OK pero vacía, y se esperaba JSON.");
        } else {
            throw new Error(`Error del backend: ${response.status} ${response.statusText} con cuerpo de respuesta vacío.`);
        }
      }

      try {
        responseData = JSON.parse(responseText);
      } catch (parseError) {
        console.error("handleSubmit: Error al parsear la respuesta JSON del backend:", parseError);
        throw new Error(`Respuesta inválida o no JSON del backend. Texto recibido (primeros 200 chars): '${responseText.substring(0, 200)}'`);
      }

      if (!response.ok) {
        console.error("handleSubmit: Error del backend (status no OK):", responseData);
        throw new Error(responseData.detail || responseData.message || `Error del backend: ${response.status}`);
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
    // Asegúrate de que LoginPage y RegisterPage también usen URLs absolutas para sus fetch
    // o una estrategia de VITE_API_BASE_URL si prefieres.
    // Ejemplo para LoginPage (deberás pasar la URL base o modificarlo internamente):
    // <LoginPage onLoginSuccess={handleLoginSuccess} onSwitchToRegister={switchToRegister} apiBaseUrl="https://software-team-builder.onrender.com" />
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