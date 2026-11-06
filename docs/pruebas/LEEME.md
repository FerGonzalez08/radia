# Pruebas unitarias y flujo de CI para RADIA

Este paquete **no modifica el repositorio**. Contiene archivos nuevos que se copian tal cual al repositorio
(`FerGonzalez08/radia`) en la misma ruta relativa, con la estructura que ya existe:

```
.github/workflows/ci.yml                       ← flujo de GitHub Actions
services/auth-service/pytest.ini
services/auth-service/requirements-test.txt
services/auth-service/tests/...                ← 64 pruebas
services/role-service/...                      ← 40 pruebas
services/navigation-service/...                ← 98 pruebas
services/chat-service/...                      ← 38 pruebas
```

No se toca ningún archivo existente. `agent-service` queda fuera: lo desarrolló otro grupo y ya tiene su propia carpeta `tests/`.

## Cómo incorporarlas

1. Copiar el contenido de este paquete a la raíz del repositorio (las carpetas `services/*` se fusionan con las existentes).
2. Crear una rama, hacer commit y abrir la solicitud de integración. El flujo se ejecuta solo.
3. Cuando el flujo salga en verde, activar la protección de `main` (Settings → Branches) y marcar como requeridos los
   checks `Pruebas (auth-service)`, `Pruebas (role-service)`, `Pruebas (navigation-service)`,
   `Pruebas (chat-service)`, `Frontend (lint y build)` e `Imagen Docker (...)`.

## Cómo ejecutarlas en local

Requieren una base PostgreSQL vacía **cuyo nombre contenga `test`** (las pruebas truncan las tablas y se niegan a correr
contra cualquier otra base, para que nunca toquen la de desarrollo ni la de Azure).

```bash
docker run -d --name radia-pg-test -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=radia_test -p 5432:5432 postgres:16
export TEST_DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/radia_test

cd services/auth-service          # o role-service, navigation-service, chat-service
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-test.txt
pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

## Qué verifican

| Servicio | Áreas cubiertas |
|---|---|
| auth | Hash de contraseñas (incluido el pre-hash SHA-256), JWT (firma, expiración, algoritmo `none`), registro (edad mínima 18, duplicados), verificación de correo, login, bloqueo tras 5 intentos fallidos, refresh con rotación y detección de reuso, logout, validate-session, recuperación de contraseña, endpoints internos con llave de servicio, selección de proveedor de correo |
| role | Acceso exclusivo del administrador (401/403 por rol), promoción y reversión de mentora, protección del rol administrador, bitácora de auditoría, cliente hacia Auth, sembrado de roles |
| navigation | Autorización por rol en cada endpoint, catálogo de categorías, categorías de la mentora, búsqueda, bloques de disponibilidad (traslapes, contiguos), solicitud/aceptación/rechazo/cancelación de mentorías, límite semanal, aceptación automática, endpoint interno para chat |
| chat | Administrador de conexiones, historial paginado, lectura, estado y presencia, WebSocket (token inválido 4401, sin mentoría 4403, entrega, acuse, mensajes vacíos, last_seen, varias pestañas), cliente que falla cerrado si Navigation no responde |

## Alcance y límites (para citar con precisión)

- **Son pruebas de servicio con base de datos real y servicios vecinos simulados**: Auth y Navigation se reemplazan por dobles
  en memoria (`httpx.MockTransport`) que respetan el contrato HTTP. No sustituyen las pruebas de integración entre
  servicios desplegados ni las del frontend.
- **No cubren el frontend**: solo se ejecutan su análisis estático (`oxlint`) y la compilación (`tsc` + `vite build`).
- **La cobertura mide líneas ejecutadas, no calidad.** Para comprobar que las pruebas detectan defectos reales se inyectaron
  errores deliberados en una copia del código (ver informe de resultados que acompaña este paquete).
- Se escribieron **después** de la ronda de pruebas funcionales, no durante los sprints.
