#!/bin/sh
# Corridas del juez de grafo (instantáneo; el costo es el LLM). En paralelo.
cd "$(dirname "$0")/.."
echo "inicio $(date)"
.venv/bin/python -u -m unirl run --config configs/bisection_graph.toml --episodes 20 --model gpt-5.4-mini --effort low > logs/graph_bisection_mini.log 2>&1 &
.venv/bin/python -u -m unirl run --config configs/bisection_graph.toml --episodes 20 --model gpt-6-luna --effort high > logs/graph_bisection_luna.log 2>&1 &
for c in fixedpoint taylor newton secant; do
  .venv/bin/python -u -m unirl run --config configs/${c}_graph.toml --episodes 20 --model gpt-5.4-mini --effort low > logs/graph_${c}_mini.log 2>&1 &
done
wait
echo "fin $(date)"
