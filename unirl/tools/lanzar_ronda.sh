#!/bin/bash
# lanzar_ronda.sh: la primera ronda del RL verbal (docs/formulacion/RELANZAMIENTO.md, pasos 1-5, luego E y E3),
# sobre la rama `reorganizar`, con el .venv de la raíz. Independiente de Claude: solo llama a unirl e Isabelle.
#
#   unirl/tools/lanzar_ronda.sh              lanza (o reanuda) la ronda con nohup y caffeinate; imprime cómo seguirla
#   unirl/tools/lanzar_ronda.sh --dry-run    ensayo en seco en primer plano: sin llamadas al modelo, dos peldaños,
#                                            corridas, cuaderno y libro en logs/ronda_dryrun_<id>/ (no toca runs/)
#   unirl/tools/lanzar_ronda.sh --nueva      empieza una ronda nueva aunque haya una sin terminar
#   unirl/tools/lanzar_ronda.sh --detener    pide a la ronda en marcha que se detenga al terminar los episodios en curso
#
# Reanudable: cada fase deja logs/ronda_<id>/fase_*.done; al relanzar se saltan las hechas y, dentro de una fase, se
# relanzan solo los peldaños sin episodios válidos (ronda.py pendientes). Topes duros por fase y total en dólares
# (UNIRL_TOPES_FASE_USD, UNIRL_TOPE_USD): unirl aborta la llamada que los pasaría; el guion se detiene ahí y lo escribe.
# Libro nuevo por ronda: logs/gasto_ronda_<id>.json; el histórico logs/gasto.json no se toca.
# Todos los `rm` usan ${VAR:?}: si una variable estuviera vacía, el guion se detiene en vez de borrar otra cosa.
set -u
RAIZ="$(cd "$(dirname "$0")/../.." && pwd)"
cd "${RAIZ:?}" || exit 1
PY="$RAIZ/.venv/bin/python"
RONDA_PY="$PY $RAIZ/unirl/tools/ronda.py"

# ---- parámetros de la ronda (Carlos, 26 sep 2026) -----------------------------------------------------------------
TOPE_TOTAL_USD=15   # Carlos, 26 sep 2026: subido de 12 a 15
# topes duros por fase (fases del libro). Los de Carlos: martillo (linea_base) $0, pareadas Luna $2, pareadas Sol $6, E $2.
# Cuaderno y evaluación B0/B/C no los fijó: con el margen del total, $1,50 y $3,00 (estimaciones: $0,65 y $1,45).
# 27 sep, 07:50: pareadas Sol de 6 a 10, porque C3 de Sol costó $4,00 (16 episodios) y E3 costará otro tanto.
TOPES_FASE_JSON='{"linea_base": 0, "preflight": 0.05, "cuaderno": 1.5, "evaluacion": 3, "evaluacion_E": 2, "pareada_luna": 2, "pareada_sol": 10}'
MODELO_LUNA=gpt-6-luna
MODELO_SOL=gpt-6-sol
MAX_RELANZAMIENTOS=6
INTERVALO_VIGILANTE=30
IDS_DRY="orden_1_lineal,secante_1_inyectiva"   # un peldaño de train y uno de test para el ensayo en seco

# ---- argumentos --------------------------------------------------------------------------------------------------
DRY=0; INTERNO=0; NUEVA=0; DETENER=0; ID=""
for a in "$@"; do
  case "$a" in
    --dry-run) DRY=1;; --interno) INTERNO=1;; --nueva) NUEVA=1;; --detener) DETENER=1;;
    --id=*) ID="${a#--id=}";;
    *) echo "argumento desconocido: $a"; exit 2;;
  esac
done

if [ "$DETENER" = 1 ]; then
  act="$RAIZ/logs/ronda_actual"
  [ -f "$act" ] || { echo "no hay ronda en marcha (logs/ronda_actual no existe)"; exit 1; }
  touch "$RAIZ/logs/ronda_$(cat "$act")/detener"; echo "orden de detención escrita; la ronda parará al terminar los episodios en curso"; exit 0
fi

# ---- identidad de la ronda ---------------------------------------------------------------------------------------
if [ "$DRY" = 1 ]; then
  ID="${ID:-dryrun_$(date '+%Y%m%d-%H%M%S')}"
  RDIR="$RAIZ/logs/ronda_$ID"
  export RONDA_RUNS="$RDIR/runs" RONDA_RESULTADOS="$RDIR/resultados" RONDA_CUADERNO="$RDIR/cuaderno" RONDA_IDS="$IDS_DRY"
  export UNIRL_LIBRO="$RDIR/gasto_ronda.json"
  DRYFLAG="--dry-run"
