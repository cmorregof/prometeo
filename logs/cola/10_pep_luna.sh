PY=.venv/bin/python
PEP="pep_gradnorm_n4 pep_gradnorm_n6 pep_gradnorm_n4_neg pep_fval_mu001_n4 pep_fval_mu01_n5"
for c in $PEP; do
  $PY -u -m unirl run --config configs/$c.toml --episodes 3 --model gpt-6-luna --effort high || echo "[cola] PEP $c gpt-6-luna falló"
done
$PY -m unirl informe --ultima $(echo $PEP | tr ' ' ',') --model gpt-6-luna --slug pep_variantes-gpt-6-luna || echo "[cola] informe PEP gpt-6-luna falló"
