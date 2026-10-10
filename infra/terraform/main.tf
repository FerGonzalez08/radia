# Infraestructura de RADIA en Azure, etapa 1 (una región).
# - Un plan de App Service Linux con 5 Web Apps de contenedor (4 backends + frontend).
# - Un PostgreSQL Flexible Server con 4 bases de datos (una por servicio).
# - Un Container Registry de donde las Web Apps descargan las imágenes.
# Los secretos (llaves JWT/internas y contraseña de la base) los genera Terraform
# y viven en el estado local, que está en .gitignore.

resource "random_string" "suffix" {
  length  = 5
  upper   = false
  special = false
}

resource "random_password" "postgres_admin" {
  length  = 28
  special = false
}

resource "random_password" "jwt_secret" {
  length  = 64
  special = false
}

resource "random_password" "internal_key" {
  length  = 48
  special = false
}

locals {
  suffix      = random_string.suffix.result
  pg_location = coalesce(var.postgres_location, var.location)
  pg_admin    = "radiaadmin"

  app_names = ["auth", "role", "navigation", "chat", "agent", "frontend"]

  # Los nombres se calculan sin referenciar los recursos para romper el ciclo:
  # los backends necesitan la URL del frontend (CORS) y el frontend necesita
  # las URLs de los backends (variables de build de Vite).
  names     = { for a in local.app_names : a => "${var.prefix}-${local.suffix}-${a}" }
  hostnames = { for a, n in local.names : a => "${n}.azurewebsites.net" }
  urls      = { for a, h in local.hostnames : a => "https://${h}" }

  databases = {
    auth       = "auth_db"
    role       = "role_db"
    navigation = "navigation_db"
    chat       = "chat_db"
    agent      = "agent_db"
  }

  db_urls = {
    for svc, db in local.databases :
    # El agente usa psycopg 3, que exige el esquema postgresql+psycopg.
    svc => "${svc == "agent" ? "postgresql+psycopg" : "postgresql"}://${local.pg_admin}:${random_password.postgres_admin.result}@${azurerm_postgresql_flexible_server.pg.fqdn}:5432/${db}?sslmode=require"
  }

  backend_common = {
    WEBSITES_PORT                       = "8000"
    WEBSITES_ENABLE_APP_SERVICE_STORAGE = "false"
    FRONTEND_ORIGINS                    = local.urls["frontend"]
    INTERNAL_SERVICE_KEY                = random_password.internal_key.result
  }

  apps = {
    auth = {
      image      = "auth-service"
      health     = "/health"
      websockets = false
      settings = merge(local.backend_common, {
        DATABASE_URL        = local.db_urls["auth"]
        JWT_SECRET_KEY      = random_password.jwt_secret.result
        COOKIE_SECURE       = "true"
        RESEND_API_KEY      = var.resend_api_key
        RESEND_SENDER_EMAIL = var.resend_sender_email
        FRONTEND_URL        = local.urls["frontend"]
      })
    }
    role = {
      image      = "role-service"
      health     = "/health"
      websockets = false
      settings = merge(local.backend_common, {
        DATABASE_URL     = local.db_urls["role"]
        AUTH_SERVICE_URL = local.urls["auth"]
      })
    }
    navigation = {
      image      = "navigation-service"
      health     = "/health"
      websockets = false
      settings = merge(local.backend_common, {
        DATABASE_URL        = local.db_urls["navigation"]
        AUTH_SERVICE_URL    = local.urls["auth"]
        RESEND_API_KEY      = var.resend_api_key
        RESEND_SENDER_EMAIL = var.resend_sender_email
        FRONTEND_URL        = local.urls["frontend"]
      })
    }
    chat = {
      image      = "chat-service"
      health     = "/health"
      websockets = true
      settings = merge(local.backend_common, {
        DATABASE_URL           = local.db_urls["chat"]
        AUTH_SERVICE_URL       = local.urls["auth"]
        NAVIGATION_SERVICE_URL = local.urls["navigation"]
      })
    }
    agent = {
      image      = "agent-service"
      health     = "/api/v1/salud"
      websockets = false
      settings = {
        WEBSITES_PORT                       = "8000"
        WEBSITES_ENABLE_APP_SERVICE_STORAGE = "false"
        DATABASE_URL                        = local.db_urls["agent"]
        ORIGENES_CORS                       = local.urls["frontend"]
        PROVEEDOR_IA                        = var.agent_provider
        MODELO_IA                           = var.agent_model
        CLAVE_API_IA                        = var.agent_api_key
      }
    }
    frontend = {
      image      = "frontend"
      health     = "/health"
      websockets = false
      settings = {
        WEBSITES_PORT                       = "80"
        WEBSITES_ENABLE_APP_SERVICE_STORAGE = "false"
      }
    }
  }
}

