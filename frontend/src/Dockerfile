# frontend/src/Dockerfile (MODIFICADO)
# frontend/src/Dockerfile

# --- Stage 1: Build ---
    FROM node:18-alpine AS builder
    WORKDIR /app
    
    # Copiar archivos de dependencias DESDE el contexto (frontend/src/)
    COPY package.json package-lock.json ./
    RUN npm install
    
    # Copiar TODO el resto DESDE el contexto (frontend/src/)
    # Esto incluye ./src (con App.jsx, etc.), ./public, vite.config.js, etc.
    # EXCEPTO este Dockerfile y nginx.conf si no están en subdirectorios.
    COPY . .
    
    # Construir la aplicación (asume salida en 'dist')
    RUN npm run build
    
    # --- Stage 2: Production ---
    FROM nginx:stable-alpine
    
    # Copiar build desde 'builder'
    COPY --from=builder /app/dist /usr/share/nginx/html
    
    # Copiar nginx.conf DESDE el contexto (frontend/src/)
    # Asegúrate que nginx.conf esté en frontend/src/nginx.conf
    COPY nginx.conf /etc/nginx/conf.d/default.conf
    
    EXPOSE 80
    CMD ["nginx", "-g", "daemon off;"]