#!/bin/bash
# lanzar_ronda3.sh: ronda 3 del RL verbal, exploratoria y de mecanismo (17 oct 2026; no es una prueba de H2).
# Prerregistro: docs/formulacion/formulacion_rl_verbal.tex, párrafo «Ronda 3», y docs/formulacion/RELANZAMIENTO.md.
# C y E sobre los 16 peldaños de prueba, dos episodios por peldaño, con Claude Sonnet 5.5 y después Claude Opus 5.5,
# el cuaderno congelado 835d3070e3b0c3b1 (el de la ronda 2) y el juez teorema-2026-09-30. Misma maquinaria que
# lanzar_ronda.sh (preflight, nohup y caffeinate, marcadores por fase, reanudación por peldaño, vigilante de red y
# topes); al terminar no escribe informes ni métricas: la auditoría (rejuzgar y cruzado) va antes de cualquier análisis.
#
#   unirl/tools/lanzar_ronda3.sh              lanza (o reanuda) la ronda con nohup y caffeinate; imprime cómo seguirla
#   unirl/tools/lanzar_ronda3.sh --dry-run    ensayo en seco en primer plano: sin llamadas al modelo, dos peldaños,
#                                             corridas, cuaderno y libro en logs/ronda_dryrun_r3_<id>/ (no toca runs/)
#   unirl/tools/lanzar_ronda3.sh --nueva      empieza una ronda nueva aunque haya una sin terminar
#   unirl/tools/lanzar_ronda3.sh --detener    pide a la ronda en marcha que se detenga al terminar los episodios en curso
#
# Todos los `rm` usan ${VAR:?}: si una variable estuviera vacía, el guion se detiene en vez de borrar otra cosa.
set -u
RAIZ="$(cd "$(dirname "$0")/../.." && pwd)"
cd "${RAIZ:?}" || exit 1
PY="$RAIZ/.venv/bin/python"
RONDA_PY="$PY $RAIZ/unirl/tools/ronda.py"

# ---- parámetros de la ronda 3 (prerregistrados) -------------------------------------------------------------------
MODELO_SONNET=claude-sonnet-5-5
MODELO_OPUS=claude-opus-5-5
# esfuerzo: high, fijo en unirl.experimentos.proveedor (evaluar no tiene opción para cambiarlo); temperatura: la de la
# API por omisión (no se envía). Los dos se registran en cada llamada (campo `uso` y libro de gasto).
EPISODIOS=2                               # por peldaño de prueba y configuración
PARALELO=2                                # episodios simultáneos por fase (dos fases a la vez: cuatro llamadas)
HASH_CUADERNO=835d3070e3b0c3b1            # cuaderno congelado al final de la ronda 2 (80 lemas)
JUEZ=teorema-2026-09-30
TOPE_TOTAL_USD=75                         # tope duro de la ronda (créditos de Anthropic, que vencen el 19 oct 2026 UTC)
# C (fase evaluacion) y E (fase evaluacion_E) se reparten el tope por igual: si se agota, quedan parejos
TOPES_FASE_JSON='{"linea_base": 0, "preflight": 0.05, "cuaderno": 0, "evaluacion": 37.5, "evaluacion_E": 37.5, "pareada_luna": 0, "pareada_sol": 0}'
MAX_RELANZAMIENTOS=6
INTERVALO_VIGILANTE=30
IDS_DRY="rf_1_punto,secante_1_inyectiva"  # dos peldaños de prueba para el ensayo en seco
export RONDA_RED_URL="https://api.anthropic.com/v1/models"   # el vigilante comprueba la API del proponente

# ---- argumentos --------------------------------------------------------------------------------------------------
DRY=0; INTERNO=0; NUEVA=0; DETENER=0; ID=""
for a in "$@"; do
  case "$a" in
    --dry-run) DRY=1;; --interno) INTERNO=1;; --nueva) NUEVA=1;; --detener) DETENER=1;;
    --id=*) ID="${a#--id=}";;
    *) echo "argumento desconocido: $a"; exit 2;;
  esac
