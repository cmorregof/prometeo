#!/bin/bash
# preflight.sh: comprobaciones previas a la ronda (26 sep 2026). Aborta con código 1 si algo falla.
#   uso: unirl/tools/preflight.sh [--dry-run] [--reanudacion] [--cuaderno=<hash>]
# --dry-run: no llama a la API. --reanudacion: no exige el cuaderno de partida ni el árbol limpio (la ronda ya escribió).
# --cuaderno=<hash>: hash de partida exigido al cuaderno vivo (ronda 2: el estado final de la ronda 1); sin él, el sembrado.
# MODELO_PREFLIGHT=<modelo>[,<modelo>…] (17 oct 2026): los proponentes de la llamada de prueba, una por modelo; por
# omisión gpt-6-luna. Con un modelo claude-* se exige ANTHROPIC_API_KEY; con los demás, OPENAI_API_KEY.
set -u
RAIZ="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$RAIZ" || exit 1
PY="$RAIZ/.venv/bin/python"
DRY=0; REANUDA=0
HASH_SEMBRADO="0b6385c1aed55323"   # cuaderno sembrado con que empezó la ronda 1
HASH_ESPERADO="$HASH_SEMBRADO"
for a in "$@"; do case "$a" in --dry-run) DRY=1;; --reanudacion) REANUDA=1;; --cuaderno=*) HASH_ESPERADO="${a#--cuaderno=}";; esac; done
fallos=0
ok()   { printf '  ✔ %s\n' "$1"; }
mal()  { printf '  ✘ %s\n' "$1"; fallos=$((fallos+1)); }

echo "preflight en $RAIZ ($(date '+%Y-%m-%d %H:%M:%S'))"

# 1. Isabelle2025 responde
ISA=$("$PY" -c "from isarl.config import ISABELLE_BIN; print(ISABELLE_BIN)" 2>/dev/null)
if [ -n "$ISA" ] && [ -x "$ISA" ] && "$ISA" version 2>/dev/null | grep -q "Isabelle2025"; then ok "Isabelle2025 responde ($ISA)"; else mal "Isabelle2025 no responde en ${ISA:-?}"; fi

# 2. el .venv importa los paquetes
if "$PY" -c "import unirl, steprl, isarl, unirl.experimentos, unirl.tools" 2>/dev/null || "$PY" -c "import unirl, steprl, isarl, unirl.experimentos" 2>/dev/null; then ok ".venv importa unirl, steprl e isarl"; else mal ".venv no importa unirl/steprl/isarl"; fi

# 3. disco ≥ 5 GB
libre_kb=$(df -k "$RAIZ" | awk 'NR==2 {print $4}')
if [ "${libre_kb:-0}" -ge 5242880 ]; then ok "disco libre: $((libre_kb/1048576)) GB"; else mal "disco libre insuficiente: $((libre_kb/1048576)) GB (< 5 GB)"; fi

# 4. el cuaderno vivo está en el hash de partida (solo al empezar una ronda)
h=$("$PY" -c "from unirl.cuaderno import Cuaderno; print(Cuaderno().hash())" 2>/dev/null)
if [ "$REANUDA" = 1 ]; then echo "  · cuaderno vivo: $h (reanudación: no se exige el hash de partida)";
elif [ "$h" = "$HASH_ESPERADO" ]; then ok "cuaderno vivo en el hash de partida $HASH_ESPERADO"; else mal "el cuaderno vivo no está en el hash de partida ($h ≠ $HASH_ESPERADO)"; fi

# 5. git: rama reorganizar y árbol limpio (limpio solo al empezar)
rama=$(git -C "$RAIZ" branch --show-current 2>/dev/null)
if [ "$rama" = "reorganizar" ]; then ok "rama reorganizar"; else mal "rama actual: ${rama:-?} (se esperaba reorganizar)"; fi
sucios=$(git -C "$RAIZ" status --porcelain 2>/dev/null | wc -l | tr -d ' ')
if [ "$REANUDA" = 1 ]; then echo "  · git status: $sucios cambios (reanudación: la ronda ya escribió registros)";
elif [ "$sucios" = 0 ]; then ok "git status limpio"; else mal "git status con $sucios cambios (commit o stash antes de empezar)"; fi

# 6. pytest rápido en verde
if out=$("$PY" -m pytest -q -p no:cacheprovider -m "not isabelle" 2>&1 | tail -1) && echo "$out" | grep -qE '^[0-9]+ passed' && ! echo "$out" | grep -qE 'failed|error'; then ok "pytest rápido: $out"; else mal "pytest rápido: $out"; fi

# 7 (último). La clave existe en el .env de la raíz (nunca se imprime) y una llamada mínima al proponente funciona.
# Va al final: la llamada crea el libro de la ronda (logs/gasto_ronda_<id>.json) y, si fuera antes, el árbol de git
# aparecería sucio en el paso 6 (lanzamientos del 26 sep, 19:00 y 19:07). Solo se llama si todo lo demás pasó.
export MODELO_PRUEBA="${MODELO_PREFLIGHT:-gpt-6-luna}"
CLAVES=$(printf '%s' "$MODELO_PRUEBA" | tr ',' '\n' | awk '/^claude-/{print "ANTHROPIC_API_KEY"; next} NF{print "OPENAI_API_KEY"}' | sort -u)
for CLAVE in $CLAVES; do
  if [ -f "$RAIZ/.env" ] && grep -qE "^${CLAVE}=.{20,}" "$RAIZ/.env"; then ok "$CLAVE presente en .env"; else mal "falta $CLAVE en .env"; fi
done
if [ "$DRY" = 1 ]; then
  echo "  · llamada de prueba a $MODELO_PRUEBA omitida (--dry-run)"
elif [ "$fallos" != 0 ]; then
  echo "  · llamada de prueba a $MODELO_PRUEBA omitida: ya hay comprobaciones fallidas"
else
  if "$PY" - <<'PYEOF'
import os, sys
from steprl.providers import make_provider
from unirl.gasto import Libro, ProveedorContable
from unirl.loop import clasificar_error
fallo = False
for modelo in [m.strip() for m in os.environ["MODELO_PRUEBA"].split(",") if m.strip()]:
    try:
        if modelo.startswith("claude-"):  # sin fallback; Opus 5.5 y Sonnet 5.5 piensan siempre: margen para el razonamiento
            p = make_provider("anthropic", modelo, effort="low", fallback_model=None, max_output_tokens=1024)
        else:
            p = make_provider("openai", modelo, reasoning_effort="low")
            p.max_output_tokens = 64
        prov = ProveedorContable(p, Libro(), fase="preflight", corrida="preflight")
        txt = prov.complete("Responde con la palabra OK y nada más.", "OK")
        u = prov.ultimo_uso or {}
        print(f"  ✔ {modelo} respondió ({u.get('entrada', '?')} + {u.get('salida', '?')} tokens, ${u.get('usd', 0):.5f}, registrado en el libro de la ronda)")
    except Exception as e:
        print(f"  ✘ la llamada de prueba a {modelo} falló ({clasificar_error(e)}): {str(e)[:160]}")
        fallo = True
sys.exit(1 if fallo else 0)
PYEOF
  then :; else fallos=$((fallos+1)); fi
fi


if [ "$fallos" = 0 ]; then echo "preflight: todo bien"; exit 0; else echo "preflight: $fallos comprobaciones fallaron; no se lanza la ronda"; exit 1; fi
