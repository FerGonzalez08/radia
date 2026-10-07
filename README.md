# RADIA

Plataforma de mentorías construida como arquitectura de microservicios, para el
Trabajo de Grado de Ingeniería de Sistemas en la Universidad Católica de
Colombia.

RADIA conecta estudiantes con mentoras según área de interés, gestiona el
agendamiento de sesiones de mentoría y habilita un chat en tiempo real mientras
la mentoría está activa.

## Arquitectura

Cinco microservicios independientes, cada uno con su propia base de datos
(Postgres), comunicándose por HTTP y WebSocket:

| Servicio | Puerto | Responsabilidad |
|---|---|---|
| **Auth Service** | 8001 | Identidad: registro, login, JWT, verificación de correo |
| **Role Service** | 8002 | Gestión de roles: promoción y reversión estudiante ↔ mentora, auditoría de cambios |
| **Navigation Service** | 8003 | Categorías, disponibilidad horaria, búsqueda de mentoras, agendamiento de mentorías |
| **Chat Service** | 8004 | Mensajería en tiempo real vía WebSocket, solo entre pares con mentoría activa |
| **Agent Service** | 8005 | Agente de orientación académica con IA (chat IA del frontend). Proviene del repo [Proyecto-de-grado](https://github.com/MiguelRamos00/Proyecto-de-grado) |

### Principios de diseño

- **Database-per-service**: cada microservicio tiene su propia base de datos;
  ninguno accede directamente a la de otro. Las referencias entre servicios
  (como `user_id`) son lógicas, sin foreign key física.
- **Validación de sesión distribuida**: ningún servicio decodifica el JWT por
  su cuenta; todos preguntan a Auth Service vía `GET /auth/validate-session`,
  para que un cambio de rol o una sesión revocada tenga efecto inmediato en
  todo el sistema.
- **Comunicación servicio a servicio**: los endpoints `/internal/*` se protegen
  con una llave compartida (`X-Internal-Service-Key`), distinta del JWT de
  usuario. Es una frontera de confianza separada para llamadas backend a
  backend.
- **Esquema gestionado con Alembic**: ningún servicio crea tablas con
  `create_all()`. Cada contenedor ejecuta `alembic upgrade head` al arrancar,
  así que una base de datos vacía se crea sola y una existente solo recibe las
  migraciones pendientes.

## Cómo levantar el proyecto localmente

Requiere Docker y Docker Compose (en Windows, dentro de WSL 2).

```bash
git clone https://github.com/FerGonzalez08/radia.git
cd radia
```

Copia el `.env.example` de cada servicio a `.env` y completa los valores. La
`INTERNAL_SERVICE_KEY` debe ser **exactamente la misma cadena** en los cuatro
servicios de RADIA (agent-service no la usa), y `JWT_SECRET_KEY` se genera con
`python3 -c "import secrets; print(secrets.token_hex(32))"`.

```bash
for s in auth-service role-service navigation-service chat-service agent-service; do
  cp services/$s/.env.example services/$s/.env
done
```

Levanta todo:

```bash
docker compose up --build
docker compose ps        # deben aparecer 10 contenedores (5 servicios + 5 bases)
```

Cada servicio expone su documentación interactiva en `/docs`:
- Auth: http://localhost:8001/docs
- Role: http://localhost:8002/docs
- Navigation: http://localhost:8003/docs
- Chat (REST): http://localhost:8004/docs
- Agente IA: http://localhost:8005/docs (salud: http://localhost:8005/api/v1/salud)

### Agente de IA (agent-service)

Por defecto arranca con `PROVEEDOR_IA=simulado`, que responde frases fijas por
palabra clave: sirve para probar la integración, no para conversar. Para
respuestas reales, en `services/agent-service/.env`:

```env
PROVEEDOR_IA=gemini
MODELO_IA=gemini-2.5-flash
CLAVE_API_IA=<clave de https://aistudio.google.com/apikey>
```

y luego `docker compose up -d --force-recreate agent-service`. El frontend lo
consume en `/app/orientacion` y en la burbuja flotante; no recibe JWT ni datos
personales (el `sesion_id` es un UUID generado en el navegador). Cada mensaje
se responde por separado: el agente no guarda historial de la conversación.

### Crear el primer administrador

No existe un endpoint para crear administradores (a propósito: nadie se
autoasigna ese rol). El primero se promueve directamente en la base de datos,
después de registrar y verificar la cuenta:

```bash
docker exec -it radia-auth-db psql -U auth_user -d auth_db -c \
  "UPDATE users SET is_verified = true, role_id = '323e4567-e89b-12d3-a456-426614174000' WHERE email = 'correo@ejemplo.com';"
```

### Correo de verificación

Resend opera en modo sandbox (sin dominio propio verificado), así que el correo
de verificación solo se entrega a la dirección dueña de la cuenta de Resend.
Para cualquier otro usuario de prueba, se marca como verificado con el mismo
`UPDATE` de arriba (`SET is_verified = true`).

## Frontend

React + TypeScript + Vite, en `frontend/`.

```bash
cd frontend
cp .env.example .env     # URLs de los 5 servicios (puertos 8001 a 8005)
npm install
npm run dev              # http://localhost:5173
```

Requiere Node 20 o superior **instalado dentro de WSL** (por ejemplo con `nvm`).
Con el `npm` de Windows, Vite falla al intentar crear su caché en
`C:\Windows`.

Abre la aplicación siempre como `http://localhost:5173`. Los servicios solo
aceptan ese origen en CORS, y `http://127.0.0.1:5173` se considera otro origen
para el navegador, así que el login falla con "No pudimos conectar con el
servidor".

## Migraciones de base de datos

Cada servicio tiene su carpeta `alembic/` con la migración inicial. Para
cambiar un modelo:

```bash
# 1. Edita el modelo en app/models/
# 2. Genera la migración dentro del contenedor del servicio
docker exec -it radia-auth-service alembic revision --autogenerate -m "describe el cambio"
# 3. Copia la migración generada a tu carpeta local
docker cp radia-auth-service:/app/alembic/versions/. services/auth-service/alembic/versions/
# 4. Aplícala (también se aplica sola al reiniciar el contenedor)
docker exec -it radia-auth-service alembic upgrade head
```

Revisa siempre el archivo generado antes de aplicarlo: si `upgrade()` solo
contiene `pass`, Alembic no detectó diferencias.

## Estructura del repositorio

```
radia/
├── docker-compose.yml
├── frontend/                 # React + TypeScript + Vite
└── services/
    ├── auth-service/
    ├── role-service/
    ├── navigation-service/
    ├── chat-service/
    └── agent-service/        # agente IA (arquitectura hexagonal propia, ver abajo)
```

Cada servicio sigue la misma estructura interna:

```
app/
├── core/       # configuración, base de datos, clientes HTTP, seguridad
├── models/     # modelos SQLAlchemy
├── schemas/    # schemas Pydantic de entrada/salida
├── routers/    # endpoints
└── main.py
alembic/        # migraciones
```

`agent-service` conserva la estructura hexagonal de su repo de origen
(`dominios/`, `aplicacion/`, `puertos/`, `adaptadores/`, `infraestructura/`).

## Stack técnico

- **Backend**: Python 3.12, FastAPI, SQLAlchemy, Alembic, Postgres 16
- **Frontend**: React, TypeScript, React Router, Vite
- **Autenticación**: JWT (HS256), bcrypt
- **Correo transaccional**: Resend
- **Contenedores**: Docker, Docker Compose
- **Despliegue objetivo**: Microsoft Azure (en preparación)

## Decisiones de diseño documentadas

Estas decisiones quedaron registradas como compromisos conscientes, no como
omisiones:

- El `refresh_token` viaja en el JSON de la respuesta de login, no en cookie
  `httpOnly`. Simplifica la integración del frontend; la migración a cookie
  queda identificada como deuda técnica.
- Resend opera en modo sandbox; en producción requiere verificar un dominio
  propio.
- La gestión de roles vive en un microservicio separado (Role Service) con su
  propia base de datos y una tabla de auditoría (`RoleChangeLog`).
- Se usa REST para toda la comunicación entre servicios. gRPC no se justifica
  con el volumen de llamadas internas del sistema.
- El correo recordatorio de mentorías quedó fuera del alcance: requiere
  infraestructura de tareas programadas que el MVP no tiene.
- Los servicios usan Postgres como almacén compartido de contadores (límite
  semanal de mentorías, bloqueo por intentos de login) en lugar de Redis. Es
  suficiente para el volumen actual y funciona con varias réplicas.

## Equipo

- Edgar Fernando González Huérfano
- Miguel Angel Rogelis Caballero

Universidad Católica de Colombia, Facultad de Ingeniería