else
  ACTUAL="$RAIZ/logs/ronda_actual"
  if [ -z "$ID" ]; then
    if [ "$NUEVA" = 0 ] && [ -f "$ACTUAL" ] && [ ! -e "$RAIZ/logs/ronda_$(cat "$ACTUAL")/terminada" ]; then ID=$(cat "$ACTUAL"); else ID=$(date '+%Y%m%d-%H%M'); fi
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

# ---- lanzador (primer plano): preflight y nohup ------------------------------------------------------------------
if [ "$INTERNO" = 0 ]; then
  REANUDA=""; [ -f "$RDIR/meta.json" ] && REANUDA="--reanudacion"
  if [ "$DRY" = 1 ]; then
    log "ENSAYO EN SECO: sin llamadas al modelo; peldaños $IDS_DRY; todo en $RDIR"
    mkdir -p "$RONDA_RUNS" "$RONDA_RESULTADOS"
    [ -d "$RONDA_CUADERNO" ] || cp -R "$RAIZ/runs/unirl/cuaderno" "$RONDA_CUADERNO"
    [ -f "$RONDA_RESULTADOS/martillo_linea_base.json" ] || cp "$RAIZ/resultados/martillo_linea_base.json" "$RONDA_RESULTADOS/"
    "$RAIZ/unirl/tools/preflight.sh" --dry-run $REANUDA || { log "preflight falló; no se lanza"; exit 1; }
    # sin `exec`: en una tubería no sustituye al shell y el guion seguiría hacia el lanzamiento real
    caffeinate -i bash "$0" --dry-run --interno "--id=$ID" 2>&1 | tee -a "$LOG"
    exit "${PIPESTATUS[0]}"
  fi
  "$RAIZ/unirl/tools/preflight.sh" $REANUDA || { log "preflight falló; no se lanza"; exit 1; }
  if [ -f "$PIDF" ] && kill -0 "$(cat "$PIDF")" 2>/dev/null; then echo "la ronda $ID ya está corriendo (pid $(cat "$PIDF"))"; exit 1; fi
  mkdir -p "$RDIR"
  echo "$ID" > "$RAIZ/logs/ronda_actual"
  nohup caffeinate -i bash "$0" --interno "--id=$ID" >> "$LOG" 2>&1 &
  echo $! > "$PIDF"
  cat <<FIN

Ronda $ID lanzada (pid $(cat "$PIDF")), con nohup y caffeinate: sobrevive a cerrar la terminal.
  progreso:        tail -f $LOG
  ¿sigue viva?     kill -0 \$(cat $PIDF) && echo viva || echo terminada
  gasto:           $RONDA_PY gasto      (libro de la ronda: $UNIRL_LIBRO)
  detener:         $0 --detener
  reanudar:        $0                   (salta lo hecho; relanza los peldaños que falten)
Al terminar: resultados/RONDA_TERMINADA.md (o RONDA_INCOMPLETA.md con la fase y el motivo).
FIN
  exit 0
fi

# ---- proceso interno ---------------------------------------------------------------------------------------------
mkdir -p "$RDIR"
[ "$DRY" = 1 ] || echo $$ > "$PIDF"
if [ ! -f "$RDIR/meta.json" ]; then
  INICIO=$(date '+%Y-%m-%dT%H:%M:%S')
  HUELLA=$("$PY" -c "from unirl.cli import code_fingerprint; print(code_fingerprint()['unirl_sha256'])")
  CUAD0=$("$PY" -c "from unirl.cuaderno import Cuaderno; print(Cuaderno().hash())")
  "$PY" - "$RDIR/meta.json" "$ID" "$INICIO" "$HUELLA" "$CUAD0" "$TOPE_TOTAL_USD" "$TOPES_FASE_JSON" "$DRY" <<'PYEOF'
import json, subprocess, sys
p, i, ini, hu, cu, tope, topes, dry = sys.argv[1:9]
commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
rama = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True).stdout.strip()
json.dump({"ronda": i, "inicio": ini, "unirl_sha256": hu, "cuaderno_inicial": cu, "tope_total_usd": float(tope),
           "topes_fase_usd": json.loads(topes), "rama": rama, "commit": commit, "dry_run": dry == "1"}, open(p, "w"), indent=1)
PYEOF
  log "ronda nueva: inicio $INICIO, unirl $HUELLA, cuaderno inicial $CUAD0, commit $(git rev-parse --short HEAD)"
