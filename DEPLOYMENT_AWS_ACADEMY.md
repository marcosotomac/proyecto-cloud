# 🚀 Guía de Deployment Manual en AWS Academy (100% Consola Web)

Esta guía te ayudará a desplegar manualmente la aplicación de microservicios en AWS Academy utilizando **únicamente la consola web de AWS**, sin necesidad de SSH, terminal o línea de comandos. Todo se hará mediante clics en la interfaz gráfica de AWS.

El código se clonará automáticamente desde GitHub: `https://github.com/marcosoto⚠️ **Nota:** Es recomendable esperar a tener la IP pública antes de lanzar la instancia, o usar la IP asignada elásticamente si está disponible en AWS Academy.

### 5. Esperar la Inicialización (15-20 minutos)

El script de User Data se ejecuta automáticamente cuando la instancia arranca por primera vez. Este proceso incluye:

1. ✅ Instalación de Docker y Docker Compose
2. ✅ Instalación de Git
3. ✅ Clonación del repositorio desde GitHub
4. ✅ Creación de archivos .env con tus credenciales
5. ✅ Construcción de imágenes Docker (esto toma tiempo)
6. ✅ Inicio de todos los contenedores

**Monitorear el progreso:**

1. Ve a **EC2** → **Instances**
2. Selecciona tu instancia `microservices-app`
3. Haz clic en la pestaña **Status checks**
4. Espera a que ambos checks estén en 2/2 (verde)
5. Haz clic en **Actions** → **Monitor and troubleshoot** → **Get system log**
6. Busca líneas que indiquen:
   - "Cloning into 'proyecto-cloud'"
   - "Building"
   - "Creating"
   - "Started"

⏱️ **Tiempo estimado:** 15-20 minutos para completar todo el proceso
Utilizaremos Amazon S3 en lugar de MinIO para el almacenamiento de archivos.

---

## 📋 Tabla de Contenidos

1. [Requisitos Previos](#requisitos-previos)
2. [Información que Necesitas Preparar](#información-que-necesitas-preparar)
3. [Configuración de AWS Academy](#configuración-de-aws-academy)
4. [Creación y Configuración de S3 Buckets](#creación-y-configuración-de-s3-buckets)
5. [Lanzamiento de Instancia EC2](#lanzamiento-de-instancia-ec2)
6. [Verificación del Deployment](#verificación-del-deployment)
7. [Troubleshooting](#troubleshooting)

---

## 🔧 Requisitos Previos

- ✅ Cuenta de AWS Academy activa
- ✅ Navegador web (Chrome, Firefox, Safari, Edge)
- ✅ GitHub Personal Access Token para el servicio LLM

---

## 📝 Información que Necesitas Preparar

Antes de comenzar, ten a la mano:

### 1. GitHub Personal Access Token

- Tu token para acceder a GitHub Models API
- Lo configurarás en el script de deployment
- Formato: `ghp_XXXXXXXXXXXXXXXXXXXXX`

### 2. Credenciales de AWS Academy

Las obtendrás de AWS Academy → AWS Details → Show:

- **Access Key ID:** `ASIA...`
- **Secret Access Key:** `...`
- **Session Token:** `...`

### 3. Nombres de Buckets S3

Decide ahora los nombres (deben ser únicos globalmente):

- Bucket para imágenes: `tu-nombre-text-image-bucket`
- Bucket para audio: `tu-nombre-text-speech-bucket`

⚠️ Reemplaza `tu-nombre` con tu identificador único (ej: `juan-proyecto`, `maria-2024`, etc.)

---

## 🎓 Configuración de AWS Academy

### 1. Iniciar el Laboratorio

1. Abre tu navegador web
2. Inicia sesión en **AWS Academy**
3. Ve a tu curso y accede a **Learner Lab**
4. Haz clic en **Start Lab** y espera a que el indicador AWS 🟢 se ponga verde
5. Haz clic en **AWS** para abrir la consola de AWS en una nueva pestaña

### 2. Guardar Credenciales AWS (Importante)

1. En el Learner Lab, haz clic en **AWS Details**
2. Haz clic en **Show** junto a "AWS CLI"
3. **Copia y guarda** las tres credenciales en un archivo de texto en tu computadora:
   ```
   aws_access_key_id = ASIAXXXXXXXXXXXXXXXX
   aws_secret_access_key = XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
   aws_session_token = XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
   ```
4. Las necesitarás más adelante para configurar los servicios

⚠️ **Importante:** Estas credenciales expiran cuando termina la sesión del laboratorio

---

## 🪣 Creación y Configuración de S3 Buckets

### 1. Crear Buckets en S3

Accede a la consola de S3 y crea los siguientes buckets (reemplaza `tu-nombre` con tu identificador único):

1. **Para imágenes generadas:**

   - Nombre: `tu-nombre-text-image-bucket`
   - Región: `us-east-1` (o la región de tu preferencia)
   - Desmarcar "Block all public access" (para permitir acceso público a las imágenes)
   - Confirmar la advertencia de acceso público

2. **Para archivos de audio generados:**
   - Nombre: `tu-nombre-text-speech-bucket`
   - Región: `us-east-1` (la misma región)
   - Desmarcar "Block all public access"
   - Confirmar la advertencia de acceso público

### 2. Configurar Política de Bucket (Para ambos buckets)

Para cada bucket creado:

1. Ve al bucket → **Permissions** → **Bucket Policy**
2. Agrega la siguiente política (reemplaza `NOMBRE_DEL_BUCKET`):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::NOMBRE_DEL_BUCKET/*"
    }
  ]
}
```

