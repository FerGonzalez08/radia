# Despliegue de RADIA en Azure (etapa 1)

Terraform crea la infraestructura y los scripts de `scripts/` construyen y suben las imágenes.
Esta etapa deja **una región** con todo funcionando; la región pasiva con Traffic Manager (etapa 2)
se agrega después reutilizando este mismo código.

## Qué se crea

| Recurso | Detalle |
|---|---|
| Grupo de recursos | `<prefijo>-rg` |
| Container Registry | SKU Basic, guarda las 5 imágenes |
| Plan de App Service | Linux, SKU `B2` por defecto |
| 5 Web Apps de contenedor | `auth`, `role`, `navigation`, `chat` y `frontend` (nginx). HTTPS obligatorio, health check en `/health`, WebSockets activos en `chat` |
| PostgreSQL Flexible Server | Burstable `B1ms`, versión 16, 32 GB, con 4 bases: `auth_db`, `role_db`, `navigation_db`, `chat_db` |

Los secretos (llave JWT, llave interna entre servicios, contraseña de PostgreSQL) los genera Terraform
y quedan en `terraform.tfstate`, que **no debe subirse a git** (ya está en `.gitignore`).

## Requisitos (en WSL o Linux)

```bash
# Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Terraform
wget -O - https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform

# Solo si vas a usar create-admin.sh y pg-backup.sh (versión 16 o superior)
sudo apt install postgresql-client
```

También se necesitan Docker (con acceso desde WSL) y git.

## Pasos

1. **Iniciar sesión en Azure**
   ```bash
   az login --use-device-code
   az account show --query id -o tsv      # este es el subscription_id
   ```
2. **Chequeo previo.** Registra los proveedores de recursos y dice qué regiones sirven para tu suscripción:
   ```bash
   chmod +x scripts/*.sh
   scripts/azure-preflight.sh
   ```
   Elige una región donde PostgreSQL y App Service digan OK. Si PostgreSQL está restringido en la región
   que prefieres, usa otra solo para la base con `postgres_location`.
3. **Configurar variables**
   ```bash
   cd infra/terraform
   cp terraform.tfvars.example terraform.tfvars    # editar: subscription_id, location, resend_api_key
   ```
4. **Crear la infraestructura**
   ```bash
   terraform init
   terraform validate
   terraform plan
   terraform apply
   ```
   Si algún recurso falla con "server is busy" o "another operation in progress" (PostgreSQL no admite
   operaciones simultáneas), vuelve a correr `terraform apply`: lo ya creado se conserva.
5. **Construir y subir las imágenes** (desde la raíz del repositorio):
   ```bash
   scripts/build-and-push.sh --restart
   ```
   Las Web Apps se crean antes que las imágenes, por eso la primera vez hace falta `--restart`.
6. **Verificar**
   ```bash
   scripts/smoke-test.sh
   ```
7. **Crear el primer administrador.** Registra la cuenta desde el frontend y luego:
   ```bash
   # poner allowed_ip = "<tu IP pública>" en terraform.tfvars y repetir terraform apply
   scripts/create-admin.sh correo@dominio
   ```
8. **Respaldos de las bases**
   ```bash
   scripts/pg-backup.sh
   ```
   PostgreSQL Flexible Server además hace copias automáticas (retención de 7 días en esta configuración).

## Variables

| Variable | Por defecto | Para qué |
|---|---|---|
| `subscription_id` | (obligatoria) | Suscripción de Azure |
| `prefix` | `radia` | Prefijo de nombres (minúsculas y números) |
| `location` | `eastus2` | Región del App Service y el registro |
| `postgres_location` | misma que `location` | Región de PostgreSQL, si hace falta otra |
| `plan_sku` | `B2` | Tamaño del plan de App Service |
| `postgres_sku` | `B_Standard_B1ms` | Tamaño de PostgreSQL (tier Burstable) |
| `resend_api_key` | (obligatoria) | API key de Resend |
| `allowed_ip` | vacío | Tu IP, para abrir el firewall de PostgreSQL |

## Limitaciones conocidas

- **PostgreSQL sin alta disponibilidad.** El tier Burstable no la soporta; hay copias automáticas y `pg-backup.sh`.
- **El firewall de PostgreSQL permite "servicios de Azure".** Cualquier recurso de Azure puede intentar conectarse,
  pero necesita usuario y contraseña. Una red privada con VNet sería la mejora siguiente.
- **Los endpoints `/internal/*` de Auth y Navigation son públicos en internet**, protegidos solo por la llave
  interna compartida (`X-Internal-Service-Key`). Se pueden limitar por IP de salida como mejora.
- **Resend en modo sandbox** solo entrega correos a la cuenta dueña de la API key. Para otros usuarios hay que
  verificarlos a mano (`create-admin.sh` hace lo mismo para el administrador) o verificar un dominio propio.
- **Las URLs entre servicios se calculan** como `https://<nombre>.azurewebsites.net`. Si Azure asignara otro
  formato de hostname, el `apply` falla con un mensaje claro (condición `postcondition` en `main.tf`).

## Problemas frecuentes

| Síntoma | Causa y solución |
|---|---|
| `SkuNotAvailable`, `LocationIsOfferRestricted` o error de capacidad | La región no tiene cupo para tu suscripción. Cambia `location` o `postgres_location` y vuelve a aplicar |
| Una Web App responde 503 justo después del apply | Todavía no están las imágenes. Corre `scripts/build-and-push.sh --restart` |
| El navegador bloquea las peticiones (CORS) | `FRONTEND_ORIGINS` debe ser exactamente la URL del frontend, sin barra final |
| El chat no conecta | Comprueba que `chat` tenga WebSockets activos y que `VITE_CHAT_API_URL` sea `https://...` (el cliente lo convierte en `wss://`) |
| `terraform apply` falla por `postcondition` de hostname | Azure asignó un hostname distinto al calculado. Avisar antes de seguir: afecta CORS y las URLs internas |

## Eliminar todo

```bash
cd infra/terraform
terraform destroy
```

Borra todos los recursos y deja de generar costos. Haz `scripts/pg-backup.sh` antes si quieres conservar los datos.
