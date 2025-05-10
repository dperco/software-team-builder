import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Configuración dinámica para desarrollo con ngrok
const NGROK_HOST = process.env.NGROK_HOST || 'e893-186-13-125-2.ngrok-free.app';

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    allowedHosts: [
      NGROK_HOST,
      'localhost',
      '127.0.0.1',
      '.ngrok-free.app' // Permite cualquier subdominio ngrok
    ],
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api'),
        secure: false,
        ws: true
      }
    }
  }
})