#!/usr/bin/env bash
# Verifica una cuenta ya registrada y la convierte en administrador (no existe un endpoint para esto a propósito).
# Requisitos: cliente psql instalado y allowed_ip configurada en terraform.tfvars (con apply hecho).
# Uso: scripts/create-admin.sh correo@dominio
set -euo pipefail
cd "$(dirname "$0")/.."

EMAIL="${1:?Uso: scripts/create-admin.sh correo@dominio}"
TF="infra/terraform"
HOST=$(terraform -chdir="$TF" output -raw postgres_fqdn)
USUARIO=$(terraform -chdir="$TF" output -raw postgres_admin_login)
export PGPASSWORD
PGPASSWORD=$(terraform -chdir="$TF" output -raw postgres_admin_password)

psql "host=$HOST port=5432 dbname=auth_db user=$USUARIO sslmode=require" -v email="$EMAIL" <<'SQL'
UPDATE users
   SET is_verified = true,
       role_id = '323e4567-e89b-12d3-a456-426614174000'
 WHERE email = :'email';
SQL
