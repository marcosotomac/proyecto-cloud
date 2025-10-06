# 🚀 Guía de Deployment en AWS Amplify

## 📋 Tabla de Contenidos

1. [Prerequisitos](#prerequisitos)
2. [Configuración del Proyecto](#configuración-del-proyecto)
3. [Deployment con SSG (Estático)](#deployment-con-ssg-estático)
4. [Deployment con SSR (Dinámico)](#deployment-con-ssr-dinámico)
5. [Variables de Entorno](#variables-de-entorno)
6. [Troubleshooting](#troubleshooting)

---

## 📌 Prerequisitos

- ✅ Cuenta de AWS Academy o AWS personal
- ✅ Repositorio Git (GitHub, GitLab, Bitbucket, CodeCommit)
- ✅ Node.js 20+ instalado localmente
- ✅ pnpm instalado: `npm install -g pnpm`

---

## ⚙️ Configuración del Proyecto

### 1️⃣ Crear archivo `amplify.yml`

Crea el archivo en la raíz del proyecto frontend:

```bash
touch frontend/amplify.yml
```

**Contenido para SSG (Recomendado para AWS Academy):**

```yaml
version: 1
frontend:
  phases:
    preBuild:
      commands:
        # Instalar pnpm globalmente
        - npm install -g pnpm@9
        # Instalar dependencias usando lockfile
        - pnpm install --frozen-lockfile
    build:
      commands:
        # Build para producción
        - pnpm run build
  artifacts:
    # Para Static Export (output: 'export')
    baseDirectory: out
    files:
      - "**/*"
  cache:
    paths:
      - node_modules/**/*
      - .pnpm-store/**/*
```

**Contenido para SSR (Next.js completo):**

```yaml
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - npm install -g pnpm@9
        - pnpm install --frozen-lockfile
    build:
      commands:
        - pnpm run build
  artifacts:
    # Para build estándar de Next.js
    baseDirectory: .next
    files:
      - "**/*"
  cache:
    paths:
      - node_modules/**/*
      - .next/cache/**/*
      - .pnpm-store/**/*
```

---

## 🎯 Deployment con SSG (Estático)

### Ventajas

- ✅ **Más barato** (solo S3 + CloudFront)
- ✅ **Más rápido** (todo pre-renderizado)
- ✅ **Ideal para AWS Academy** (pocos recursos)
- ✅ **Mejor rendimiento**

### Desventajas

- ❌ No hay Server-Side Rendering
- ❌ No hay API Routes
- ❌ No hay ISR (Incremental Static Regeneration)

### Pasos:

#### 1. Modificar `next.config.ts`

```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export", // 🔴 Activar export estático

  images: {
    unoptimized: true, // 🔴 Necesario para static export
  },

  // Si usas variables de entorno del lado del cliente
  env: {
    NEXT_PUBLIC_API_URL:
      process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  },

  // Configuración de Turbopack (opcional)
  turbopack: {
    root: "/Users/marcosotomaceda/Desktop/cloud-proyect/frontend",
  },
};

export default nextConfig;
```

#### 2. Verificar rutas dinámicas

Si tienes rutas dinámicas como `[id].tsx`, necesitas generar las páginas estáticas:

```typescript
// app/dashboard/analytics/[id]/page.tsx
export async function generateStaticParams() {
  return [
    { id: "1" },
    { id: "2" },
    // ... todas las IDs que necesites
  ];
}
```

#### 3. Test local del build estático

```bash
cd frontend
pnpm run build
```

Esto debe generar la carpeta `out/` con archivos HTML estáticos.

#### 4. Verificar el output

```bash
ls -la out/
# Deberías ver:
# - index.html
# - _next/
# - dashboard/
# - login/
# - register/
```

#### 5. Deploy en AWS Amplify

**Opción A: Desde la Consola de AWS**

1. Ir a [AWS Amplify Console](https://console.aws.amazon.com/amplify/)
2. Click en **"New app"** → **"Host web app"**
3. Seleccionar **GitHub** (o tu provider)
4. Autorizar AWS Amplify a acceder a tu repositorio
5. Seleccionar el repositorio: `marcosotomac/proyecto-cloud`
6. Seleccionar la rama: `main`
7. Configurar build settings:
   - **App root directory**: `frontend`
   - Amplify detectará automáticamente el `amplify.yml`
8. Click en **"Advanced settings"** y agregar variables de entorno
9. Click en **"Save and deploy"**

**Opción B: Desde AWS CLI**

```bash
# Instalar AWS Amplify CLI
npm install -g @aws-amplify/cli

# Configurar credenciales
amplify configure

# Inicializar proyecto
cd frontend
amplify init

# Agregar hosting
amplify add hosting

# Seleccionar: Hosting with Amplify Console
# Deploy
amplify publish
```

---

## 🚀 Deployment con SSR (Dinámico)

### Ventajas

- ✅ Server-Side Rendering completo
- ✅ API Routes funcionales
- ✅ ISR (Incremental Static Regeneration)
- ✅ Todas las features de Next.js

### Desventajas

- ❌ **Más costoso** (usa Lambda@Edge)
- ❌ Más lento en cold starts
- ❌ **No recomendado para AWS Academy** (consume muchos créditos)

### Pasos:

#### 1. Usar `next.config.ts` por defecto

```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // NO uses 'output: export'

  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**",
      },
    ],
  },

  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },
};

export default nextConfig;
```

#### 2. Usar el `amplify.yml` para SSR

```yaml
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - npm install -g pnpm@9
        - pnpm install --frozen-lockfile
    build:
      commands:
        - pnpm run build
  artifacts:
    baseDirectory: .next
    files:
      - "**/*"
  cache:
    paths:
      - node_modules/**/*
      - .next/cache/**/*
```

#### 3. Deploy siguiendo los mismos pasos de SSG

---

## 🔐 Variables de Entorno

### En AWS Amplify Console:

1. Ir a tu app en Amplify
2. Click en **"Environment variables"**
3. Agregar las siguientes variables:

```bash
# Node version
NODE_VERSION=20.19.19

# API Gateway URL (reemplaza con tu URL real)
NEXT_PUBLIC_API_URL=https://tu-api-gateway.execute-api.us-east-1.amazonaws.com

# Otras variables si las tienes
NEXT_PUBLIC_GATEWAY_URL=https://tu-gateway.com
```

### En local (`.env.local`):

```bash
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**⚠️ IMPORTANTE**: Nunca commitees `.env.local` al repositorio.

---

## 🐛 Troubleshooting

### Error: "pnpm: command not found"

**Solución**: Asegúrate de que el `amplify.yml` incluya:

```yaml
preBuild:
  commands:
    - npm install -g pnpm@9
```

### Error: "Image Optimization using Next.js' default loader is not compatible with 'output: export'"

**Solución**: Agrega a `next.config.ts`:

```typescript
images: {
  unoptimized: true,
}
```

### Error: Build falla en Amplify pero funciona localmente

**Solución**:

1. Verifica la versión de Node:

```yaml
# En amplify.yml
NODE_VERSION=20
```

2. Limpia caché:

```bash
pnpm clean
rm -rf node_modules .next
pnpm install
pnpm run build
```

### Error: "Module not found: next-themes/dist/types"

**Solución**: Ya está corregido en `theme-provider.tsx`:

```typescript
import {
  ThemeProvider as NextThemesProvider,
  type ThemeProviderProps,
} from "next-themes";
```

### Error: Rutas no funcionan después del deploy

**Solución**: Para SSG, asegúrate de configurar redirects en Amplify:

1. Ir a **App settings** → **Rewrites and redirects**
2. Agregar:

```json
[
  {
    "source": "/<*>",
    "target": "/index.html",
    "status": "404-200",
    "condition": null
  }
]
```

### Error: Variables de entorno no se cargan

**Solución**:

1. Las variables deben tener prefijo `NEXT_PUBLIC_` para estar disponibles en el cliente
2. Reconstruir la app después de agregar variables en Amplify

---

## 📊 Comparación de Costos (AWS Academy)

| Feature                                | SSG (Static) | SSR (Server)          |
| -------------------------------------- | ------------ | --------------------- |
| **S3 Storage**                         | ~$0.023/GB   | ~$0.023/GB            |
| **CloudFront**                         | ~$0.085/GB   | ~$0.085/GB            |
| **Lambda@Edge**                        | ❌ No usa    | ✅ ~$0.60/1M requests |
| **Total estimado (1000 usuarios/mes)** | ~$5-10       | ~$50-100              |

**Recomendación para AWS Academy**: Usa **SSG** para evitar consumir créditos rápidamente.

---

## 🎯 Checklist Final

Antes de hacer deploy, verifica:

- [ ] ✅ `pnpm run build` funciona localmente sin errores
- [ ] ✅ `amplify.yml` está configurado correctamente
- [ ] ✅ Variables de entorno configuradas en Amplify Console
- [ ] ✅ `.env.local` NO está en Git (revisar `.gitignore`)
- [ ] ✅ `next.config.ts` tiene la configuración correcta (export para SSG)
- [ ] ✅ Todos los cambios están commiteados y pusheados
- [ ] ✅ Repositorio conectado a AWS Amplify

---

## 📚 Recursos Adicionales

- [Next.js Static Export](https://nextjs.org/docs/app/building-your-application/deploying/static-exports)
- [AWS Amplify Hosting](https://docs.aws.amazon.com/amplify/latest/userguide/welcome.html)
- [Next.js on AWS Amplify](https://aws.amazon.com/blogs/mobile/host-a-next-js-ssr-app-with-real-time-data-on-aws-amplify/)

---

## 🆘 Soporte

Si tienes problemas:

1. Revisa los logs en Amplify Console → Build logs
2. Verifica que el build local funciona: `pnpm run build`
3. Compara el `amplify.yml` con esta guía
4. Verifica las variables de entorno

**Build exitoso**: El último build local fue exitoso ✅

```
✓ Compiled successfully in 2.6s
✓ Checking validity of types
✓ Collecting page data
✓ Generating static pages (12/12)
```

---

**Creado**: 5 de Octubre, 2025  
**Proyecto**: Cloud Project - Next.js Frontend  
**Autor**: Marcos Soto Maceda