### 3. Habilitar CORS (Para ambos buckets)

1. Ve al bucket → **Permissions** → **Cross-origin resource sharing (CORS)**
2. Agrega la siguiente configuración:

```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
    "AllowedOrigins": ["*"],
    "ExposeHeaders": ["ETag"]
  }
]
```

### 4. Crear Usuario IAM para S3 (Opcional pero Recomendado)

⚠️ **Nota:** En AWS Academy, el acceso a IAM puede estar limitado. Si no puedes crear usuarios IAM, usa las credenciales del Lab directamente (las copiarás en el script de deployment).

---

## 🖥️ Lanzamiento de Instancia EC2

---

## � Preparación del Código (en tu computadora local)

### 1. Actualizar Variables de Entorno Localmente

Antes de subir el código, actualiza estos archivos en tu computadora:

#### a) Archivo `llm-api/.env`

Abre el archivo y reemplaza el token de GitHub:

```properties
GITHUB_TOKEN=ghp_TU_TOKEN_REAL_DE_GITHUB_AQUI
```

#### b) Archivo `text_image_api/.env`

Crea o edita este archivo con tus credenciales de AWS:

```properties
# Service Configuration
PORT=8000
SERVICE_NAME=text-image-service

# JWT Configuration
JWT_ACCESS_SECRET=dev-super-secret-access-key-2024

# Users Service
USERS_SERVICE_URL=http://users-service:3000

# AWS S3 Configuration
AWS_REGION=us-east-1
S3_BUCKET_NAME=tu-nombre-text-image-bucket
AWS_ACCESS_KEY_ID=ASIA_TU_ACCESS_KEY_AQUI
AWS_SECRET_ACCESS_KEY=TU_SECRET_ACCESS_KEY_AQUI
AWS_SESSION_TOKEN=TU_SESSION_TOKEN_AQUI

# Pollinations API
POLLINATIONS_API_URL=https://image.pollinations.ai/prompt
```

#### c) Archivo `text_speech_api/.env`

Crea o edita este archivo:

```properties
# Service Configuration
PORT=8000
SERVICE_NAME=text-speech-service

# JWT Configuration
JWT_ACCESS_SECRET=dev-super-secret-access-key-2024

# Users Service
USERS_SERVICE_URL=http://users-service:3000

# AWS S3 Configuration
AWS_REGION=us-east-1
S3_BUCKET_NAME=tu-nombre-text-speech-bucket
AWS_ACCESS_KEY_ID=ASIA_TU_ACCESS_KEY_AQUI
AWS_SECRET_ACCESS_KEY=TU_SECRET_ACCESS_KEY_AQUI
AWS_SESSION_TOKEN=TU_SESSION_TOKEN_AQUI

# Pollinations API
POLLINATIONS_TTS_URL=https://text-to-speech.pollinations.ai/
```

#### d) Archivo `frontend/.env.local`

⚠️ **Importante:** Necesitas saber la IP pública de tu EC2. La obtendrás después de crear la instancia.

Por ahora, déjalo así (lo actualizaremos después):

