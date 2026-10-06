#!/usr/bin/env bash
# Chequeos previos al primer "terraform apply". Requiere haber hecho: az login --use-device-code
# Uso: scripts/azure-preflight.sh [region1 region2 ...]   (por defecto: eastus2 centralus southcentralus)
set -euo pipefail

REGIONES=("$@")
[ ${#REGIONES[@]} -eq 0 ] && REGIONES=(eastus2 centralus southcentralus)

echo "== Suscripción activa"
az account show --query "{nombre:name, id:id, estado:state}" -o table

echo
echo "== Registrando proveedores de recursos (puede tardar unos minutos)"
for ns in Microsoft.Web Microsoft.DBforPostgreSQL Microsoft.ContainerRegistry Microsoft.Network; do
  az provider register --namespace "$ns" --wait
  echo "  $ns: $(az provider show --namespace "$ns" --query registrationState -o tsv)"
done

echo
echo "== PostgreSQL Flexible Server (Burstable B1ms) por región"
for r in "${REGIONES[@]}"; do
  salida=$(az postgres flexible-server list-skus --location "$r" -o json 2>&1 || true)
  if [[ "${salida,,}" == *restricted* ]]; then
    echo "  $r: RESTRINGIDA para tu suscripción -> no la uses para PostgreSQL"
  elif [[ "$salida" == *Standard_B1ms* ]]; then
    echo "  $r: OK, B1ms disponible"
  else
    echo "  $r: revisar la salida de az:"; echo "$salida" | head -3 | sed 's/^/     /'
  fi
done

echo
echo "== App Service Linux B2 por región"
disponibles=$(az appservice list-locations --sku B2 --linux-workers-enabled --query "[].name" -o tsv 2>/dev/null | tr -d ' ' | tr 'A-Z' 'a-z' || true)
for r in "${REGIONES[@]}"; do
  if echo "$disponibles" | grep -qx "$r"; then echo "  $r: OK"; else echo "  $r: no aparece como disponible para B2 Linux"; fi
done

echo
echo "Elige una región donde ambas dicen OK. Si PostgreSQL solo está libre en otra, usa postgres_location en terraform.tfvars."
