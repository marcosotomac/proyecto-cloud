# Users/Auth Microservice

Microservicio de autenticación y usuarios usando NestJS, PostgreSQL y JWT.

## 🚀 Características

- **Registro y login** de usuarios
- **Autenticación JWT** con refresh tokens
- **Gestión de sesiones** con revocación
- **Validación** de datos con class-validator
- **Base de datos PostgreSQL** con TypeORM
- **Seguridad** con bcryptjs y JWT

## 📡 Endpoints

### Autenticación

```bash
# Registrar usuario
POST /auth/register
{
  "email": "user@example.com",
  "password": "password123"
}

# Iniciar sesión
POST /auth/login
{
  "email": "user@example.com",
  "password": "password123"
}

# Renovar tokens
POST /auth/refresh
{
  "refreshToken": "your-refresh-token"
}

# Cerrar sesión
POST /auth/logout
{
  "refreshToken": "your-refresh-token"
}
```

### Usuarios

```bash
# Obtener perfil (requiere JWT)
GET /users/me
Authorization: Bearer your-access-token
```

## 🛠️ Desarrollo Local

```bash
# Instalar dependencias
pnpm install

# Copiar variables de entorno
cp .env.example .env

# Iniciar PostgreSQL (con Docker)
docker run -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:16

# Ejecutar en modo desarrollo
pnpm run start:dev
```

## 🐳 Docker

```bash
# Construir imagen
docker build -t users-service .

# Ejecutar contenedor
docker run -p 3000:3000 --env-file .env users-service
```

## 📊 Base de Datos

### Tabla `users`

- `id` (UUID, PK)
- `email` (unique)
- `password_hash`
- `role` (default: 'user')
- `created_at`

### Tabla `sessions`

- `id` (UUID, PK)
- `user_id` (FK → users.id)
- `refresh_token_hash`
- `user_agent`
- `ip`
- `created_at`
- `revoked_at`

## 🔐 Seguridad

- Contraseñas hasheadas con **bcryptjs**
- Tokens JWT con **RS256** (access + refresh)
- **Refresh token rotation** en cada renovación
- **Sesiones revocables** por seguridad
- **Validación** estricta de entrada
  <!--[![Backers on Open Collective](https://opencollective.com/nest/backers/badge.svg)](https://opencollective.com/nest#backer)
  [![Sponsors on Open Collective](https://opencollective.com/nest/sponsors/badge.svg)](https://opencollective.com/nest#sponsor)-->

## Description

[Nest](https://github.com/nestjs/nest) framework TypeScript starter repository.

## Project setup

```bash
$ pnpm install
```

## Compile and run the project

```bash
# development
$ pnpm run start

# watch mode
$ pnpm run start:dev

# production mode
$ pnpm run start:prod
```

## Run tests

```bash
# unit tests
$ pnpm run test

# e2e tests
$ pnpm run test:e2e

# test coverage
$ pnpm run test:cov
```

## Deployment

When you're ready to deploy your NestJS application to production, there are some key steps you can take to ensure it runs as efficiently as possible. Check out the [deployment documentation](https://docs.nestjs.com/deployment) for more information.

If you are looking for a cloud-based platform to deploy your NestJS application, check out [Mau](https://mau.nestjs.com), our official platform for deploying NestJS applications on AWS. Mau makes deployment straightforward and fast, requiring just a few simple steps:

```bash
$ pnpm install -g @nestjs/mau
$ mau deploy
```

With Mau, you can deploy your application in just a few clicks, allowing you to focus on building features rather than managing infrastructure.

## Resources

Check out a few resources that may come in handy when working with NestJS:

- Visit the [NestJS Documentation](https://docs.nestjs.com) to learn more about the framework.
- For questions and support, please visit our [Discord channel](https://discord.gg/G7Qnnhy).
- To dive deeper and get more hands-on experience, check out our official video [courses](https://courses.nestjs.com/).
- Deploy your application to AWS with the help of [NestJS Mau](https://mau.nestjs.com) in just a few clicks.
- Visualize your application graph and interact with the NestJS application in real-time using [NestJS Devtools](https://devtools.nestjs.com).
- Need help with your project (part-time to full-time)? Check out our official [enterprise support](https://enterprise.nestjs.com).
- To stay in the loop and get updates, follow us on [X](https://x.com/nestframework) and [LinkedIn](https://linkedin.com/company/nestjs).
- Looking for a job, or have a job to offer? Check out our official [Jobs board](https://jobs.nestjs.com).

## Support

Nest is an MIT-licensed open source project. It can grow thanks to the sponsors and support by the amazing backers. If you'd like to join them, please [read more here](https://docs.nestjs.com/support).

## Stay in touch

- Author - [Kamil Myśliwiec](https://twitter.com/kammysliwiec)
- Website - [https://nestjs.com](https://nestjs.com/)
- Twitter - [@nestframework](https://twitter.com/nestframework)

## License

Nest is [MIT licensed](https://github.com/nestjs/nest/blob/master/LICENSE).
