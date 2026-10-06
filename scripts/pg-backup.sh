#!/usr/bin/env bash
# Respaldo de las 4 bases de datos con pg_dump (formato custom, restaurable con pg_restore).
# Requisitos: cliente de PostgreSQL 16 instalado y allowed_ip configurada en terraform.tfvars.
# Uso: scripts/pg-backup.sh [carpeta_destino]     (por defecto: backups/AAAAMMDD-HHMM)
set -euo pipefail
cd "$(dirname "$0")/.."

TF="infra/terraform"
DESTINO="${1:-backups/$(date +%Y%m%d-%H%M)}"
mkdir -p "$DESTINO"

HOST=$(terraform -chdir="$TF" output -raw postgres_fqdn)
USUARIO=$(terraform -chdir="$TF" output -raw postgres_admin_login)
export PGPASSWORD
PGPASSWORD=$(terraform -chdir="$TF" output -raw postgres_admin_password)

for db in auth_db role_db navigation_db chat_db; do
  echo "== Respaldando $db"
  pg_dump "host=$HOST port=5432 dbname=$db user=$USUARIO sslmode=require" -Fc -f "$DESTINO/$db.dump"
done

echo "Respaldos en $DESTINO"
echo "Restaurar una base:  pg_restore --clean --if-exists -d \"host=\$HOST dbname=<base> user=\$USUARIO sslmode=require\" $DESTINO/<base>.dump"
