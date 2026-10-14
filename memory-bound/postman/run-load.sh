#!/usr/bin/env bash
# Uso: ./run-load.sh [iteracoes] [base_url] [size_mb]
# Roda a collection varias vezes via Newman e gera relatório HTML em postman/results/.
set -e
cd "$(dirname "$0")"
ITER=${1:-50}; URL=${2:-http://localhost:8000}; SIZE=${3:-64}
mkdir -p results
npx --yes newman run memory-bound.postman_collection.json \
  --env-var "base_url=$URL" --env-var "size_mb=$SIZE" \
  -n "$ITER" --reporters cli,json --reporter-json-export "results/newman-$(date +%s).json"
