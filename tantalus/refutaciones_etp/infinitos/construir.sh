#!/bin/bash
# Compila PortF5 con Lean 4.34.1 + Mathlib v4.34.1 de corpus_lean. Uso: ./construir.sh [Modulo ...]
A="$(cd "$(dirname "$0")" && pwd)"; L="$A/../../../corpus_compilar/corpus_lean"
eval "$(cd "$L" && lake env env | grep -E '^(LEAN_PATH|LEAN_SYSROOT|ELAN_TOOLCHAIN|PATH)=' | sed 's/^/export /; s/=/="/; s/$/"/')"
export LEAN_PATH="$A/build:$LEAN_PATH"; mkdir -p "$A/build/PortF5"
ORDEN="Magma FactsSyntax Ecuaciones FreeMagma Confluence ConfluenceSystem Confluence3 Confluence2 Confluence4 Eq1437 Eq1659 Eq1661 Eq1701 Inf3994 OrLemmas Superposition Eq883 Tareas"
for m in ${@:-$ORDEN}; do
  [ -f "$A/PortF5/$m.lean" ] || continue
  t0=$(date +%s)
  if (cd "$A" && lean -R "$A" -o "$A/build/PortF5/$m.olean" -i "$A/build/PortF5/$m.ilean" "PortF5/$m.lean") > "$A/build/$m.log" 2>&1; then r=ok; else r=FALLA; fi
  echo "$m $r $(( $(date +%s)-t0 )) s errores=$(grep -c 'error' "$A/build/$m.log")"
done
