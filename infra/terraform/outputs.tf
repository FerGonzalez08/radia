output "resource_group" {
  value = azurerm_resource_group.rg.name
}

output "acr_name" {
  value = azurerm_container_registry.acr.name
}

output "acr_login_server" {
  value = azurerm_container_registry.acr.login_server
}

output "webapp_names" {
  value = local.names
}

output "app_urls" {
  value = { for k, v in azurerm_linux_web_app.app : k => "https://${v.default_hostname}" }
}

output "frontend_url" {
  value = "https://${azurerm_linux_web_app.app["frontend"].default_hostname}"
}

# Las URLs de los backends se fijan en el bundle del frontend en el momento del build.
output "frontend_build_args" {
  value = {
    VITE_API_URL                    = local.urls["auth"]
    VITE_ROLE_API_URL               = local.urls["role"]
    VITE_NAV_API_URL                = local.urls["navigation"]
    VITE_CHAT_API_URL               = local.urls["chat"]
    VITE_AGENTE_ORIENTACION_API_URL = local.urls["agent"]
  }
}

output "postgres_fqdn" {
  value = azurerm_postgresql_flexible_server.pg.fqdn
}

output "postgres_admin_login" {
  value = local.pg_admin
}

output "postgres_admin_password" {
  value     = random_password.postgres_admin.result
  sensitive = true
}
