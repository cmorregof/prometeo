# Primera validación del juez de stepsize en Isabelle (no es compuerta): da señal temprana; si falla, se corrige
# mientras corren las etapas del PEP, que no usan Isabelle.
.venv/bin/python tools/gd_validar.py > logs/gd_validacion_temprana.log 2>&1
echo "[cola] validación gd temprana rc=$? (detalle en logs/gd_validacion_temprana.log)"
grep "^\[gd_validar\]" logs/gd_validacion_temprana.log | tail -20
