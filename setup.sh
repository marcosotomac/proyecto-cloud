#!/bin/bash

# 🚀 LLM Microservices - Setup Script
# Configura automáticamente el entorno de desarrollo

set -e

echo "🚀 Configurando LLM Microservices Platform..."

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_step() {
    echo -e "${BLUE}📋 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Verificar requisitos
print_step "Verificando requisitos del sistema..."

# Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker no está instalado. Instala Docker Desktop desde https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Docker Compose
if ! docker compose version &> /dev/null; then
    print_error "Docker Compose no está disponible. Actualiza Docker Desktop."
    exit 1
fi

# Node.js
if ! command -v node &> /dev/null; then
    print_warning "Node.js no detectado. Instala Node.js 18+ para desarrollo local."
fi

# Python
if ! command -v python3 &> /dev/null; then
    print_warning "Python 3 no detectado. Instala Python 3.11+ para desarrollo local."
fi

print_success "Requisitos verificados"

# Crear directorios necesarios
print_step "Creando directorios del proyecto..."

mkdir -p .env
mkdir -p data/postgres
mkdir -p data/minio
mkdir -p logs

print_success "Directorios creados"

# Generar claves JWT si no existen
print_step "Configurando claves JWT..."

if [ ! -f ".env/jwt-private.key" ]; then
    openssl genpkey -algorithm RSA -out .env/jwt-private.key -pkcs8 -pass pass:changeme
    print_success "Clave privada JWT generada"
else
    print_warning "Clave privada JWT ya existe"
fi

if [ ! -f ".env/jwt-public.key" ]; then
    openssl rsa -pubout -in .env/jwt-private.key -out .env/jwt-public.key -passin pass:changeme
    print_success "Clave pública JWT generada"
else
    print_warning "Clave pública JWT ya existe"
fi

# Crear archivo .env para users service
print_step "Configurando variables de entorno..."

cat > users/.env << EOF
# Database
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_USERNAME=postgres
DATABASE_PASSWORD=postgres
DATABASE_NAME=postgres

# JWT Configuration
JWT_SECRET=your-super-secret-jwt-key-change-in-production
JWT_PRIVATE_KEY_PATH=../.env/jwt-private.key
JWT_PUBLIC_KEY_PATH=../.env/jwt-public.key
JWT_PRIVATE_KEY_PASSPHRASE=changeme
JWT_EXPIRES_IN=15m
JWT_REFRESH_EXPIRES_IN=30d

# Application
PORT=3000
NODE_ENV=development
EOF

print_success "Archivo .env creado para users service"

# Crear archivo .env para text-image service
cat > text_image_api/.env << EOF
# Environment
ENVIRONMENT=development
LOG_LEVEL=INFO

# S3/MinIO Configuration
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minio
S3_SECRET_KEY=minio123
S3_BUCKET=llmhist-image-dev
S3_REGION=us-east-1

# Users Service Configuration
USERS_SERVICE_URL=http://localhost:3000
USERS_SERVICE_VERIFY_URL=http://localhost:3000/auth/verify

# JWT Public Key for verification
JWT_PUBLIC_KEY_PATH=../.env/jwt-public.key

# Pollinations API
POLLINATIONS_API_URL=https://image.pollinations.ai/prompt
EOF

print_success "Archivo .env creado para text-image service"

# Instalar dependencias si Node.js está disponible
if command -v node &> /dev/null && command -v pnpm &> /dev/null; then
    print_step "Instalando dependencias de users service..."
    cd users && pnpm install && cd ..
    print_success "Dependencias instaladas para users service"
elif command -v node &> /dev/null && command -v npm &> /dev/null; then
    print_step "Instalando dependencias de users service (usando npm)..."
    cd users && npm install && cd ..
    print_success "Dependencias instaladas para users service"
else
    print_warning "Skipping users service dependencies (Node.js/pnpm not available)"
fi

# Configurar entorno Python si está disponible
if command -v python3 &> /dev/null; then
    print_step "Configurando entorno Python..."
    cd text_image_api
    
    if [ ! -d ".venv" ]; then
        python3 -m venv .venv
        print_success "Virtual environment creado"
    fi
    
    source .venv/bin/activate
    pip install -r requirements.txt
    print_success "Dependencias Python instaladas"
    cd ..
else
    print_warning "Skipping Python setup (Python 3 not available)"
fi

# Construir imágenes Docker
print_step "Construyendo imágenes Docker..."

if docker compose build; then
    print_success "Imágenes Docker construidas exitosamente"
else
    print_error "Error construyendo imágenes Docker"
    exit 1
fi

# Mostrar información final
echo ""
echo "🎉 ¡Setup completado exitosamente!"
echo ""
echo "📋 Próximos pasos:"
echo ""
echo "1. 🚀 Iniciar servicios:"
echo "   make up"
echo ""
echo "2. 🔍 Verificar estado:"
echo "   make healthcheck"
echo ""
echo "3. 🧪 Probar autenticación:"
echo "   make test-auth"
echo ""
echo "4. 🖼️ Probar generación de imágenes:"
echo "   make test-image"
echo ""
echo "📚 Comandos útiles:"
echo "   make logs          # Ver logs de todos los servicios"
echo "   make down          # Detener servicios"
echo "   make clean         # Limpiar todo"
echo ""
echo "🌐 URLs después de iniciar:"
echo "   Users API:    http://localhost:3000"
echo "   Image API:    http://localhost:8000"
echo "   MinIO Console: http://localhost:9001 (minio/minio123)"
echo ""
print_success "¡Listo para desarrollar! 🚀"