done

ACTUAL="$RAIZ/logs/ronda3_actual"
if [ "$DETENER" = 1 ]; then
  [ -f "$ACTUAL" ] || { echo "no hay ronda 3 en marcha (logs/ronda3_actual no existe)"; exit 1; }
  touch "$RAIZ/logs/ronda_$(cat "$ACTUAL")/detener"; echo "orden de detención escrita; la ronda 3 parará al terminar los episodios en curso"; exit 0
fi

# ---- identidad de la ronda ---------------------------------------------------------------------------------------
if [ "$DRY" = 1 ]; then
  ID="${ID:-dryrun_r3_$(date '+%Y%m%d-%H%M%S')}"
  RDIR="$RAIZ/logs/ronda_$ID"
  export RONDA_RUNS="$RDIR/runs" RONDA_RESULTADOS="$RDIR/resultados" RONDA_CUADERNO="$RDIR/cuaderno" RONDA_IDS="$IDS_DRY"
  export UNIRL_LIBRO="$RDIR/gasto_ronda.json"
  DRYFLAG="--dry-run"
else
  if [ -z "$ID" ]; then
    if [ "$NUEVA" = 0 ] && [ -f "$ACTUAL" ] && [ ! -e "$RAIZ/logs/ronda_$(cat "$ACTUAL")/terminada" ]; then ID=$(cat "$ACTUAL"); else ID="r3_$(date '+%Y%m%d-%H%M')"; fi
  fi
  RDIR="$RAIZ/logs/ronda_$ID"
  export UNIRL_LIBRO="$RAIZ/logs/gasto_ronda_$ID.json"
  DRYFLAG=""
fi
: "${ID:?}"; : "${RDIR:?}"
export UNIRL_TOPE_USD="$TOPE_TOTAL_USD" UNIRL_TOPES_FASE_USD="$TOPES_FASE_JSON"
LOG="$RAIZ/logs/ronda_$ID.log"; PIDF="$RAIZ/logs/ronda_$ID.pid"
[ "$DRY" = 1 ] && mkdir -p "$RDIR"   # en la ronda real la carpeta se crea después del preflight (que exige el árbol limpio)

