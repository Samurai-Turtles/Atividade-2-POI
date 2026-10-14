#!/usr/bin/env bash
# Experimento com a carga FORA da VM: o hey roda no host e o monitor.sh roda na VM (via SSH).
# Uso: ./run_remote.sh <cenario> [size_mb] [duracao] ["niveis de concorrencia"]
# Ex.: ./run_remote.sh 1cpu-1gb 128 60s "1 2 4 8 16"
# Variáveis: PASSES (padrão 3), VM_USER (osboxes), VM_HOST (localhost), VM_SSH_PORT (2222), APP_PORT (8000),
# RECOVERY_TIMEOUT (segundos esperando o app voltar entre níveis, padrão 300).
# Requer chave SSH sem senha para a VM (ssh-copy-id -p 2222 osboxes@localhost).
# Se o app não se recuperar entre níveis, o script para e mantém o que já foi coletado.
set -e
cd "$(dirname "$0")"
CENARIO=${1:?informe o nome do cenario}
SIZE=${2:-128}; DUR=${3:-60s}; LEVELS=${4:-"1 2 4 8 16"}
PASSES=${PASSES:-3}
VM_USER=${VM_USER:-osboxes}; VM_HOST=${VM_HOST:-localhost}
VM_SSH_PORT=${VM_SSH_PORT:-2222}; APP_PORT=${APP_PORT:-8000}
RECOVERY_TIMEOUT=${RECOVERY_TIMEOUT:-300}
URL=http://localhost:$APP_PORT
case "$CENARIO" in
  */*|.|..) echo "nome de cenario invalido: $CENARIO" >&2; exit 1;;
esac
# timeouts: com a VM em swap, ssh/scp podem ficar pendurados para sempre
SSH_OPTS="-o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=5 -o ServerAliveCountMax=6"
SSH="timeout 120 ssh -p $VM_SSH_PORT $SSH_OPTS $VM_USER@$VM_HOST"
SCP="timeout 120 scp -P $VM_SSH_PORT $SSH_OPTS"

app_ok() { curl -fs --max-time 5 "$URL/health" > /dev/null; }

# espera o app responder de novo (a VM pode estar esvaziando o swap e processando requisições abandonadas)
wait_app() {
  local waited=0
  until app_ok; do
    [ "$waited" -ge "$RECOVERY_TIMEOUT" ] && return 1
    sleep 5; waited=$((waited+5))
  done
}

$SSH true || { echo "SSH sem senha para a VM falhou (rode ssh-copy-id)" >&2; exit 1; }
app_ok || { echo "app nao responde em $URL (suba o uvicorn na VM)" >&2; exit 1; }
$SCP monitor.sh "$VM_USER@$VM_HOST:/tmp/monitor.sh"

DIR=results/$CENARIO
rm -rf "$DIR"
mkdir -p "$DIR"
OUT=$DIR/resultados.csv
echo "cenario,size_mb,concorrencia,duracao,req_por_s,media_s,p50_s,p90_s,p95_s,p99_s,respostas_200,outras_respostas,erros,cpu_media_pct,mem_usada_max_mb,swap_max_mb" > "$OUT"

for C in $LEVELS; do
  echo ">> $CENARIO: concorrência=$C size_mb=$SIZE passes=$PASSES duração=$DUR"
  $SSH "rm -f /tmp/rec.csv; nohup bash /tmp/monitor.sh /tmp/rec.csv >/dev/null 2>&1 & echo \$! > /tmp/mon.pid" || true
  F=$DIR/c$C-hey.txt
  hey -z "$DUR" -c "$C" "$URL/memory?size_mb=$SIZE&passes=$PASSES" > "$F" 2>&1 || true
  $SSH 'kill $(cat /tmp/mon.pid) 2>/dev/null || true' || true
  R=$DIR/c$C-recursos.csv
  $SCP "$VM_USER@$VM_HOST:/tmp/rec.csv" "$R" || echo "timestamp,cpu_used_pct,mem_used_mb,mem_available_mb,swap_used_mb" > "$R"

  rps=$(awk '/Requests\/sec/{print $2}' "$F")
  avg=$(awk '/Average:/{print $2}' "$F")
  pct() { awk -v p="$1" '$1==p"%" && $2=="in"{print $3}' "$F"; }
  ok=$(awk '/\[200\]/{print $2}' "$F"); ok=${ok:-0}
  total=$(awk '/^\s*\[[0-9]+\]\s/{s+=$2}END{print s+0}' "$F")
  erros=$(awk '/Error distribution/{f=1;next} f&&NF{s+=$1}END{print s+0}' "$F")
  cpu=$(awk -F, 'NR>1{s+=$2;n++}END{if(n)printf "%.1f",s/n}' "$R")
  mem=$(awk -F, 'NR>1&&$3>m{m=$3}END{print m+0}' "$R")
  swap=$(awk -F, 'NR>1&&$5>m{m=$5}END{print m+0}' "$R")
  echo "$CENARIO,$SIZE,$C,$DUR,$rps,$avg,$(pct 50),$(pct 90),$(pct 95),$(pct 99),$ok,$((total-ok)),$erros,$cpu,$mem,$swap" >> "$OUT"

  sleep 10
  if ! wait_app; then
    echo "!! app nao se recuperou em ${RECOVERY_TIMEOUT}s apos c=$C (thrashing de swap/OOM). Parando; niveis seguintes nao medidos." >&2
    echo "   Reinicie a VM/app antes de medir outro cenario." >&2
    break
  fi
done
echo "Resultados em $OUT"
