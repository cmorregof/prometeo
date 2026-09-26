# Astra en bisección con lemas y memoria corre en run_isabelle_lemas_mem_astra.sh (PID en logs/cola/astra_bis.pid),
# que espera a Luna. Esta etapa solo espera a que ese script termine.
P=$(cat logs/cola/astra_bis.pid)
while ps -p "$P" >/dev/null 2>&1; do sleep 30; done
tail -3 logs/isabelle_lemas_mem_astra.log
