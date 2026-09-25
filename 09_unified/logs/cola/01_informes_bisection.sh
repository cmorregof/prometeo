PY=.venv/bin/python
for m in gpt-6-luna gpt-6-astra; do
  $PY -m unirl informe --ultima bisection_isabelle_lemas_mem --model $m --slug bisection_isabelle_lemas_mem-$m || echo "[cola] informe bisección $m falló"
done
