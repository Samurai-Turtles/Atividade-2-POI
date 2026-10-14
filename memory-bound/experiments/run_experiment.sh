#!/usr/bin/env bash
# Varre níveis de concorrência com o hey e grava um CSV com as métricas de desempenho.
# Uso: ./run_experiment.sh <cenario> [base_url] [size_mb] [duracao] [niveis_de_concorrencia]
# Ex.: ./run_experiment.sh vm-2cpu-2gb http://192.168.0.10:8000 64 30s "1 5 10 20 40"
# PASSES=N define as passadas por requisição (padrão 1).
# Se MONITOR=1, também amostra CPU/memória local (use quando rodar dentro da VM).
set -e
cd "$(dirname "$0")"
CENARIO=${1:?informe o nome do cenario}
URL=${2:-http://localhost:8000}; SIZE=${3:-64}; DUR=${4:-30s}; LEVELS=${5:-"1 5 10 20 40"}
case "$CENARIO" in
  */*|.|..) echo "nome de cenario invalido: $CENARIO" >&2; exit 1;;
esac
DIR=results/$CENARIO
rm -rf "$DIR"   # recomeça o cenário do zero
mkdir -p "$DIR"
OUT=$DIR/resultados.csv
echo "cenario,size_mb,concorrencia,duracao,req_por_s,media_s,p50_s,p90_s,p95_s,p99_s,respostas_200,outras_respostas,erros,cpu_media_pct,mem_usada_max_mb" > "$OUT"

for C in $LEVELS; do
  echo ">> $CENARIO: concorrência=$C size_mb=$SIZE duração=$DUR"
  if [ "${MONITOR:-0}" = 1 ]; then
    ./monitor.sh "$DIR/c$C-recursos.csv" & MON=$!
  fi
  hey -z "$DUR" -c "$C" "$URL/memory?size_mb=$SIZE&passes=${PASSES:-1}" > "$DIR/c$C-hey.txt" 2>&1 || true
  [ -n "$MON" ] && { kill $MON 2>/dev/null; wait $MON 2>/dev/null || true; MON=; }

  F=$DIR/c$C-hey.txt
  rps=$(awk '/Requests\/sec/{print $2}' "$F")
  avg=$(awk '/Average:/{print $2}' "$F")
  pct() { awk -v p="$1" '$1==p"%" && $2=="in"{print $3}' "$F"; }
  ok=$(awk '/\[200\]/{print $2}' "$F"); ok=${ok:-0}
  total=$(awk '/^\s*\[[0-9]+\]\s/{s+=$2}END{print s+0}' "$F")
  erros=$(awk '/Error distribution/{f=1;next} f&&NF{s+=$1}END{print s+0}' "$F")
  cpu=""; mem=""
  R=$DIR/c$C-recursos.csv
  if [ -f "$R" ]; then
    cpu=$(awk -F, 'NR>1{s+=$2;n++}END{if(n)printf "%.1f",s/n}' "$R")
    mem=$(awk -F, 'NR>1&&$3>m{m=$3}END{print m}' "$R")
  fi
  echo "$CENARIO,$SIZE,$C,$DUR,$rps,$avg,$(pct 50),$(pct 90),$(pct 95),$(pct 99),$ok,$((total-ok)),$erros,$cpu,$mem" >> "$OUT"
done
echo "Resultados em $OUT"
