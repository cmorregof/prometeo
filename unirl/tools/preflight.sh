#!/bin/bash
# preflight.sh: comprobaciones previas a la ronda (26 sep 2026). Aborta con código 1 si algo falla.
#   uso: unirl/tools/preflight.sh [--dry-run] [--reanudacion]
# --dry-run: no llama a la API. --reanudacion: no exige el cuaderno sembrado ni el árbol limpio (la ronda ya escribió).
set -u
RAIZ="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$RAIZ" || exit 1
PY="$RAIZ/.venv/bin/python"
DRY=0; REANUDA=0
for a in "$@"; do case "$a" in --dry-run) DRY=1;; --reanudacion) REANUDA=1;; esac; done
HASH_SEMBRADO="0b6385c1aed55323"
fallos=0
ok()   { printf '  ✔ %s\n' "$1"; }
mal()  { printf '  ✘ %s\n' "$1"; fallos=$((fallos+1)); }

echo "preflight en $RAIZ ($(date '+%Y-%m-%d %H:%M:%S'))"

# 1. Isabelle2025 responde
ISA=$("$PY" -c "from isarl.config import ISABELLE_BIN; print(ISABELLE_BIN)" 2>/dev/null)
if [ -n "$ISA" ] && [ -x "$ISA" ] && "$ISA" version 2>/dev/null | grep -q "Isabelle2025"; then ok "Isabelle2025 responde ($ISA)"; else mal "Isabelle2025 no responde en ${ISA:-?}"; fi

# 2. el .venv importa los paquetes
if "$PY" -c "import unirl, steprl, isarl, unirl.experimentos, unirl.tools" 2>/dev/null || "$PY" -c "import unirl, steprl, isarl, unirl.experimentos" 2>/dev/null; then ok ".venv importa unirl, steprl e isarl"; else mal ".venv no importa unirl/steprl/isarl"; fi

# 3. la clave existe en el .env de la raíz (nunca se imprime) y una llamada mínima a Luna funciona
if [ -f "$RAIZ/.env" ] && grep -qE '^OPENAI_API_KEY=.{20,}' "$RAIZ/.env"; then ok "OPENAI_API_KEY presente en .env"; else mal "falta OPENAI_API_KEY en .env"; fi
if [ "$DRY" = 1 ]; then
  echo "  · llamada de prueba a Luna omitida (--dry-run)"
else
  if "$PY" - <<'PYEOF'
import os, sys
from steprl.providers import make_provider
from unirl.gasto import Libro, ProveedorContable
from unirl.loop import clasificar_error
try:
    p = make_provider("openai", "gpt-6-luna", reasoning_effort="low")
    p.max_output_tokens = 64
    prov = ProveedorContable(p, Libro(), fase="preflight", corrida="preflight")
    txt = prov.complete("Responde con la palabra OK y nada más.", "OK")
    u = prov.ultimo_uso or {}
    print(f"  ✔ Luna respondió ({u.get('entrada', '?')} + {u.get('salida', '?')} tokens, ${u.get('usd', 0):.5f}, registrado en el libro de la ronda)")
except Exception as e:
    print(f"  ✘ la llamada de prueba a Luna falló ({clasificar_error(e)}): {str(e)[:160]}")
    sys.exit(1)
PYEOF
  then :; else fallos=$((fallos+1)); fi
fi

# 4. disco ≥ 5 GB
libre_kb=$(df -k "$RAIZ" | awk 'NR==2 {print $4}')
if [ "${libre_kb:-0}" -ge 5242880 ]; then ok "disco libre: $((libre_kb/1048576)) GB"; else mal "disco libre insuficiente: $((libre_kb/1048576)) GB (< 5 GB)"; fi

# 5. el cuaderno vivo está en el hash sembrado (solo al empezar una ronda)
h=$("$PY" -c "from unirl.cuaderno import Cuaderno; print(Cuaderno().hash())" 2>/dev/null)
if [ "$REANUDA" = 1 ]; then echo "  · cuaderno vivo: $h (reanudación: no se exige el sembrado)";
elif [ "$h" = "$HASH_SEMBRADO" ]; then ok "cuaderno vivo en el hash sembrado $HASH_SEMBRADO"; else mal "el cuaderno vivo no está en el hash sembrado ($h ≠ $HASH_SEMBRADO)"; fi

# 6. git: rama reorganizar y árbol limpio (limpio solo al empezar)
rama=$(git -C "$RAIZ" branch --show-current 2>/dev/null)
if [ "$rama" = "reorganizar" ]; then ok "rama reorganizar"; else mal "rama actual: ${rama:-?} (se esperaba reorganizar)"; fi
sucios=$(git -C "$RAIZ" status --porcelain 2>/dev/null | wc -l | tr -d ' ')
if [ "$REANUDA" = 1 ]; then echo "  · git status: $sucios cambios (reanudación: la ronda ya escribió registros)";
elif [ "$sucios" = 0 ]; then ok "git status limpio"; else mal "git status con $sucios cambios (commit o stash antes de empezar)"; fi

# 7. pytest rápido en verde
if out=$("$PY" -m pytest -q -p no:cacheprovider -m "not isabelle" 2>&1 | tail -1) && echo "$out" | grep -qE '^[0-9]+ passed' && ! echo "$out" | grep -qE 'failed|error'; then ok "pytest rápido: $out"; else mal "pytest rápido: $out"; fi

if [ "$fallos" = 0 ]; then echo "preflight: todo bien"; exit 0; else echo "preflight: $fallos comprobaciones fallaron; no se lanza la ronda"; exit 1; fi