log() { printf '%s [ronda %s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$ID" "$*"; }

comprobar_insumos() {  # el cuaderno congelado intacto y la versión del juez que dice el prerregistro
  local v
  "$PY" -c "from unirl.experimentos import cargar_congelado; cargar_congelado('$HASH_CUADERNO')" 2>/dev/null \
    || { log "el cuaderno congelado $HASH_CUADERNO falta o cambió en disco"; return 1; }
  v=$("$PY" -c "from unirl.gd_isabelle import TheoremVerifier as T; print(T.VERSION_JUEZ)" 2>/dev/null)
  [ "$v" = "$JUEZ" ] || { log "el juez es ${v:-?}, el prerregistro dice $JUEZ"; return 1; }
  return 0
}

# ---- lanzador (primer plano): preflight y nohup ------------------------------------------------------------------
if [ "$INTERNO" = 0 ]; then
  REANUDA=""; [ -f "$RDIR/meta.json" ] && REANUDA="--reanudacion"
  export MODELO_PREFLIGHT="$MODELO_SONNET,$MODELO_OPUS"
  if [ "$DRY" = 1 ]; then
    log "ENSAYO EN SECO: sin llamadas al modelo; peldaños $IDS_DRY; todo en $RDIR"
    mkdir -p "$RONDA_RUNS" "$RONDA_RESULTADOS"
    [ -d "$RONDA_CUADERNO" ] || cp -R "$RAIZ/runs/unirl/cuaderno" "$RONDA_CUADERNO"
    for f in martillo_linea_base.json "martillo_linea_base_$("$PY" -c "from unirl.experimentos import cargar_congelado; print(cargar_congelado('$HASH_CUADERNO').hash_lemas())" 2>/dev/null).json"; do
      [ -f "$RONDA_RESULTADOS/$f" ] || cp "$RAIZ/resultados/$f" "$RONDA_RESULTADOS/" 2>/dev/null || log "no encontré resultados/$f"
    done
    comprobar_insumos || exit 1
    "$RAIZ/unirl/tools/preflight.sh" --dry-run $REANUDA "--cuaderno=$HASH_CUADERNO" || { log "preflight falló; no se lanza"; exit 1; }
    # sin `exec`: en una tubería no sustituye al shell y el guion seguiría hacia el lanzamiento real
    caffeinate -i bash "$0" --dry-run --interno "--id=$ID" 2>&1 | tee -a "$LOG"
    exit "${PIPESTATUS[0]}"
  fi
  comprobar_insumos || exit 1
  "$RAIZ/unirl/tools/preflight.sh" $REANUDA "--cuaderno=$HASH_CUADERNO" || { log "preflight falló; no se lanza"; exit 1; }
  if [ -f "$PIDF" ] && kill -0 "$(cat "$PIDF")" 2>/dev/null; then echo "la ronda $ID ya está corriendo (pid $(cat "$PIDF"))"; exit 1; fi
  mkdir -p "$RDIR"
  echo "$ID" > "$ACTUAL"
  nohup caffeinate -ims bash "$0" --interno "--id=$ID" >> "$LOG" 2>&1 &
  echo $! > "$PIDF"
  cat <<FIN

Ronda 3 $ID lanzada (pid $(cat "$PIDF")), con nohup y caffeinate: sobrevive a cerrar la terminal.
  progreso:        tail -f $LOG
  ¿sigue viva?     kill -0 \$(cat $PIDF) && echo viva || echo terminada
  gasto:           UNIRL_LIBRO=$UNIRL_LIBRO $RONDA_PY gasto
  detener:         $0 --detener
  reanudar:        $0                   (salta lo hecho; relanza los peldaños que falten)
Mantén el cargador conectado y la tapa abierta. Al terminar: logs/ronda_$ID/terminada; luego, la auditoría.
FIN
  exit 0
fi

# ---- proceso interno ---------------------------------------------------------------------------------------------
mkdir -p "$RDIR"
[ "$DRY" = 1 ] || echo $$ > "$PIDF"
if [ ! -f "$RDIR/meta.json" ]; then
  INICIO=$(date '+%Y-%m-%dT%H:%M:%S')
  HUELLA=$("$PY" -c "from unirl.cli import code_fingerprint; print(code_fingerprint()['unirl_sha256'])")
  "$PY" - "$RDIR/meta.json" "$ID" "$INICIO" "$HUELLA" "$HASH_CUADERNO" "$TOPE_TOTAL_USD" "$TOPES_FASE_JSON" "$DRY" \
    "$MODELO_SONNET,$MODELO_OPUS" "$EPISODIOS" "$PARALELO" "$JUEZ" <<'PYEOF'
import json, subprocess, sys
p, i, ini, hu, cu, tope, topes, dry, modelos, ep, par, juez = sys.argv[1:13]
commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
rama = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True).stdout.strip()
json.dump({"ronda": i, "tipo": "ronda 3, exploratoria y de mecanismo", "inicio": ini, "unirl_sha256": hu,
           "cuaderno_congelado": cu, "juez": juez, "modelos": modelos.split(","), "configs": ["C", "E"],
           "episodios_por_peldano": int(ep), "paralelo": int(par), "effort": "high", "temperatura": None,
           "tope_total_usd": float(tope), "topes_fase_usd": json.loads(topes), "rama": rama, "commit": commit,
           "dry_run": dry == "1"}, open(p, "w"), indent=1)
PYEOF
  log "ronda 3 nueva: inicio $INICIO, unirl $HUELLA, cuaderno $HASH_CUADERNO, juez $JUEZ, commit $(git rev-parse --short HEAD)"
