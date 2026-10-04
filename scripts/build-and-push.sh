#!/usr/bin/env bash
# Construye las 5 imágenes y las sube al Container Registry que creó Terraform.
# Uso: scripts/build-and-push.sh [--restart]
#   --restart  reinicia las Web Apps al terminar (necesario la primera vez, porque se crean antes que las imágenes)
set -euo pipefail
cd "$(dirname "$0")/.."

TF="infra/terraform"
tf_out() { terraform -chdir="$TF" output -raw "$1"; }
tf_json() { terraform -chdir="$TF" output -json "$1"; }

ACR_NAME=$(tf_out acr_name)
LOGIN=$(tf_out acr_login_server)
SHA=$(git rev-parse --short HEAD)

echo "== Iniciando sesión en $LOGIN"
az acr login --name "$ACR_NAME"

for svc in auth role navigation chat; do
  echo "== $svc-service"
  docker build -t "$LOGIN/$svc-service:latest" -t "$LOGIN/$svc-service:$SHA" "services/$svc-service"
  docker push "$LOGIN/$svc-service:latest"
  docker push "$LOGIN/$svc-service:$SHA"
done

echo "== frontend (las URLs de los backends se fijan en el build)"
arg() { tf_json frontend_build_args | python3 -c "import sys, json; print(json.load(sys.stdin)['$1'])"; }
docker build -t "$LOGIN/frontend:latest" -t "$LOGIN/frontend:$SHA" \
  --build-arg "VITE_API_URL=$(arg VITE_API_URL)" \
  --build-arg "VITE_ROLE_API_URL=$(arg VITE_ROLE_API_URL)" \
  --build-arg "VITE_NAV_API_URL=$(arg VITE_NAV_API_URL)" \
  --build-arg "VITE_CHAT_API_URL=$(arg VITE_CHAT_API_URL)" \
  frontend
docker push "$LOGIN/frontend:latest"
docker push "$LOGIN/frontend:$SHA"

if [ "${1:-}" = "--restart" ]; then
  RG=$(tf_out resource_group)
  for nombre in $(tf_json webapp_names | python3 -c "import sys, json; print(' '.join(json.load(sys.stdin).values()))"); do
    echo "== Reiniciando $nombre"
    az webapp restart --resource-group "$RG" --name "$nombre"
  done
fi

echo "Listo. Verifica con: scripts/smoke-test.sh"