else
  INICIO=$("$PY" -c "import json; print(json.load(open('$RDIR/meta.json'))['inicio'])")
  HUELLA0=$("$PY" -c "import json; print(json.load(open('$RDIR/meta.json'))['unirl_sha256'])")
  HUELLA=$("$PY" -c "from unirl.cli import code_fingerprint; print(code_fingerprint()['unirl_sha256'])")
  if [ "$HUELLA" != "$HUELLA0" ] && [ "${RONDA_FORZAR:-0}" != 1 ]; then
    log "el código de unirl cambió desde el inicio de la ronda ($HUELLA0 → $HUELLA); no se reanuda (RONDA_FORZAR=1 para forzar)"; exit 1
  fi
  log "reanudación de la ronda iniciada el $INICIO (unirl $HUELLA)"
fi
rm -f "${RDIR:?}/detener" "${RDIR:?}/red_caida" "${RDIR:?}/fin"   # fin solo marca que el proceso anterior cerró; terminada es la marca definitiva

escribir_parada() {  # nombre motivo
  printf '%s  fase %s: %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" "$2" >> "$RDIR/detenida.txt"
  touch "$RDIR/detener"
  log "DETENIDA en $1: $2"
}

esperar_red() {  # nombre
  local n=0
  while [ "$($RONDA_PY red)" != "ok" ]; do
    [ -e "$RDIR/detener" ] && return 1
    n=$((n+1)); [ $((n % 5)) = 1 ] && log "[$1] sin conexión con api.openai.com; esperando ($n)"
    sleep 60
  done
  return 0
}

es_fatal() {  # motivo → 0 si hay que detener la ronda
  case "$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')" in
    *tope*|*gastoexcedido*|*insufficient*|*quota*|*api\ key*|*api_key*|*401*|*403*|*billing*|*credit*|*"error del código"*|*traceback*) return 0;;
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
    log "[$nombre] lanzamiento $n: configs $configs, $episodios episodio(s), pendientes $pend"
    t0=$(date +%s)
    $RONDA_PY exec $DRYFLAG -- evaluar --modelo "$modelo" --configs "$configs" --episodios "$episodios" --paralelo "$paralelo" --fase "$fase" --cuaderno "$cuaderno" --ids "$pend" >> "$RDIR/$nombre.out" 2>&1 &
    echo $! > "$RDIR/$nombre.pid"; wait $!; rc=$?; rm -f "${RDIR:?}/${nombre:?}.pid"
    motivo=$($RONDA_PY ultimo-aborto --fase "$fase" --desde "$INICIO" --despues "$t0")
    log "[$nombre] terminó el lanzamiento $n (rc=$rc)${motivo:+; abortada: $motivo}"
    if [ -n "$motivo" ] && es_fatal "$motivo"; then escribir_parada "$nombre" "$motivo"; return 2; fi
    [ -e "$RDIR/red_caida" ] && log "[$nombre] la red se cayó durante la corrida; se recalculan los pendientes"
  done
}

fase_cuaderno() {
  local nombre=01_cuaderno marca="$RDIR/fase_01_cuaderno.done" n=0 carpeta t0 motivo rc
  [ -e "$marca" ] && { log "[$nombre] ya hecha"; return 0; }
  while :; do
    [ -e "$RDIR/detener" ] && return 2
    carpeta=$($RONDA_PY carpeta-cuaderno --desde "$INICIO" --modelo "$MODELO_LUNA")
    if [ -n "$carpeta" ] && [ -f "$carpeta/FIN.json" ]; then touch "$marca"; log "[$nombre] completa: $(basename "$carpeta")"; return 0; fi
    n=$((n+1)); [ $n -gt $MAX_RELANZAMIENTOS ] && { escribir_parada "$nombre" "$MAX_RELANZAMIENTOS lanzamientos sin congelar el cuaderno"; return 2; }
    esperar_red "$nombre" || return 2
    log "[$nombre] lanzamiento $n${carpeta:+ (reanuda $(basename "$carpeta"))}"
    t0=$(date +%s)
    if [ -n "$carpeta" ]; then $RONDA_PY exec $DRYFLAG -- cuaderno --modelo "$MODELO_LUNA" --reanudar "$carpeta" >> "$RDIR/$nombre.out" 2>&1 &
    else $RONDA_PY exec $DRYFLAG -- cuaderno --modelo "$MODELO_LUNA" >> "$RDIR/$nombre.out" 2>&1 & fi
    echo $! > "$RDIR/$nombre.pid"; wait $!; rc=$?; rm -f "${RDIR:?}/${nombre:?}.pid"
    motivo=$($RONDA_PY ultimo-aborto --fase cuaderno --desde "$INICIO" --despues "$t0")
    log "[$nombre] terminó el lanzamiento $n (rc=$rc)${motivo:+; abortada: $motivo}"
    if [ -n "$motivo" ] && es_fatal "$motivo"; then escribir_parada "$nombre" "$motivo"; return 2; fi
  done
}