```bash
NEXT_PUBLIC_API_URL=http://TU_IP_PUBLICA_EC2:8080/api
```

### 2. Crear archivo docker-compose.prod.yml

En la raíz de tu proyecto, crea un archivo llamado `docker-compose.prod.yml` con este contenido.

### 3. Comprimir el Proyecto

1. Asegúrate de que todos los archivos estén guardados
2. **Comprime** toda la carpeta del proyecto en un archivo ZIP
3. Nombre sugerido: `proyecto-cloud.zip`

---

## 📤 Subida de Código a S3

### 1. Crear Bucket para el Código

1. Ve a la consola de **S3**
2. Haz clic en **Create bucket**
3. **Nombre:** `tu-nombre-deployment-code`
4. **Región:** us-east-1
5. **Mantén** marcado "Block all public access" (el código no debe ser público)
6. Haz clic en **Create bucket**

### 2. Subir el Código Comprimido

1. Haz clic en el bucket `tu-nombre-deployment-code`
2. Haz clic en **Upload**
3. Haz clic en **Add files**
4. Selecciona tu archivo `proyecto-cloud.zip`
5. Haz clic en **Upload**
6. Espera a que se complete la subida

---

## �🖥️ Lanzamiento de Instancia EC2

### 1. Crear Security Group

1. Ve a la consola de **EC2**
2. En el menú lateral, haz clic en **Security Groups** (bajo Network & Security)
3. Haz clic en **Create security group**
4. **Security group name:** `microservices-sg`
5. **Description:** `Security group for microservices application`
6. **VPC:** Deja la default
7. **Inbound rules** - Haz clic en **Add rule** para cada una:

| Type       | Port Range | Source    | Description       |
| ---------- | ---------- | --------- | ----------------- |
| Custom TCP | 8080       | 0.0.0.0/0 | Gateway API       |
| Custom TCP | 3000       | 0.0.0.0/0 | Users Service     |
| Custom TCP | 8002       | 0.0.0.0/0 | LLM Service       |
| Custom TCP | 8000       | 0.0.0.0/0 | Image Service     |
| Custom TCP | 8001       | 0.0.0.0/0 | Speech Service    |
| Custom TCP | 8005       | 0.0.0.0/0 | Analytics Service |
| Custom TCP | 3001       | 0.0.0.0/0 | Frontend          |

8. Haz clic en **Create security group**

### 2. Preparar Script de Deployment (User Data)

Antes de lanzar la instancia, prepara el siguiente script reemplazando los valores indicados:

**⚠️ IMPORTANTE - Reemplaza estos valores:**

- `TU_GITHUB_TOKEN_AQUI` → Tu GitHub Personal Access Token
- `TU_ACCESS_KEY_ID_AQUI` → Tu AWS Access Key ID de AWS Academy
- `TU_SECRET_ACCESS_KEY_AQUI` → Tu AWS Secret Access Key de AWS Academy
- `TU_SESSION_TOKEN_AQUI` → Tu AWS Session Token de AWS Academy
- `tu-nombre-text-image-bucket` → Nombre real de tu bucket de imágenes
- `tu-nombre-text-speech-bucket` → Nombre real de tu bucket de audio
- `TU_IP_PUBLICA_EC2` → La IP pública de la instancia (la obtendrás después, puedes dejarlo así por ahora)

