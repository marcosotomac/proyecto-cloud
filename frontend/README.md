# LLM Microservices Platform - Frontend

A modern, responsive frontend application for the LLM Microservices Platform built with Next.js 15, React 19, and shadcn/ui components.

## Features

### 🔐 Authentication

- User registration and login
- JWT-based authentication with automatic token refresh
- Protected routes with redirect to login
- Persistent sessions using localStorage

### 💬 Chat Interface

- Real-time chat with multiple LLM models (GPT-4, GPT-3.5, etc.)
- Session management and history
- Model selection dropdown
- Beautiful message bubbles with user/assistant distinction
- Auto-scrolling message list

### 🎨 Image Generation

- AI-powered image generation using DALL-E
- Image gallery with status tracking
- Download functionality
- Full-screen image preview
- Real-time status polling for generation progress

### 🔊 Speech Synthesis

- Text-to-speech conversion
- Multiple language support (8+ languages)
- Audio player with controls
- Download audio files
- Status tracking for generation

### 📊 Analytics Dashboard

- User activity statistics
- Service usage metrics
- System-wide analytics
- Visual charts and graphs
- Daily usage trends

## Tech Stack

- **Framework**: Next.js 15 (App Router)
- **UI Library**: React 19
- **Styling**: Tailwind CSS
- **Components**: shadcn/ui
- **Icons**: Lucide React
- **HTTP Client**: Axios
- **Notifications**: Sonner (toast)
- **Language**: TypeScript

## Installation

1. **Install dependencies**:

   ```bash
   cd frontend
   pnpm install
   ```

2. **Configure environment**:
   Create `.env.local` file:

   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8080/api
   ```

3. **Run development server**:

   ```bash
   pnpm dev
   ```

4. **Open browser**:
   Navigate to http://localhost:3000

## API Endpoints Used

**Authentication**:

- POST `/auth/register` - User registration
- POST `/auth/login` - User login
- POST `/auth/logout` - User logout
- GET `/auth/profile` - Get user profile
- POST `/auth/refresh` - Refresh access token

**Chat**:

- POST `/chat` - Send message
- GET `/chat/sessions` - Get all sessions
- GET `/chat/sessions/{id}` - Get session details
- GET `/chat/models` - Get available models

**Image**:

- POST `/image/generate` - Generate image
- GET `/image/{id}` - Get image details
- GET `/image/{id}/download` - Download image

**Speech**:

- POST `/speech/generate` - Generate speech
- GET `/speech/{id}` - Get speech details
- GET `/speech/{id}/download` - Download audio

**Analytics**:

- GET `/analytics/user/me` - User statistics
- GET `/analytics/service/{type}` - Service statistics
- GET `/analytics/system` - System statistics
- GET `/analytics/usage` - Usage statistics

## Building for Production

```bash
# Build the application
pnpm build

# Start production server
pnpm start
```
