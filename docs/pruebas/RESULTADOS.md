# Resultados de la ejecución (5 de noviembre de 2026)

Ejecutadas sobre una copia del repositorio en el commit `a63c8c5` (rama `main`), con PostgreSQL 16 local y Python 3.13.
**No** es una ejecución de GitHub Actions: esa se obtiene al abrir la primera solicitud de integración con estos archivos.

| Servicio | Pruebas | Resultado | Líneas ejecutadas |
|---|---|---|---|
| auth-service | 64 | todas pasan | 431 / 431 (100 %) |
| role-service | 40 | todas pasan | 199 / 199 (100 %) |
| navigation-service | 98 | todas pasan | 546 / 546 (100 %) |
| chat-service | 38 | todas pasan | 249 / 249 (100 %) |
| **Total** | **240** | **240 pasan** | **1.425 / 1.425** |

Estabilidad: la suite de chat (la única con WebSockets y concurrencia) se repitió 5 veces sin fallos.

## Comprobación de que las pruebas detectan defectos

Se inyectaron 15 defectos deliberados, uno por vez, en una copia del código. Las pruebas detectaron los 15
(en uno, el WebSocket se queda esperando y la prueba expira, por eso el flujo tiene `timeout-minutes`).

| Defecto inyectado | Resultado |
|---|---|
| Bloqueo de login a los 6 intentos en vez de 5 | detectado |
| Edad mínima de registro 16 en vez de 18 | detectado |
| Reuso de refresh token no revoca la familia | detectado |
| `require_admin` invertido (auth) | detectado |
| Llave interna entre servicios invertida | detectado |
| JWT acepta el algoritmo `none` | detectado |
| Role Service: «administrador» comparado contra el rol de mentora | detectado |
| Role Service: permite reasignar el rol de un administrador | detectado |
| Navigation: límite semanal fuera por uno | detectado |
| Navigation: bloques contiguos cuentan como traslape | detectado |
| Navigation: `require_mentor` compara contra el rol de administrador | detectado |
| Navigation: mentoría pendiente habilita el chat | detectado |
| Chat: si Navigation falla, el chat se abre (falla abierto) | detectado |
| Chat: sin mentoría activa no se cierra el WebSocket | detectado (expira) |
| Chat: «marcar como leído» marca los mensajes propios | detectado |

## Frontend (mismas órdenes que ejecuta el flujo)

- `npm ci`: correcto. `npm run lint` (oxlint): termina sin errores, con 13 advertencias de estilo (`set-state-in-effect`, `only-export-components`).
- `npm run build` (`tsc -b && vite build`): correcto.