```bash
#!/bin/bash
# Script de deployment automático para AWS Academy

# Actualizar sistema
apt update && apt upgrade -y

# Instalar Docker
apt install -y ca-certificates curl gnupg
mkdir -m 0755 -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Instalar Git
apt install -y git

# Clonar repositorio
cd /home/ubuntu
git clone https://github.com/marcosotomac/proyecto-cloud.git
cd proyecto-cloud

# Configurar variables de entorno para LLM Service
cat > llm-api/.env << 'EOF'
NODE_ENV=development
PORT=8002
MONGO_URI=mongodb://mongo:27017/llm_chat
GITHUB_TOKEN=TU_GITHUB_TOKEN_AQUI
GITHUB_API_BASE=https://models.inference.ai.azure.com
JWT_ACCESS_SECRET=dev-super-secret-access-key-2024
USERS_SERVICE_URL=http://users-service:3000
EOF

# Configurar variables de entorno para Text-to-Image Service
cat > text_image_api/.env << 'EOF'
PORT=8000
SERVICE_NAME=text-image-service
JWT_ACCESS_SECRET=dev-super-secret-access-key-2024
USERS_SERVICE_URL=http://users-service:3000
AWS_REGION=us-east-1
S3_BUCKET_NAME=tu-nombre-text-image-bucket
AWS_ACCESS_KEY_ID=TU_ACCESS_KEY_ID_AQUI
AWS_SECRET_ACCESS_KEY=TU_SECRET_ACCESS_KEY_AQUI
AWS_SESSION_TOKEN=TU_SESSION_TOKEN_AQUI
POLLINATIONS_API_URL=https://image.pollinations.ai/prompt
EOF

# Configurar variables de entorno para Text-to-Speech Service
cat > text_speech_api/.env << 'EOF'
PORT=8000
SERVICE_NAME=text-speech-service
JWT_ACCESS_SECRET=dev-super-secret-access-key-2024
USERS_SERVICE_URL=http://users-service:3000
AWS_REGION=us-east-1
S3_BUCKET_NAME=tu-nombre-text-speech-bucket
AWS_ACCESS_KEY_ID=TU_ACCESS_KEY_ID_AQUI
AWS_SECRET_ACCESS_KEY=TU_SECRET_ACCESS_KEY_AQUI
AWS_SESSION_TOKEN=TU_SESSION_TOKEN_AQUI
POLLINATIONS_TTS_URL=https://text-to-speech.pollinations.ai/
EOF

# Configurar variables de entorno para Frontend
cat > frontend/.env.local << 'EOF'
NEXT_PUBLIC_API_URL=http://TU_IP_PUBLICA_EC2:8080/api
EOF

# Dar permisos
chown -R ubuntu:ubuntu /home/ubuntu/proyecto-cloud

# Construir y ejecutar contenedores
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

### 3. Lanzar Instancia EC2

1. Ve a **EC2** → **Instances** → **Launch instances**
2. **Name:** `microservices-app`
3. **Application and OS Images:**
   - **Ubuntu Server 24.04 LTS** (Free tier eligible)
4. **Instance type:** `t2.large` o `t3.large`
5. **Key pair:** Selecciona **Proceed without a key pair** (no necesitamos SSH)
6. **Network settings:**
   - **Auto-assign public IP:** Enable
   - **Select existing security group:** `microservices-sg`
7. **Configure storage:** 50 GB
8. **Advanced details:**

   - Desplázate hasta **User data**
   - **Pega el script que preparaste en el paso 2** (con tus valores reemplazados)

9. Haz clic en **Launch instance**

### 4. Obtener IP Pública y Actualizar Frontend

1. Ve a **EC2** → **Instances**
2. Selecciona tu instancia `microservices-app`
3. **Copia la IP pública** (aparece en la columna "Public IPv4 address")
4. **Actualiza el script de User Data:**
   - Si todavía no lanzaste la instancia, reemplaza `TU_IP_PUBLICA_EC2` en el script con tu IP real
   - Si ya lanzaste la instancia con `TU_IP_PUBLICA_EC2`, necesitarás actualizar el frontend después (ver sección Troubleshooting)

⚠️ **Nota:** Es recomendable esperar a tener la IP pública antes de lanzar la instancia, o usar la IP asignada elásticamente si está disponible en AWS Academy.
aws_session_token = TU_SESSION_TOKEN_AQUI
EOF

cat > /root/.aws/config << 'EOF'
[default]
region = us-east-1
EOF

# Descargar código desde S3

cd /home/ubuntu
aws s3 cp s3://tu-nombre-deployment-code/proyecto-cloud.zip .
unzip -q proyecto-cloud.zip
cd proyecto-cloud

# Dar permisos

chown -R ubuntu:ubuntu /home/ubuntu/proyecto-cloud

# Construir y ejecutar

docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

```

9. Haz clic en **Launch instance**
10. **Copia la IP pública** (aparecerá en la lista de instancias)

### 3. Esperar la Inicialización (15-20 minutos)

El script de User Data se ejecuta automáticamente cuando la instancia arranca por primera vez. Este proceso incluye:

1. ✅ Instalación de Docker y Docker Compose
2. ✅ Instalación de AWS CLI
3. ✅ Configuración de credenciales AWS
4. ✅ Descarga del código desde S3
5. ✅ Construcción de imágenes Docker (esto toma tiempo)
6. ✅ Inicio de todos los contenedores

