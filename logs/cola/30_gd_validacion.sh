# Compuerta: las corridas gd solo arrancan si la validación pasa. Si falla, espera hasta 150 min a que aparezca
# logs/cola/gd_listo (lo crea Claude tras corregir) y valida otra vez.
rm -f logs/cola/gd_ok
v() { .venv/bin/python tools/gd_validar.py > logs/gd_validacion.log 2>&1; }
if v; then touch logs/cola/gd_ok; echo "[cola] validación gd OK"; exit 0; fi
echo "[cola] validación gd FALLÓ; espero logs/cola/gd_listo (máx. 150 min)"
i=0; while [ $i -lt 300 ] && [ ! -f logs/cola/gd_listo ]; do sleep 30; i=$((i+1)); done
if v; then touch logs/cola/gd_ok; echo "[cola] validación gd OK tras corrección"; else echo "[cola] validación gd sigue fallando: se omiten las corridas gd"; fi
