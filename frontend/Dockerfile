# Etapa 1: compilar con Vite
FROM node:22-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .

# Vite fija estas variables en el momento del build. Los valores por defecto
# apuntan a localhost para que la imagen funcione igual que en desarrollo.
ARG VITE_API_URL=http://localhost:8001
ARG VITE_ROLE_API_URL=http://localhost:8002
ARG VITE_NAV_API_URL=http://localhost:8003
ARG VITE_CHAT_API_URL=http://localhost:8004
ARG VITE_AGENTE_ORIENTACION_API_URL=http://localhost:8005
ENV VITE_API_URL=$VITE_API_URL \
    VITE_ROLE_API_URL=$VITE_ROLE_API_URL \
    VITE_NAV_API_URL=$VITE_NAV_API_URL \
    VITE_CHAT_API_URL=$VITE_CHAT_API_URL \
    VITE_AGENTE_ORIENTACION_API_URL=$VITE_AGENTE_ORIENTACION_API_URL
RUN npm run build

# Etapa 2: servir los estáticos con nginx
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80

