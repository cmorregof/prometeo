#!/bin/sh
# Igual que run_isabelle_lemas_mem.sh (V_I con lemas y memoria, 3 episodios, B = 4, memory_prompt = v1) pero con
# gpt-6-astra (high). Corre desde una copia congelada del código (rl_metodos/.snap_astra_bis/unirl, huella
# 61c5c2b8649611f6, tomada el 23 sep 22:47) para que los cambios de esa noche en 09_unified/unirl no la afecten.
# En cola: espera a que termine la corrida de Luna (PID 3665) y a que no quede ningún `isabelle build` vivo.
cd "$(dirname "$0")/.."
U=$(pwd)
echo "en cola $(date): esperando a Luna (PID 3665)"
while ps -p 3665 -o command= 2>/dev/null | grep -q "unirl run"; do sleep 30; done
while pgrep -f "Isabelle_Tool build" >/dev/null; do sleep 10; done
echo "inicio $(date)"
cd "$U/../.snap_astra_bis" && "$U/.venv/bin/python" -u -m unirl run --config "$U/configs/bisection_isabelle_lemas_mem.toml" \
  --episodes 3 --model gpt-6-astra --effort high --out "$U/runs"
echo "fin $(date)"