resource "azurerm_resource_group" "rg" {
  name     = "${var.prefix}-rg"
  location = var.location
  tags     = var.tags
}

resource "azurerm_container_registry" "acr" {
  name                = "${var.prefix}${local.suffix}acr"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "Basic"
  admin_enabled       = true
  tags                = var.tags
}

resource "azurerm_service_plan" "plan" {
  name                = "${var.prefix}-${local.suffix}-plan"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  os_type             = "Linux"
  sku_name            = var.plan_sku
  tags                = var.tags
}

resource "azurerm_postgresql_flexible_server" "pg" {
  name                          = "${var.prefix}-${local.suffix}-pg"
  resource_group_name           = azurerm_resource_group.rg.name
  location                      = local.pg_location
  version                       = "16"
  administrator_login           = local.pg_admin
  administrator_password        = random_password.postgres_admin.result
  sku_name                      = var.postgres_sku
  storage_mb                    = var.postgres_storage_mb
  backup_retention_days         = 7
  geo_redundant_backup_enabled  = false
  public_network_access_enabled = true
  tags                          = var.tags

  lifecycle {
    ignore_changes = [zone]
  }
}

resource "azurerm_postgresql_flexible_server_database" "db" {
  for_each = local.databases

  name      = each.value
  server_id = azurerm_postgresql_flexible_server.pg.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

# Permite que los servicios de Azure (las Web Apps) lleguen a la base.
resource "azurerm_postgresql_flexible_server_firewall_rule" "azure_services" {
  name             = "AllowAzureServices"
  server_id        = azurerm_postgresql_flexible_server.pg.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

# Acceso opcional desde tu máquina, para psql y pg_dump.
resource "azurerm_postgresql_flexible_server_firewall_rule" "admin_ip" {
  count = var.allowed_ip == "" ? 0 : 1

  name             = "AllowAdminIp"
  server_id        = azurerm_postgresql_flexible_server.pg.id
  start_ip_address = var.allowed_ip
  end_ip_address   = var.allowed_ip

  depends_on = [azurerm_postgresql_flexible_server_firewall_rule.azure_services]
}

resource "azurerm_linux_web_app" "app" {
  for_each = toset(local.app_names)

  name                    = local.names[each.key]
  resource_group_name     = azurerm_resource_group.rg.name
  location                = azurerm_resource_group.rg.location
  service_plan_id         = azurerm_service_plan.plan.id
  https_only              = true
  client_affinity_enabled = false
  tags                    = var.tags

  site_config {
    always_on                         = true
    health_check_path                 = local.apps[each.key].health
    health_check_eviction_time_in_min = 5
    websockets_enabled                = local.apps[each.key].websockets
    ftps_state                        = "Disabled"
    http2_enabled                     = true
    minimum_tls_version               = "1.2"

    application_stack {
      docker_image_name        = "${local.apps[each.key].image}:${var.image_tag}"
      docker_registry_url      = "https://${azurerm_container_registry.acr.login_server}"
      docker_registry_username = azurerm_container_registry.acr.admin_username
      docker_registry_password = azurerm_container_registry.acr.admin_password
    }
  }

  app_settings = merge(local.apps[each.key].settings, local.email_settings_by_app[each.key])

  depends_on = [
    azurerm_postgresql_flexible_server_database.db,
    azurerm_postgresql_flexible_server_firewall_rule.azure_services,
  ]

  lifecycle {
    postcondition {
      condition     = self.default_hostname == local.hostnames[each.key]
      error_message = "El hostname real (${self.default_hostname}) no coincide con el calculado (${local.hostnames[each.key]}). Las URLs entre servicios y el CORS quedarían mal."
    }
  }
}