**Monitorear el progreso:**

1. Ve a **EC2** → **Instances**
2. Selecciona tu instancia `microservices-app`
3. Haz clic en la pestaña **Status checks**
4. Espera a que ambos checks estén en 2/2 (verde)
5. Haz clic en **Actions** → **Monitor and troubleshoot** → **Get system log**
6. Busca líneas que indiquen que Docker Compose está construyendo o iniciando servicios

⏱️ **Tiempo estimado:** 15-20 minutos para completar todo el proceso

---

## ✅ Verificación del Deployment

### 1. Verificar que los Servicios Estén Activos

Abre tu navegador y prueba estos endpoints (reemplaza `EC2_PUBLIC_IP` con tu IP):

#### a) Frontend (Aplicación Web)
```

http://EC2_PUBLIC_IP:3001

```
Deberías ver la página principal de la aplicación.

#### b) Gateway API
```

http://EC2_PUBLIC_IP:8080/health
o
http://EC2_PUBLIC_IP:8080/docs

```
Deberías ver un mensaje de health check o la documentación de la API.

#### c) Users Service
```

http://EC2_PUBLIC_IP:3000/health

```

#### d) LLM Service
```

http://EC2_PUBLIC_IP:8002/health

```

### 2. Probar la Aplicación Completa

1. **Registro de Usuario:**
   - Abre `http://EC2_PUBLIC_IP:3001` en tu navegador
   - Ve a la página de registro
   - Crea una cuenta nueva

2. **Login:**
   - Inicia sesión con tus credenciales

3. **Probar Servicios:**
   - **Chat LLM:** Envía un mensaje al chatbot
   - **Generación de Imágenes:** Genera una imagen con un prompt
   - **Text-to-Speech:** Genera audio a partir de texto

### 3. Verificar Archivos en S3

1. Ve a la consola de **S3**
2. Abre tu bucket `tu-nombre-text-image-bucket`
3. Deberías ver las imágenes generadas
4. Abre tu bucket `tu-nombre-text-speech-bucket`
5. Deberías ver los archivos de audio generados


---

## 🐛 Troubleshooting

### Problema: Los servicios no están accesibles

**Verificaciones desde la consola web:**

1. **Verificar Security Group:**
   - Ve a **EC2** → **Security Groups**
   - Selecciona `microservices-sg`
   - Verifica que los puertos estén abiertos (8080, 3000, 8002, 8000, 8001, 8005, 3001)

2. **Verificar que la instancia esté corriendo:**
   - Ve a **EC2** → **Instances**
   - La instancia debe estar en estado "Running" (verde)

3. **Verificar IP Pública:**
   - Copia la IP pública correcta de la instancia
   - Prueba en el navegador: `http://IP_PUBLICA:3001`

### Problema: No se pueden generar imágenes o audio

**Síntoma:** Error al usar text-to-image o text-to-speech

**Solución:**

1. **Verificar Buckets S3:**
   - Ve a **S3** → Busca tus buckets
   - Verifica que existan: `tu-nombre-text-image-bucket` y `tu-nombre-text-speech-bucket`

2. **Verificar Políticas de Bucket:**
   - Abre cada bucket
   - Ve a **Permissions** → **Bucket Policy**
   - Verifica que la política de acceso público esté configurada

3. **Renovar Credenciales AWS Academy:**
   - Las credenciales expiran después de unas horas
   - Ve a AWS Academy → **AWS Details** → **Show**
   - Copia las nuevas credenciales (Access Key, Secret Key, Session Token)
   - Actualiza los archivos `.env` localmente
   - Vuelve a comprimir el proyecto
   - Sube el nuevo ZIP a S3
   - **Termina** la instancia EC2 actual
   - **Crea una nueva instancia** con el mismo proceso (User Data actualizará las credenciales)

### Problema: La instancia no se inicia correctamente

**Solución:**

1. Ve a **EC2** → **Instances**
2. Selecciona tu instancia
3. **Actions** → **Monitor and troubleshoot** → **Get system log**
4. Busca errores en el log
5. Errores comunes:
   - **"fatal: could not read Username":** Error al clonar desde GitHub (el repositorio es público, no debería pasar)
   - **"GitHub token is invalid":** Verifica que tu GitHub token en el script sea correcto
   - **"No space left on device":** Aumenta el tamaño del disco (mínimo 50 GB)
   - **"AWS credentials not found":** Verifica que las credenciales en el User Data sean correctas

