#!/bin/sh
# V_G con gpt-6-luna (high) en 02–05; la de bisección ya está hecha (runs/bisection_graph/20260923-193740-gpt-6-luna-high).
cd "$(dirname "$0")/.."
echo "inicio $(date)"
for c in fixedpoint taylor newton secant; do
  .venv/bin/python -u -m unirl run --config configs/${c}_graph.toml --episodes 20 > logs/graph_${c}_luna.log 2>&1 &
  sleep 2
done
wait
echo "fin $(date)"
