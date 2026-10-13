#!/usr/bin/env bash
# Amostra CPU e memória a cada segundo e grava em CSV. Rode na máquina do servidor (VM).
# Uso: ./monitor.sh saida.csv   (Ctrl+C ou kill para parar)
OUT=${1:?uso: monitor.sh saida.csv}
echo "timestamp,cpu_used_pct,mem_used_mb,mem_available_mb,swap_used_mb" > "$OUT"
read -r _ u n s i w q sq st _ < /proc/stat; prev_total=$((u+n+s+i+w+q+sq+st)); prev_idle=$((i+w))
while sleep 1; do
  read -r _ u n s i w q sq st _ < /proc/stat
  total=$((u+n+s+i+w+q+sq+st)); idle=$((i+w))
  cpu=$(( 100 * ( (total-prev_total) - (idle-prev_idle) ) / (total-prev_total) ))
  prev_total=$total; prev_idle=$idle
  mem=$(awk '/MemTotal/{t=$2}/MemAvailable/{a=$2}/SwapTotal/{st=$2}/SwapFree/{sf=$2}END{printf "%d,%d,%d",(t-a)/1024,a/1024,(st-sf)/1024}' /proc/meminfo)
  echo "$(date +%s),$cpu,$mem" >> "$OUT"
done
