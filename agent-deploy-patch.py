"""Parche: despliega agent-service (agente de IA) en Azure como sexto Web App, en modo simulado.

Ejecútalo desde la raíz del repositorio, ya con la rama del agente mezclada en develop:
    python3 agent-deploy-patch.py
Es seguro repetirlo: cada paso se salta si ya está aplicado, y aborta sin escribir
si un archivo no tiene el aspecto esperado.
"""
import pathlib

ROOT = pathlib.Path(".")

AGENT_TF = '''# Agente de orientación académica (IA), sexto Web App.
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
'''

EDITS = [
    (
        "infra/terraform/main.tf",
        '  app_names = ["auth", "role", "navigation", "chat", "frontend"]\n',
        '  app_names = ["auth", "role", "navigation", "chat", "agent", "frontend"]\n',
        '"chat", "agent", "frontend"',
    ),
    (
        "infra/terraform/main.tf",
        '    chat       = "chat_db"\n  }\n',
        '    chat       = "chat_db"\n    agent      = "agent_db"\n  }\n',
        'agent      = "agent_db"',
    ),
    (
        "infra/terraform/main.tf",
        '    svc => "postgresql://${local.pg_admin}:',
        '    # El agente usa psycopg 3, que exige el esquema postgresql+psycopg.\n'
        '    svc => "${svc == "agent" ? "postgresql+psycopg" : "postgresql"}://${local.pg_admin}:',
        'postgresql+psycopg" : "postgresql"',
    ),
    (
        "infra/terraform/main.tf",
        '    frontend = {\n      image      = "frontend"\n',
        '    agent = {\n'
        '      image      = "agent-service"\n'
        '      health     = "/api/v1/salud"\n'
        '      websockets = false\n'
        '      settings = {\n'
        '        WEBSITES_PORT                       = "8000"\n'
        '        WEBSITES_ENABLE_APP_SERVICE_STORAGE = "false"\n'
        '        DATABASE_URL                        = local.db_urls["agent"]\n'
        '        ORIGENES_CORS                       = local.urls["frontend"]\n'
        '        PROVEEDOR_IA                        = var.agent_provider\n'
        '        MODELO_IA                           = var.agent_model\n'
        '        CLAVE_API_IA                        = var.agent_api_key\n'
        '      }\n'
        '    }\n'
        '    frontend = {\n      image      = "frontend"\n',
        'image      = "agent-service"',
    ),
    (
        "infra/terraform/email.tf",
        '    chat       = tomap({})\n',
        '    chat       = tomap({})\n    agent      = tomap({})\n',
        'agent      = tomap({})',
    ),
    (
        "infra/terraform/outputs.tf",
        '    VITE_CHAT_API_URL = local.urls["chat"]\n',
        '    VITE_CHAT_API_URL = local.urls["chat"]\n    VITE_AGENTE_ORIENTACION_API_URL = local.urls["agent"]\n',
        "VITE_AGENTE_ORIENTACION_API_URL",
    ),
    (
        "scripts/build-and-push.sh",
        "for svc in auth role navigation chat; do",
        "for svc in auth role navigation chat agent; do",
        "chat agent; do",
    ),
    (
        "scripts/build-and-push.sh",
        '  --build-arg "VITE_CHAT_API_URL=$(arg VITE_CHAT_API_URL)" \\\n',
        '  --build-arg "VITE_CHAT_API_URL=$(arg VITE_CHAT_API_URL)" \\\n'
        '  --build-arg "VITE_AGENTE_ORIENTACION_API_URL=$(arg VITE_AGENTE_ORIENTACION_API_URL)" \\\n',
        "VITE_AGENTE_ORIENTACION_API_URL=",
    ),
    (
        "scripts/smoke-test.sh",
        'front=$(echo "$URLS"',
        'agent=$(echo "$URLS" | python3 -c "import sys, json; print(json.load(sys.stdin)[\'agent\'])")\n'
        'verificar "agent /api/v1/salud" "$agent/api/v1/salud"\n'
        'verificar "agent /docs" "$agent/docs"\n\n'
        'front=$(echo "$URLS"',
        'agent /api/v1/salud',
    ),
]


def main():
    agent_tf = ROOT / "infra/terraform/agent.tf"
    if agent_tf.exists() and agent_tf.read_text(encoding="utf-8") != AGENT_TF:
        raise SystemExit(f"ERROR: {agent_tf} existe con otro contenido (¿de otro parche?). Bórralo y repite.")

    pendientes = []
    for rel, viejo, nuevo, marcador in EDITS:
        p = ROOT / rel
        if not p.exists():
            raise SystemExit(f"ERROR: no encuentro {rel}. Ejecuta el script desde la raíz del repositorio.")
        texto = p.read_text(encoding="utf-8")
        if marcador in texto:
            print(f"  = ya aplicado: {rel}  [{marcador[:40]}]")
            continue
        if texto.count(viejo) != 1:
            raise SystemExit(
                f"ERROR: {rel}: esperaba 1 coincidencia de {viejo.strip()[:50]!r} y hay {texto.count(viejo)}."
            )
        pendientes.append((p, viejo, nuevo, rel, marcador))

    if not agent_tf.exists():
        agent_tf.write_text(AGENT_TF, encoding="utf-8")
        print("  + creado: infra/terraform/agent.tf")
    for p, viejo, nuevo, rel, marcador in pendientes:
        p.write_text(p.read_text(encoding="utf-8").replace(viejo, nuevo), encoding="utf-8")
        print(f"  + editado: {rel}  [{marcador[:40]}]")

    print("\nListo. Siguiente: cd infra/terraform && terraform fmt && terraform validate && terraform plan")


main()
