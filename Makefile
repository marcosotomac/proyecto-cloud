# LLM Microservices Platform - Makefile

.PHONY: help build up down logs clean test-auth test-image

# Variables
COMPOSE_FILE := docker-compose.yml
USERS_SERVICE := http://localhost:3000
IMAGE_SERVICE := http://localhost:8000
SPEECH_SERVICE := http://localhost:8001

help: ## Mostrar esta ayuda
	@echo "LLM Microservices Platform"
	@echo "=========================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Construir todas las imágenes
	docker compose -f $(COMPOSE_FILE) build

up: ## Levantar todos los servicios
	docker compose -f $(COMPOSE_FILE) up -d
	@echo "🚀 Servicios iniciados:"
	@echo "  - Users/Auth: $(USERS_SERVICE)"
	@echo "  - Text-to-Image: $(IMAGE_SERVICE)"
	@echo "  - Text-to-Speech: $(SPEECH_SERVICE)"
	@echo "  - MinIO Console: http://localhost:9001 (minio/minio123)"
	@echo "  - PostgreSQL: localhost:5432 (postgres/postgres)"

up-build: ## Construir y levantar todos los servicios
	docker compose -f $(COMPOSE_FILE) up -d --build

down: ## Detener todos los servicios
	docker compose -f $(COMPOSE_FILE) down

down-clean: ## Detener servicios y limpiar volúmenes
	docker compose -f $(COMPOSE_FILE) down -v
	docker system prune -f

logs: ## Ver logs de todos los servicios
	docker compose -f $(COMPOSE_FILE) logs -f

logs-users: ## Ver logs del servicio de usuarios
	docker compose -f $(COMPOSE_FILE) logs -f users-service

logs-image: ## Ver logs del servicio de imágenes
	docker compose -f $(COMPOSE_FILE) logs -f text-image-service

logs-speech: ## Ver logs del servicio de text-to-speech
	docker compose -f $(COMPOSE_FILE) logs -f text-speech-service

status: ## Ver estado de los servicios
	docker compose -f $(COMPOSE_FILE) ps

# Comandos de testing
test-auth: ## Probar endpoints de autenticación
	@echo "🧪 Probando autenticación..."
	@echo "1. Registrando usuario..."
	curl -X POST "$(USERS_SERVICE)/auth/register" \
		-H "Content-Type: application/json" \
		-d '{"email":"test@example.com","password":"password123"}' || true
	@echo "\n2. Iniciando sesión..."
	curl -X POST "$(USERS_SERVICE)/auth/login" \
		-H "Content-Type: application/json" \
		-d '{"email":"test@example.com","password":"password123"}'

test-image: ## Probar generación de imagen (anónimo)
	@echo "🖼️ Probando generación de imagen..."
	curl -X POST "$(IMAGE_SERVICE)/image/generate" \
		-H "Content-Type: application/json" \
		-d '{"prompt":"cute cyberpunk cat","size":"512x512"}'

test-image-auth: ## Probar generación de imagen con autenticación
	@echo "🔐 Probando generación de imagen autenticada..."
	@echo "Primero obtén un token con 'make test-auth' y úsalo:"
	@echo "curl -X POST '$(IMAGE_SERVICE)/image/generate' \\"
	@echo "  -H 'Content-Type: application/json' \\"
	@echo "  -H 'Authorization: Bearer YOUR_TOKEN' \\"
	@echo "  -d '{\"prompt\":\"authenticated image\",\"size\":\"512x512\"}'"

test-protected: ## Probar endpoint protegido
	@echo "🔒 Probando endpoint protegido..."
	@echo "Primero obtén un token con 'make test-auth' y úsalo:"
	@echo "curl -H 'Authorization: Bearer YOUR_TOKEN' '$(IMAGE_SERVICE)/admin/images'"

test-speech: ## Probar generación de audio (anónimo)
	@echo "🎤 Probando generación de audio..."
	curl -X POST "$(SPEECH_SERVICE)/tts/generate" \
		-H "Content-Type: application/json" \
		-d '{"prompt":"Hello, this is a test of text to speech synthesis","voice":"alloy"}'

test-speech-auth: ## Probar generación de audio con autenticación
	@echo "🔐 Probando generación de audio autenticada..."
	@echo "Primero obtén un token con 'make test-auth' y úsalo:"
	@echo "curl -X POST '$(SPEECH_SERVICE)/tts/generate' \\"
	@echo "  -H 'Content-Type: application/json' \\"
	@echo "  -H 'Authorization: Bearer YOUR_TOKEN' \\"
	@echo "  -d '{\"prompt\":\"Authenticated audio test\",\"voice\":\"nova\"}'"

healthcheck: ## Verificar salud de todos los servicios
	@echo "🏥 Verificando salud de servicios..."
	@echo "Users Service:"
	@curl -f $(USERS_SERVICE)/ 2>/dev/null && echo " ✅ OK" || echo " ❌ FAIL"
	@echo "Text-Image Service:"
	@curl -f $(IMAGE_SERVICE)/healthz 2>/dev/null && echo " ✅ OK" || echo " ❌ FAIL"
	@echo "Text-Speech Service:"
	@curl -f $(SPEECH_SERVICE)/healthz 2>/dev/null && echo " ✅ OK" || echo " ❌ FAIL"

clean: ## Limpiar contenedores, imágenes y volúmenes no utilizados
	docker compose -f $(COMPOSE_FILE) down -v --remove-orphans
	docker system prune -af --volumes

setup-dev: ## Configurar entorno de desarrollo
	@echo "🛠️ Configurando entorno de desarrollo..."
	@if [ ! -f ./users/.env ]; then cp ./users/.env.example ./users/.env; fi
	@if [ ! -f ./text_image_api/.env ]; then cp ./text_image_api/.env.example ./text_image_api/.env; fi
	@if [ ! -f ./text_speech_api/.env ]; then cp ./text_speech_api/.env.example ./text_speech_api/.env; fi
	@echo "✅ Archivos .env configurados"

# Comandos de desarrollo
dev-users: ## Ejecutar servicio de usuarios en modo desarrollo
	cd users && pnpm run start:dev

dev-image: ## Ejecutar servicio de imágenes en modo desarrollo
	cd text_image_api && python main.py

dev-speech: ## Ejecutar servicio de text-to-speech en modo desarrollo
	cd text_speech_api && python main.py

install-deps: ## Instalar dependencias de todos los servicios
	@echo "📦 Instalando dependencias..."
	cd users && pnpm install
	cd text_image_api && pip install -r requirements.txt
	cd text_speech_api && pip install -r requirements.txt