fase_linea_base() {  # H
  local nombre=05_linea_base marca="$RDIR/fase_05_linea_base.done" hl
  [ -e "$marca" ] && { log "[$nombre] ya hecha"; return 0; }
  hl=$($RONDA_PY hash-lemas --desde "$INICIO" --modelo "$MODELO_LUNA")
  if [ -z "$hl" ]; then
    # sin lemas, la línea base con cuaderno coincide con la de sin cuaderno (resultados/martillo_linea_base.json, del
    # 24 sep, versionada); rehacerla la sobrescribiría con solo los peldaños de test. Se omite y se anota.
    log "[$nombre] el cuaderno congelado no tiene lemas: vale la línea base sin cuaderno (martillo_linea_base.json); no se rehace"
    touch "$marca"; return 0
  fi
  log "[$nombre] martillo solo con el cuaderno congelado $1 (en serie, sin API)"
  if $RONDA_PY exec $DRYFLAG -- linea-base --cuaderno "$1" --config E >> "$RDIR/$nombre.out" 2>&1; then
    touch "$marca"; log "[$nombre] completa: $(tail -1 "$RDIR/$nombre.out")"; return 0
  fi
  escribir_parada "$nombre" "linea-base falló (ver $RDIR/$nombre.out)"; return 2
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
        for f in "$RDIR"/0[1-4]_*.pid "$RDIR"/0[6-8]_*.pid; do matar_pid "$f"; done
      fi
    fi
    [ $((t % 600)) = 0 ] && log "[vigilante] $($RONDA_PY gasto 2>/dev/null)"
  done
}

cerrar() {  # estado motivo
  touch "$RDIR/fin"
  if [ "$DRY" = 0 ]; then
    log "consolidar.py"; "$PY" "$RAIZ/resultados/consolidar.py" >> "$LOG" 2>&1 || log "consolidar.py falló (ver el log)"
  fi
  out=$($RONDA_PY informe --ronda "$ID" --desde "$INICIO" --estado "$1" --motivo "$2" 2>>"$LOG") && log "informe: $out"
  [ "$1" = terminada ] && touch "$RDIR/terminada"
  [ "$DRY" = 0 ] && [ "$1" = terminada ] && rm -f "${RAIZ:?}/logs/ronda_actual"
  rm -f "${PIDF:?}"
}
trap 'log "señal recibida: se detiene la ronda"; touch "$RDIR/detener"; sleep 2; for f in "$RDIR"/*.pid; do matar_pid "$f"; done; cerrar incompleta "detenida por señal (Ctrl-C o kill) $(date)"; exit 130' INT TERM

vigilante & VIG=$!
CUADERNO_NADA=ninguno

# pasos 1-4 en paralelo (RELANZAMIENTO.md); el martillo va en serie entre procesos por su candado
fase_cuaderno & P1=$!
fase_evaluar 02_eval_B0BC evaluacion "$MODELO_LUNA" B0,B,C 2 3 "$CUADERNO_NADA" & P2=$!
fase_evaluar 03_pareada_luna_C3 pareada_luna "$MODELO_LUNA" C3 1 2 "$CUADERNO_NADA" & P3=$!
fase_evaluar 04_pareada_sol_C3 pareada_sol "$MODELO_SOL" C3 1 2 "$CUADERNO_NADA" & P4=$!
wait $P1; wait $P2; wait $P3; wait $P4
if [ -e "$RDIR/detener" ]; then kill $VIG 2>/dev/null; cerrar incompleta "$(cat "$RDIR/detenida.txt" 2>/dev/null)"; exit 1; fi

# paso 5: A con el cuaderno congelado (H1); pasos 6 y 7: E y E3
H=$($RONDA_PY hash-congelado --desde "$INICIO" --modelo "$MODELO_LUNA")
[ -n "$H" ] || { kill $VIG 2>/dev/null; cerrar incompleta "no hay cuaderno congelado tras el paso 1"; exit 1; }
log "cuaderno congelado: $H"
fase_linea_base "$H" || { kill $VIG 2>/dev/null; cerrar incompleta "$(cat "$RDIR/detenida.txt" 2>/dev/null)"; exit 1; }
fase_evaluar 06_eval_E evaluacion_E "$MODELO_LUNA" E 2 3 "$H" & P6=$!
fase_evaluar 07_pareada_luna_E3 pareada_luna "$MODELO_LUNA" E3 1 2 "$H" & P7=$!
fase_evaluar 08_pareada_sol_E3 pareada_sol "$MODELO_SOL" E3 1 2 "$H" & P8=$!
wait $P6; wait $P7; wait $P8
kill $VIG 2>/dev/null
if [ -e "$RDIR/detener" ]; then cerrar incompleta "$(cat "$RDIR/detenida.txt" 2>/dev/null)"; exit 1; fi
cerrar terminada ""
log "RONDA TERMINADA"