### Problema: El frontend muestra error de conexión

**Síntoma:** Frontend carga pero no puede conectarse al backend

**Solución:**

1. Verifica que pusiste la IP pública correcta en el script de User Data
2. Si la IP estaba incorrecta:
   - **Termina** la instancia actual
   - **Crea una nueva instancia** con la IP correcta en el script
   - O actualiza manualmente el archivo (ver sección de actualización)

### Problema: El deployment tarda mucho tiempo

**Explicación:**

- La construcción de imágenes Docker puede tardar 15-20 minutos
- Es normal, especialmente en instancias t2.large
- Se están construyendo 7 servicios diferentes

**Monitorear:**

1. **EC2** → **Instances** → Selecciona tu instancia
2. **Actions** → **Monitor and troubleshoot** → **Get system log**
3. Busca mensajes como:
   - "Cloning into 'proyecto-cloud'"
   - "Building users-service"
   - "Creating containers"
   - "Started"
4. Espera pacientemente hasta ver todos los servicios iniciados

---

## 🔄 Actualizar la Aplicación

Para actualizar el código después de hacer cambios en GitHub:

### Método 1: Terminando y Recreando la Instancia (Recomendado)

1. **Haz push de tus cambios a GitHub** (desde tu computadora local)
2. **Termina la instancia actual:**
   - Ve a **EC2** → **Instances**
   - Selecciona tu instancia
   - **Actions** → **Instance State** → **Terminate instance**
3. **Crea una nueva instancia** siguiendo los mismos pasos de deployment
4. El script clonará la versión más reciente del código

### Método 2: Actualizando la Instancia Existente (Requiere crear nueva AMI con SSH habilitado)

⚠️ Este método requeriría acceso SSH, lo cual está fuera del alcance de esta guía 100% web.

**Alternativa recomendada:** Usar el Método 1 (terminar y recrear)

---

## 🛑 Detener la Aplicación

### Detener la Instancia (Mantiene datos)

1. Ve a **EC2** → **Instances**
2. Selecciona tu instancia `microservices-app`
3. **Actions** → **Instance State** → **Stop instance**
4. Confirma

⚠️ Los datos en los volúmenes de Docker se mantendrán cuando vuelvas a iniciar la instancia.

### Terminar la Instancia (Elimina todo)

1. Ve a **EC2** → **Instances**
2. Selecciona tu instancia
3. **Actions** → **Instance State** → **Terminate instance**
4. Confirma

⚠️ Esto eliminará la instancia y todos los datos. Los buckets S3 permanecerán intactos.

---

## 📊 Monitoreo desde la Consola

### Monitorear Uso de Recursos

1. Ve a **EC2** → **Instances**
2. Selecciona tu instancia
3. Pestaña **Monitoring:**
   - **CPU Utilization:** Uso de CPU
   - **Network In/Out:** Tráfico de red
   - **Disk Read/Write:** Actividad de disco

### Ver Logs del Sistema

1. **EC2** → **Instances** → Selecciona instancia
2. **Actions** → **Monitor and troubleshoot** → **Get system log**
3. Revisa los logs de arranque y errores

---

## 💾 Backup de Datos

### Backup de Archivos en S3

Los archivos en S3 ya están respaldados automáticamente. Para mayor seguridad:

1. Ve a **S3**
2. Selecciona tu bucket
3. **Management** → **Replication rules**
4. Configura replicación a otra región (opcional)

### Backup de Base de Datos MongoDB

MongoDB está dentro del contenedor Docker. Para hacer backup manual:

⚠️ **Nota:** Esto requeriría acceso SSH. Como alternativa:

**Opción 1:** Usar AWS Backup (si está disponible en Academy)
**Opción 2:** Exportar datos desde la aplicación antes de terminar la instancia
**Opción 3:** Crear una AMI de la instancia EC2:

1. Ve a **EC2** → **Instances**
2. Selecciona tu instancia
3. **Actions** → **Image and templates** → **Create image**
4. Dale un nombre: `microservices-backup-YYYYMMDD`
5. Haz clic en **Create image**

Esto creará una imagen completa que puedes restaurar más tarde.

---

## ⚠️ Notas Importantes sobre AWS Academy