else
  INICIO=$("$PY" -c "import json; print(json.load(open('$RDIR/meta.json'))['inicio'])")
  HUELLA0=$("$PY" -c "import json; print(json.load(open('$RDIR/meta.json'))['unirl_sha256'])")
  HUELLA=$("$PY" -c "from unirl.cli import code_fingerprint; print(code_fingerprint()['unirl_sha256'])")
  if [ "$HUELLA" != "$HUELLA0" ] && [ "${RONDA_FORZAR:-0}" != 1 ]; then
    log "el código de unirl cambió desde el inicio de la ronda ($HUELLA0 → $HUELLA); no se reanuda (RONDA_FORZAR=1 para forzar)"; exit 1
  fi
  log "reanudación de la ronda 3 iniciada el $INICIO (unirl $HUELLA)"
fi
rm -f "${RDIR:?}/detener" "${RDIR:?}/red_caida" "${RDIR:?}/fin"   # fin solo marca que el proceso anterior cerró

escribir_parada() {  # nombre motivo
  printf '%s  fase %s: %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" "$2" >> "$RDIR/detenida.txt"
  touch "$RDIR/detener"
  log "DETENIDA en $1: $2"
}

esperar_red() {  # nombre
  local n=0
  while [ "$($RONDA_PY red)" != "ok" ]; do
    [ -e "$RDIR/detener" ] && return 1
    n=$((n+1)); [ $((n % 5)) = 1 ] && log "[$1] sin conexión con la API de Anthropic; esperando ($n)"
    sleep 60
  done
  return 0
}

es_fatal() {  # motivo → 0 si hay que detener la ronda
  case "$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')" in
    *tope*|*gastoexcedido*|*insufficient*|*quota*|*api\ key*|*api_key*|*api-key*|*authentication*|*401*|*403*|*billing*|*credit*|*"error del código"*|*traceback*) return 0;;
  esac
  return 1
}

matar_pid() {  # archivo .pid
  [ -f "$1" ] && kill "$(cat "$1")" 2>/dev/null
}

fase_evaluar() {  # nombre fase modelo configs episodios paralelo cuaderno
  local nombre=$1 fase=$2 modelo=$3 configs=$4 episodios=$5 paralelo=$6 cuaderno=$7 marca="$RDIR/fase_$1.done" n=0 pend t0 motivo rc
  [ -e "$marca" ] && { log "[$nombre] ya hecha"; return 0; }
  while :; do
    [ -e "$RDIR/detener" ] && { log "[$nombre] no se relanza: hay orden de detención"; return 2; }
    pend=$($RONDA_PY pendientes --fase "$fase" --modelo "$modelo" --configs "$configs" --episodios "$episodios" --desde "$INICIO") || { escribir_parada "$nombre" "ronda.py pendientes falló"; return 2; }
    if [ -z "$pend" ]; then touch "$marca"; log "[$nombre] completa"; return 0; fi
    n=$((n+1)); [ $n -gt $MAX_RELANZAMIENTOS ] && { escribir_parada "$nombre" "$MAX_RELANZAMIENTOS lanzamientos sin completar; pendientes: $pend"; return 2; }
    esperar_red "$nombre" || return 2
    log "[$nombre] lanzamiento $n: $modelo, configs $configs, $episodios episodio(s), pendientes $pend"
    t0=$(date +%s)
    $RONDA_PY exec $DRYFLAG -- evaluar --modelo "$modelo" --configs "$configs" --episodios "$episodios" --paralelo "$paralelo" --fase "$fase" --cuaderno "$cuaderno" --ids "$pend" >> "$RDIR/$nombre.out" 2>&1 &
    echo $! > "$RDIR/$nombre.pid"; wait $!; rc=$?; rm -f "${RDIR:?}/${nombre:?}.pid"
    motivo=$($RONDA_PY ultimo-aborto --fase "$fase" --desde "$INICIO" --despues "$t0")
    log "[$nombre] terminó el lanzamiento $n (rc=$rc)${motivo:+; abortada: $motivo}"
    if [ -n "$motivo" ] && es_fatal "$motivo"; then escribir_parada "$nombre" "$motivo"; return 2; fi
    [ -e "$RDIR/red_caida" ] && log "[$nombre] la red se cayó durante la corrida; se recalculan los pendientes"
  done
}

