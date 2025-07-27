# CloudWatch Pro - Dashboard Dockerfile
# Multi-stage build dla optymalizacji rozmiaru obrazu

# Stage 1: Build
FROM node:20-alpine AS builder

# Ustawienie katalogu roboczego
WORKDIR /app

# Kopiowanie package.json i pnpm-lock.yaml
COPY package.json pnpm-lock.yaml ./

# Instalacja pnpm globalnie
RUN npm install -g pnpm

# Instalacja zależności
RUN pnpm install --frozen-lockfile

# Kopiowanie kodu źródłowego
COPY . .

# Budowanie aplikacji
RUN pnpm run build

# Stage 2: Production
FROM nginx:alpine

# Kopiowanie plików zbudowanej aplikacji
COPY --from=builder /app/dist /usr/share/nginx/html

# Kopiowanie konfiguracji nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Eksponowanie portu
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

# Komenda uruchomienia
CMD ["nginx", "-g", "daemon off;"]