### 1. Tiempo de Sesión Limitado

- Las sesiones duran aproximadamente **4 horas**
- El indicador AWS 🔴 se pondrá rojo cuando expire
- **Antes de que expire:**
  - Detén la instancia EC2 (no terminarla)
  - Los buckets S3 permanecerán

### 2. Credenciales Temporales

- Las credenciales cambian cada vez que inicias el lab
- **Al iniciar una nueva sesión:**
  1. Copia las nuevas credenciales (AWS Details → Show)
  2. Si tu instancia EC2 está **detenida:**
     - Actualiza el script de User Data con las nuevas credenciales
     - Termina la instancia actual
     - Crea una nueva instancia con el script actualizado
  3. Si necesitas nuevas credenciales para S3, repite el proceso de deployment

### 3. Persistencia de Recursos

**Persisten entre sesiones:**
- ✅ Buckets S3 y su contenido
- ✅ Instancias EC2 detenidas (no terminadas)
- ✅ Volúmenes EBS
- ✅ Security Groups
- ✅ Código en GitHub (siempre disponible)

**NO persisten:**
- ❌ Instancias EC2 terminadas
- ❌ Credenciales AWS (cambian cada sesión)
- ❌ Contenedores Docker corriendo (se detienen con la instancia)

### 4. Reiniciar Trabajo en Nueva Sesión

1. **Inicia el Lab** en AWS Academy
2. **Copia nuevas credenciales** (AWS Details → Show)
3. **Actualiza el script de User Data** con las nuevas credenciales
4. **Dos opciones:**

   **Opción A - Si la instancia existe y está detenida:**
   - Start la instancia
   - ⚠️ Las credenciales dentro siguen siendo las viejas
   - Deberás terminarla y crear una nueva si necesitas usar S3

   **Opción B - Crear nueva instancia (Recomendado):**
   - Termina la instancia anterior
   - Crea nueva instancia con credenciales actualizadas
   - El código se clonará automáticamente desde GitHub

---

## 📞 Soporte

Si encuentras problemas:

1. ✅ Revisa la sección de [Troubleshooting](#troubleshooting)
2. ✅ Verifica los logs del sistema (EC2 → Get system log)
3. ✅ Verifica Security Groups y permisos S3
4. ✅ Consulta la documentación de AWS Academy
5. ✅ Revisa el repositorio: https://github.com/marcosotomac/proyecto-cloud

---

## ✨ ¡Deployment Exitoso!

Si todo funcionó correctamente, deberías tener:

- ✅ Instancia EC2 corriendo con Docker
- ✅ Todos los microservicios funcionando
- ✅ MongoDB con datos persistentes
- ✅ Imágenes y audios guardándose en S3
- ✅ Frontend accesible desde el navegador
- ✅ API Gateway coordinando todos los servicios

**URLs de Acceso:**

```

Frontend: http://TU_IP_PUBLICA:3001
API Gateway: http://TU_IP_PUBLICA:8080
API Docs: http://TU_IP_PUBLICA:8080/docs

```

**Servicios Individuales:**

```

Users: http://TU_IP_PUBLICA:3000
LLM Chat: http://TU_IP_PUBLICA:8002
Text-Image: http://TU_IP_PUBLICA:8000
Text-Speech: http://TU_IP_PUBLICA:8001
Analytics: http://TU_IP_PUBLICA:8005

```

**Buckets S3:**

- Imágenes: `tu-nombre-text-image-bucket`
- Audio: `tu-nombre-text-speech-bucket`

**Repositorio GitHub:**

- Código fuente: `https://github.com/marcosotomac/proyecto-cloud`

---

## 🎯 Checklist Final

Antes de terminar, verifica:

- [ ] Todos los servicios están accesibles en el navegador
- [ ] Puedes registrarte e iniciar sesión
- [ ] El chat LLM responde a mensajes (verifica el GitHub token)
- [ ] La generación de imágenes funciona (verifica credenciales AWS S3)
- [ ] La generación de audio funciona (verifica credenciales AWS S3)
- [ ] Los archivos aparecen en S3
- [ ] Has guardado la IP pública de tu EC2
- [ ] Has guardado los nombres de tus buckets S3
- [ ] Entiendes cómo actualizar las credenciales AWS

¡Felicitaciones! 🎉 Has desplegado exitosamente la aplicación completa en AWS Academy.
```
