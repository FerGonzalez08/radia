variable "subscription_id" {
  type        = string
  description = "ID de la suscripción de Azure. Se obtiene con: az account show --query id -o tsv"
}

variable "prefix" {
  type        = string
  default     = "radia"
  description = "Prefijo de los nombres de recursos. Solo minúsculas y números (el Container Registry no admite guiones)."

  validation {
    condition     = can(regex("^[a-z][a-z0-9]{1,11}$", var.prefix))
    error_message = "El prefijo debe tener entre 2 y 12 caracteres: minúsculas y números, empezando por una letra."
  }
}

variable "location" {
  type        = string
  default     = "eastus2"
  description = "Región de Azure para el App Service y el registro. Confirma cupos con scripts/azure-preflight.sh antes de aplicar."
}

variable "postgres_location" {
  type        = string
  default     = null
  description = "Región de PostgreSQL. Si es null usa la misma de location. Útil cuando una región está restringida para PostgreSQL."
}

variable "plan_sku" {
  type        = string
  default     = "B2"
  description = "SKU del plan de App Service (Linux). B2 = 2 vCPU y 3,5 GB; B1 = 1 vCPU y 1,75 GB."
}

variable "postgres_sku" {
  type        = string
  default     = "B_Standard_B1ms"
  description = "SKU de PostgreSQL Flexible Server. B_Standard_B1ms es el tier Burstable (sin alta disponibilidad)."
}

variable "postgres_storage_mb" {
  type        = number
  default     = 32768
  description = "Almacenamiento de PostgreSQL en MB. 32768 (32 GB) es el mínimo del servicio flexible."
}

variable "image_tag" {
  type        = string
  default     = "latest"
  description = "Etiqueta de las imágenes que usan las Web Apps."
}

variable "resend_api_key" {
  type        = string
  sensitive   = true
  description = "API key de Resend para el correo transaccional (Auth y Navigation)."
}

variable "resend_sender_email" {
  type        = string
  default     = "onboarding@resend.dev"
  description = "Remitente de los correos. En el sandbox de Resend solo entrega a la cuenta dueña de la API key."
}

variable "allowed_ip" {
  type        = string
  default     = ""
  description = "Tu IP pública, para abrir el firewall de PostgreSQL y poder usar psql o pg_dump. Vacío = sin acceso externo a la base."

  validation {
    condition     = var.allowed_ip == "" || can(cidrhost("${var.allowed_ip}/32", 0))
    error_message = "allowed_ip debe ser una IPv4 válida (por ejemplo 203.0.113.10) o estar vacío."
  }
}

variable "tags" {
  type = map(string)
  default = {
    proyecto = "RADIA"
    entorno  = "demo"
  }
  description = "Etiquetas que se aplican a todos los recursos."
}
