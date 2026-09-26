#!/bin/sh
# Cola de la noche del 23 al 24 sep 2026. Ejecuta en orden los scripts logs/cola/NN_*.sh; cada uno se lee justo
# antes de correrlo, así que las etapas futuras se pueden corregir sin tocar este archivo ni lo que ya corre.
# Nada de Isabelle se solapa: cada etapa espera a la anterior.
cd "$(dirname "$0")/.."
DIR=logs/cola
hechas=" "
while :; do
  sig=""
  for f in $(ls $DIR/*.sh 2>/dev/null | sort); do
    b=$(basename "$f")
    case "$hechas" in *" $b "*) ;; *) sig=$b; break;; esac
  done
  [ -z "$sig" ] && break
  echo "[cola] $(date '+%F %T') inicio $sig"
  sh "$DIR/$sig"
  rc=$?
  echo "[cola] $(date '+%F %T') fin $sig (rc=$rc)"
  hechas="$hechas$sig "
done
echo "[cola] $(date '+%F %T') cola terminada"
