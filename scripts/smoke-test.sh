#!/usr/bin/env bash
# Comprueba que cada servicio desplegado responde. Falla (código 1) si alguno no responde 200.
# Uso: scripts/smoke-test.sh
set -uo pipefail
cd "$(dirname "$0")/.."

URLS=$(terraform -chdir=infra/terraform output -json app_urls)
fallos=0

verificar() {
  local etiqueta="$1" url="$2" esperado="${3:-200}"
  local codigo
  codigo=$(curl -s -o /dev/null -w "%{http_code}" --max-time 40 "$url" || true)
  if [ "$codigo" = "$esperado" ]; then
    echo "PASS  $etiqueta ($codigo)  $url"
  else
    echo "FAIL  $etiqueta (esperado $esperado, recibió ${codigo:-sin respuesta})  $url"
    fallos=$((fallos + 1))
  fi
}

for svc in auth role navigation chat; do
  base=$(echo "$URLS" | python3 -c "import sys, json; print(json.load(sys.stdin)['$svc'])")
  verificar "$svc /health" "$base/health"
  verificar "$svc /docs" "$base/docs"
done

agent=$(echo "$URLS" | python3 -c "import sys, json; print(json.load(sys.stdin)['agent'])")
verificar "agent /api/v1/salud" "$agent/api/v1/salud"
verificar "agent /docs" "$agent/docs"

front=$(echo "$URLS" | python3 -c "import sys, json; print(json.load(sys.stdin)['frontend'])")
verificar "frontend /" "$front/"
verificar "frontend /app/chat (fallback de SPA)" "$front/app/chat"

echo
if [ "$fallos" -eq 0 ]; then echo "Todo en orden."; else echo "$fallos comprobación(es) fallaron."; exit 1; fi
