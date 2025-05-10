import React, { useState } from 'react';
import './RegisterPage.css'; // Asegúrate que este archivo CSS exista

// Recibe onSwitchToLogin y onRegisterSuccess de App.jsx
function RegisterPage({ onSwitchToLogin, onRegisterSuccess }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');   
    setSuccessMessage('');

    // Validación Frontend básica
    if (password !== confirmPassword) {
      setError('Las contraseñas no coinciden.');
      return;
    }
    if (password.length < 6) {
      setError('La contraseña debe tener al menos 6 caracteres.');
      return;
    }
    if (!username || username.length < 3) {
        setError('El nombre de usuario debe tener al menos 3 caracteres.');
        return;
    }
    // Podrías añadir aquí validación de caracteres permitidos si quieres

    setIsLoading(true); // Inicia carga aquí, tras validación básica

    try {
       // URL del endpoint de registro (incluye /api)
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (response.ok) { // Estado 201 Created u otros 2xx
        setSuccessMessage(`Usuario '${data.username}' registrado. Redirigiendo a login...`);
        console.log('Registration successful:', data);
        setUsername(''); // Limpiar formulario
        setPassword('');
        setConfirmPassword('');
        if(onRegisterSuccess) onRegisterSuccess(data.username); // Llama a la función del padre

      } else {
        // Muestra el error específico del backend (ej. usuario ya existe)
        setError(data.detail || `Error ${response.status}: ${response.statusText}`);
        console.error('Registration failed:', data);
      }
    } catch (err) {
      console.error('Network or fetch error during registration:', err);
      setError('Error de conexión al intentar registrar.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="register-container"> {/* Clase contenedora */}
      <form onSubmit={handleSubmit} className="register-form"> {/* Clase del formulario */}
        <h2>Crear Cuenta</h2>
        {error && <p className="error-message">{error}</p>}
        {successMessage && <p className="success-message">{successMessage}</p>}

        <div className="form-group"> {/* Grupo para usuario */}
          <label htmlFor="reg-username">Usuario:</label>
          <input
            type="text"
            id="reg-username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            minLength="3"
            maxLength="50"
            disabled={isLoading || !!successMessage} // Deshabilitar si carga o si ya tuvo éxito
            placeholder="Mínimo 3 caracteres (letras, números, _)"
            autoComplete="username"
          />
        </div>

        <div className="form-group"> {/* Grupo para contraseña */}
          <label htmlFor="reg-password">Contraseña:</label>
          <input
            type="password"
            id="reg-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength="6"
            disabled={isLoading || !!successMessage}
            autoComplete="new-password"
          />
        </div>

        <div className="form-group"> {/* Grupo para confirmar contraseña */}
          <label htmlFor="reg-confirm-password">Confirmar Contraseña:</label>
          <input
            type="password"
            id="reg-confirm-password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            minLength="6"
            disabled={isLoading || !!successMessage}
            autoComplete="new-password"
          />
        </div>

        <button type="submit" disabled={isLoading || !!successMessage} className="register-button"> {/* Botón de registro */}
          {isLoading ? 'Registrando...' : 'Registrarse'}
        </button>

        {/* Enlace para volver a la vista de login */}
        <p className="switch-link">
          ¿Ya tienes cuenta?{' '}
          <button
            type="button"
            onClick={onSwitchToLogin} // Llama a la función del padre
            className="link-button" // Clase para estilo
            disabled={isLoading} // Deshabilitar si está cargando
          >
            Inicia Sesión aquí
          </button>
        </p>
      </form>
    </div>
  );
}

export default RegisterPage;