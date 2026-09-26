#!/bin/sh
# Ejecuta un comando que compila en Isabelle SOLO mientras ninguna otra compilación de Isabelle (p. ej. la bisección,
# cuyo Sledgehammer tiene límite de tiempo real) esté activa, y lo interrumpe si aparece una.
# Arranca tras 20 s seguidos sin compilaciones ajenas. Uso: sh tools/ventana.sh <comando ...>
ajenas() { ps -ax -o command= | grep "Isabelle_Tool build" | grep -v grep | grep -v "/gd-" | grep -v "IsaRL_GD_"; }
matar_mias() { pkill -f "IsaRL_GD_" 2>/dev/null; pkill -f "/scratch/gd-" 2>/dev/null; }
libre=0
while [ $libre -lt 4 ]; do
  if [ -n "$(ajenas)" ]; then libre=0; else libre=$((libre+1)); fi
  sleep 5
done
echo "[ventana] $(date '+%T') sin compilaciones ajenas: arranco"
"$@" &
P=$!
while kill -0 $P 2>/dev/null; do
  if [ -n "$(ajenas)" ]; then
    echo "[ventana] $(date '+%T') otra compilación de Isabelle empezó: interrumpo"
    pkill -TERM -P $P 2>/dev/null; kill $P 2>/dev/null; matar_mias; sleep 2; matar_mias
    exit 99
  fi
  sleep 2
done
wait $P
