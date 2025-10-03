# Quick Start Guide - Full Stack Application

## Complete System Overview

This guide will help you start the entire LLM Microservices Platform with both backend and frontend.

## Prerequisites

- Docker and Docker Compose
- Node.js 18+ and pnpm
- Ports available: 3000 (frontend), 8080 (gateway), 3000, 8000, 8002, 8005 (services)

## Starting the Application

### Step 1: Start Backend Services

```bash
# From the project root
docker compose up -d

# Verify all services are running
docker ps

# Expected: 9 containers running
# - postgres, mongo, minio
# - users-service, llm-chat-service, image-service, text-to-speech-service, analytics-service
# - gateway-api
```

### Step 2: Wait for Services to be Ready

```bash
# Check gateway health
curl http://localhost:8080/health

# Should return: {"status":"healthy","services":{"users":"healthy","chat":"healthy","image":"healthy","speech":"healthy","analytics":"healthy"}}
```

### Step 3: Start Frontend

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (first time only)
pnpm install

# Start development server
pnpm dev
```

### Step 4: Access the Application

Open your browser and navigate to:

```
http://localhost:3000
```

You'll be redirected to the login page.

## First Time Setup

### 1. Register a New User

- Click "Sign up" on the login page
- Enter your details:
  - Full Name: `Test User`
  - Email: `user@example.com`
  - Password: `Password123!`
- Click "Create Account"

You'll be automatically logged in and redirected to the chat page.

### 2. Explore Features

**Chat**:

- Select a model from the dropdown (default: gpt-4o-mini)
- Type a message and send
- View conversation history
- Create new sessions with the + button

**Images**:

- Navigate to Images from the top menu
- Enter a prompt: "A beautiful sunset over the ocean"
- Click Generate
- Wait for the image to be generated
- Click to preview or download

**Speech**:

- Navigate to Speech from the top menu
- Select a language (default: English)
- Enter text to convert
- Click Generate Speech
- Play audio or download

**Analytics**:

- Navigate to Analytics from the top menu
- View your usage statistics
- See service breakdowns
- Check system metrics

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  Frontend (Next.js)                                     │
│  http://localhost:3000                                  │
│                                                         │
└───────────────────────┬─────────────────────────────────┘
                        │
                        │ HTTP/REST
                        │
┌───────────────────────▼─────────────────────────────────┐
│                                                         │
│  API Gateway (FastAPI)                                  │
│  http://localhost:8080                                  │
│                                                         │
└───────────────────────┬─────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┬────────────┐
        │               │               │            │
┌───────▼──────┐ ┌─────▼─────┐ ┌──────▼─────┐ ┌────▼────┐
│              │ │           │ │            │ │         │
│ Users        │ │ Chat      │ │ Image      │ │ Speech  │
│ Service      │ │ Service   │ │ Service    │ │ Service │
│              │ │           │ │            │ │         │
│ :3000        │ │ :8002     │ │ :8000      │ │ :8000   │
└──────────────┘ └───────────┘ └────────────┘ └─────────┘
```

## Available Services

| Service     | Port | Technology | Database   |
| ----------- | ---- | ---------- | ---------- |
| Frontend    | 3000 | Next.js 15 | -          |
| API Gateway | 8080 | FastAPI    | -          |
| Users       | 3000 | NestJS     | PostgreSQL |
| Chat        | 8002 | FastAPI    | MongoDB    |
| Image       | 8000 | FastAPI    | MinIO      |
| Speech      | 8000 | FastAPI    | MinIO      |
| Analytics   | 8005 | FastAPI    | MongoDB    |

## Environment Configuration

### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8080/api
```

### Backend Services

All backend environment variables are configured in `docker-compose.yml`

## Troubleshooting

### Frontend won't start

```bash
# Clear cache and reinstall
rm -rf .next node_modules
pnpm install
pnpm dev
```

### API Gateway errors

```bash
# Check gateway logs
docker logs gateway-api

# Restart gateway
docker restart gateway-api
```

### Services not healthy

```bash
# Check individual service logs
docker logs users-service
docker logs llm-chat-service
docker logs image-service
docker logs text-to-speech-service
docker logs analytics-service

# Restart all services
docker compose restart
```

### Database connection errors

```bash
# Check database containers
docker ps | grep -E "postgres|mongo|minio"

# Restart databases
docker compose restart postgres mongo minio
```

### CORS errors in browser

- Ensure API Gateway is running on http://localhost:8080
- Check browser console for specific CORS error
- Verify CORS configuration in gateway_api/main.py

## Development Workflow

### 1. Backend Development

```bash
# Watch backend logs
docker compose logs -f gateway-api

# Restart a service after code changes
docker compose restart gateway-api

# Rebuild after dependency changes
docker compose up -d --build gateway-api
```

### 2. Frontend Development

```bash
# Frontend auto-reloads on file changes
pnpm dev

# Build for production
pnpm build

# Run production build
pnpm start
```

## Testing

### Test Backend Endpoints

```bash
# Login
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"Password123!"}'

# Get profile (use token from login)
curl http://localhost:8080/api/auth/profile \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get chat models
curl http://localhost:8080/api/chat/models \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Test Frontend

1. Open http://localhost:3000
2. Open browser DevTools (F12)
3. Go to Network tab
4. Perform actions in the app
5. Verify API calls are successful (200 status codes)

## Production Deployment

### Frontend

```bash
cd frontend
pnpm build
pnpm start
```

### Backend

```bash
# Use production docker-compose
docker compose -f docker-compose.prod.yml up -d
```

## Useful Commands

```bash
# View all containers
docker ps -a

# View logs for all services
docker compose logs -f

# Stop all services
docker compose down

# Stop and remove volumes (CAUTION: deletes data)
docker compose down -v

# Restart specific service
docker compose restart service-name

# Check frontend build
cd frontend && pnpm build

# Check API Gateway health
curl http://localhost:8080/health

# Monitor resource usage
docker stats
```

## Default Credentials

After registration, you can use any email/password combination. Example:

- Email: `test@example.com`
- Password: `Test123!`

## Features Checklist

After starting the application, verify these features work:

- [ ] User registration
- [ ] User login
- [ ] JWT token refresh
- [ ] Chat with AI (multiple models)
- [ ] Create new chat sessions
- [ ] View chat history
- [ ] Generate images with DALL-E
- [ ] Download images
- [ ] Generate speech (text-to-speech)
- [ ] Download audio files
- [ ] View user analytics
- [ ] View service statistics
- [ ] View system metrics
- [ ] Logout functionality

## Support

For issues or questions:

1. Check logs: `docker compose logs -f`
2. Verify all containers are healthy: `docker ps`
3. Check frontend console: Browser DevTools
4. Review API Gateway health: `curl http://localhost:8080/health`

## Next Steps

1. ✅ Start backend: `docker compose up -d`
2. ✅ Start frontend: `cd frontend && pnpm dev`
3. ✅ Register a user at http://localhost:3000
4. ✅ Explore all features (chat, images, speech, analytics)
5. 🚀 Build something amazing!

---

**Congratulations!** 🎉 You now have a fully functional LLM Microservices Platform with a modern Next.js frontend!
