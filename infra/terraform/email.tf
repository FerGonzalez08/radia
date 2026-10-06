# Correo transaccional con Azure Communication Services (dominio administrado por Azure).
# El dominio administrado no necesita DNS ni comprar nada, pero Azure limita su envío
# a 5 correos por minuto y 10 por hora por suscripción.
# Para volver a Resend: email_provider = "resend" en terraform.tfvars.

variable "email_provider" {
  type        = string
  default     = "acs"
  description = "Proveedor de correo: acs (Azure Communication Services) o resend."

  validation {
    condition     = contains(["acs", "resend"], var.email_provider)
    error_message = "email_provider debe ser acs o resend."
  }
}

resource "azurerm_communication_service" "acs" {
  name                = "${var.prefix}-${local.suffix}-acs"
  resource_group_name = azurerm_resource_group.rg.name
  data_location       = "United States"
  tags                = var.tags
}

resource "azurerm_email_communication_service" "email" {
  name                = "${var.prefix}-${local.suffix}-email"
  resource_group_name = azurerm_resource_group.rg.name
  data_location       = "United States"
  tags                = var.tags
}

# Con domain_management = "AzureManaged" el nombre debe ser exactamente AzureManagedDomain.
resource "azurerm_email_communication_service_domain" "managed" {
  name              = "AzureManagedDomain"
  email_service_id  = azurerm_email_communication_service.email.id
  domain_management = "AzureManaged"
  tags              = var.tags
}

resource "azurerm_communication_service_email_domain_association" "assoc" {
  communication_service_id = azurerm_communication_service.acs.id
  email_service_domain_id  = azurerm_email_communication_service_domain.managed.id
}

locals {
  email_settings = var.email_provider == "acs" ? tomap({
    EMAIL_PROVIDER        = "acs"
    ACS_CONNECTION_STRING = azurerm_communication_service.acs.primary_connection_string
    ACS_SENDER_ADDRESS    = "DoNotReply@${azurerm_email_communication_service_domain.managed.mail_from_sender_domain}"
    }) : tomap({
    EMAIL_PROVIDER = "resend"
  })

  # Solo Auth y Navigation envían correo.
  email_settings_by_app = {
    auth       = local.email_settings
    navigation = local.email_settings
    role       = tomap({})
    chat       = tomap({})
    frontend   = tomap({})
  }
}

output "acs_sender_address" {
  value = "DoNotReply@${azurerm_email_communication_service_domain.managed.mail_from_sender_domain}"
}

output "acs_from_sender_domain" {
  value = azurerm_email_communication_service_domain.managed.from_sender_domain
}