vigilante() {
  local caidas=0 t=0 total f
  while :; do
    sleep "$INTERVALO_VIGILANTE"; t=$((t+INTERVALO_VIGILANTE))
    if [ -e "$RDIR/detener" ]; then
      for f in "$RDIR"/*.pid; do matar_pid "$f"; done
      log "[vigilante] orden de detención: procesos de las fases terminados"; return 0
    fi
    [ -e "$RDIR/fin" ] && return 0
    total=$($RONDA_PY gasto 2>/dev/null | awk '{print $1}' | cut -d= -f2)
    if [ -n "$total" ] && awk -v t="$total" -v m="$TOPE_TOTAL_USD" 'BEGIN{exit !(t>=m)}'; then
      escribir_parada vigilante "gasto total \$$total alcanzó el tope de \$$TOPE_TOTAL_USD"
    fi
    if [ "$($RONDA_PY red)" = "ok" ]; then
      [ -e "$RDIR/red_caida" ] && { rm -f "${RDIR:?}/red_caida"; log "[vigilante] la red volvió"; }; caidas=0
    else
      caidas=$((caidas+1))
      if [ $caidas -ge 3 ] && [ ! -e "$RDIR/red_caida" ]; then
        touch "$RDIR/red_caida"; log "[vigilante] sin red ≥ 90 s: se detienen las fases con API; se relanzarán cuando vuelva"
        for f in "$RDIR"/0[1-4]_*.pid; do matar_pid "$f"; done
      fi
    fi
    [ $((t % 600)) = 0 ] && log "[vigilante] $($RONDA_PY gasto 2>/dev/null)"
  done
}

cerrar() {  # estado motivo
  touch "$RDIR/fin"
  printf '%s\n' "$1${2:+: $2}" > "$RDIR/estado.txt"
  log "gasto: $($RONDA_PY gasto 2>/dev/null)"
  [ "$1" = terminada ] && touch "$RDIR/terminada"
  [ "$DRY" = 0 ] && [ "$1" = terminada ] && rm -f "${ACTUAL:?}"
  rm -f "${PIDF:?}"
}
trap 'log "señal recibida: se detiene la ronda"; touch "$RDIR/detener"; sleep 2; for f in "$RDIR"/*.pid; do matar_pid "$f"; done; cerrar incompleta "detenida por señal (Ctrl-C, kill o apagado) $(date)"; exit 130' INT TERM

vigilante & VIG=$!
CUADERNO_NADA=ninguno

# Sonnet 5.5 primero (C y E a la vez), después Opus 5.5: si el tope se agota, el modelo barato queda completo
fase_evaluar 01_sonnet_C evaluacion "$MODELO_SONNET" C "$EPISODIOS" "$PARALELO" "$CUADERNO_NADA" & P1=$!
fase_evaluar 02_sonnet_E evaluacion_E "$MODELO_SONNET" E "$EPISODIOS" "$PARALELO" "$HASH_CUADERNO" & P2=$!
wait $P1; wait $P2
if [ -e "$RDIR/detener" ]; then kill $VIG 2>/dev/null; cerrar incompleta "$(cat "$RDIR/detenida.txt" 2>/dev/null)"; exit 1; fi
fase_evaluar 03_opus_C evaluacion "$MODELO_OPUS" C "$EPISODIOS" "$PARALELO" "$CUADERNO_NADA" & P3=$!
fase_evaluar 04_opus_E evaluacion_E "$MODELO_OPUS" E "$EPISODIOS" "$PARALELO" "$HASH_CUADERNO" & P4=$!
wait $P3; wait $P4
kill $VIG 2>/dev/null
if [ -e "$RDIR/detener" ]; then cerrar incompleta "$(cat "$RDIR/detenida.txt" 2>/dev/null)"; exit 1; fi
cerrar terminada ""
log "RONDA 3 TERMINADA (falta la auditoría: rejuzgar y cruzado antes de cualquier análisis)"
