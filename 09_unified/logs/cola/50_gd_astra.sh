[ -f logs/cola/gd_ok ] || { echo "[cola] sin validación gd: se omite gd gpt-6-astra"; exit 0; }
PY=.venv/bin/python
GD="gd_n1 gd_const_n2 gd_const_textbook gd_const_dt"
for c in $GD; do
  $PY -u -m unirl run --config configs/$c.toml --episodes 3 --model gpt-6-astra --effort high || echo "[cola] gd $c gpt-6-astra falló"
done
$PY -m unirl informe --ultima $(echo $GD | tr ' ' ',') --model gpt-6-astra --slug gd_isabelle-gpt-6-astra || echo "[cola] informe gd gpt-6-astra falló"
