# Agente de orientación académica (IA), sexto Web App.
# Arranca en modo "simulado" (frases fijas). Para activar un proveedor real, en terraform.tfvars:
#   agent_provider = "gemini"            # o openai / openrouter
#   agent_model    = "gemini-2.5-flash"
#   agent_api_key  = "..."
# y luego: terraform apply   (no hace falta reconstruir imágenes)

variable "agent_provider" {
  type        = string
  default     = "simulado"
  description = "Proveedor de IA del agente: simulado, gemini, openai u openrouter."

  validation {
    condition     = contains(["simulado", "gemini", "openai", "openrouter"], var.agent_provider)
    error_message = "agent_provider debe ser simulado, gemini, openai u openrouter."
  }
}

variable "agent_model" {
  type        = string
  default     = "gemini-2.5-flash"
  description = "Modelo del proveedor (se ignora con simulado)."
}

variable "agent_api_key" {
  type        = string
  default     = ""
  sensitive   = true
  description = "Clave del proveedor de IA (vacía con simulado)."
}
