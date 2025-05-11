import React, { useState } from 'react';
import './LoginPage.css'; // Asegúrate que este archivo CSS existe

// Recibe onLoginSuccess y onSwitchToRegister de App.jsx
function LoginPage({ onLoginSuccess, onSwitchToRegister }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      // URL del endpoint de login (incluye /api)
      const response = await fetch('https://software-team-builder.onrender.com/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (response.ok) {
        console.log('Login successful:', data);
        onLoginSuccess(data.username); // Llama a la función del padre en caso de éxito
      } else {
        // Muestra el error específico del backend
        setError(data.detail || `Error ${response.status}: ${response.statusText}`);
        console.error('Login failed:', data);
      }
    } catch (err) {
      console.error('Network or fetch error during login:', err);
      setError('Error de conexión al intentar iniciar sesión.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-container"> {/* Clase contenedora */}
      <form onSubmit={handleSubmit} className="login-form"> {/* Clase del formulario */}
        <h2>Iniciar Sesión</h2>
        {error && <p className="error-message">{error}</p>} {/* Mensaje de error */}

        <div className="form-group"> {/* Grupo para usuario */}
          <label htmlFor="username">Usuario:</label>
          <input
            type="text"
            id="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            disabled={isLoading}
            autoComplete="username" // Ayuda a navegadores
          />
        </div>

        <div className="form-group"> {/* Grupo para contraseña */}
          <label htmlFor="password">Contraseña:</label>
          <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            disabled={isLoading}
            autoComplete="current-password" // Ayuda a navegadores
          />
        </div>

        <button type="submit" disabled={isLoading} className="login-button"> {/* Botón de login */}
          {isLoading ? 'Ingresando...' : 'Ingresar'}
        </button>

        {/* Enlace para cambiar a la vista de registro */}
        <p className="switch-link">
          ¿No tienes cuenta?{' '}
          <button
            type="button"
            onClick={onSwitchToRegister} // Llama a la función del padre
            className="link-button" // Clase para estilo de enlace
            disabled={isLoading} // Deshabilitar si está cargando
          >
            Regístrate aquí
          </button>
        </p>
      </form>
    </div>
  );
}

export default LoginPage;